#!/usr/bin/env python3
"""macOS Claude local cleanup; no keychain or browser mutations."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile

CACHE = [
 '.claude/cache', '.claude/stats-cache.json', '.claude/telemetry',
 'Library/Caches/claude-cli-nodejs', 'Library/Caches/com.anthropic.claudefordesktop',
 'Library/Caches/com.anthropic.claudefordesktop.ShipIt', 'Library/Logs/Claude',
] + ['Library/Application Support/Claude/' + n for n in (
 'Cache', 'Code Cache', 'GPUCache', 'DawnGraphiteCache', 'DawnWebGPUCache',
 'GPUPersistentCache', 'GraphiteDawnCache', 'Crashpad', 'sentry',
 'window-state.json', 'vm-support-probe.json')]
ACCOUNT_KEYS = ('oauthAccount', 'accountUuid', 'oauth:tokenCache',
                'oauth:tokenCacheV2', 'lastKnownAccountUuid')
DEVICE = ['Library/Application Support/Claude/ant-did',
          'Library/Application Support/Claude/ant-device-registry.json']


def safe_path(home, path):
    path.relative_to(home)
    for part in [path, *path.parents]:
        if part == home:
            break
        if part.is_symlink():
            raise RuntimeError('拒绝符号链接路径: ' + str(path))
    return path


def inventory(path):
    def item(p):
        if p.is_symlink():
            raise RuntimeError('拒绝目标中的符号链接: ' + str(p))
        if p.is_dir():
            return {'type': 'directory'}
        if not p.is_file():
            raise RuntimeError('拒绝非普通文件: ' + str(p))
        h = hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        return {'sha256': h.hexdigest(), 'size': p.stat().st_size}
    result = {'.': item(path)}
    if path.is_dir():
        for p in sorted(path.rglob('*')):
            result[str(p.relative_to(path))] = item(p)
    return result


def plan(home, scopes):
    moves = []
    edits = []
    if 'cache' in scopes:
        moves.extend(home / x for x in CACHE)
        for rel in ('Library/Logs/DiagnosticReports', 'Library/Application Support/CrashReporter'):
            parent = safe_path(home, home / rel)
            if parent.is_dir():
                moves.extend(parent.glob('Claude_*'))
    if 'device-records' in scopes:
        moves.extend(home / x for x in DEVICE)
    if 'account' in scopes:
        moves.extend(home / x for x in ('.claude/.credentials.json',
                     'Library/Application Support/Claude/config.json.journal'))
        backups = safe_path(home, home / '.claude/backups')
        files = [home / '.claude.json', home / 'Library/Application Support/Claude/config.json']
        if backups.is_dir():
            files.extend(sorted(backups.glob('.claude.json.backup.*')))
        for p in files:
            safe_path(home, p)
            if not p.exists():
                continue
            d = json.loads(p.read_text())
            if not isinstance(d, dict):
                raise RuntimeError('JSON 顶层不是对象: ' + str(p))
            keys = [k for k in ACCOUNT_KEYS if k in d]
            if keys:
                edits.append((p, keys))
    moves = sorted(set(safe_path(home, p) for p in moves if p.exists() or p.is_symlink()))
    return moves, edits


def check_processes():
    r = subprocess.run(['ps', '-axo', 'comm='], capture_output=True, text=True, check=True)
    if any(Path(x.strip()).name in ('Claude', 'claude', 'claude-code') or
           '/Claude.app/' in x for x in r.stdout.splitlines()):
        raise RuntimeError('Claude 相关进程仍在运行；请正常退出。')
    pid = os.getppid()
    for _ in range(20):
        r = subprocess.run(['ps', '-p', str(pid), '-o', 'ppid=,comm='],
                           capture_output=True, text=True, check=True)
        parts = r.stdout.strip().split(None, 1)
        if len(parts) != 2:
            raise RuntimeError('无法确定父进程状态')
        if Path(parts[1]).name.lower() in ('claude', 'claude-code'):
            raise RuntimeError('不能由 Claude Code 修改它正在使用的数据')
        pid = int(parts[0])
        if pid <= 1:
            return
    raise RuntimeError('父进程检查超出范围')


def write_json(p, data):
    mode = stat.S_IMODE(p.stat().st_mode) if p.exists() else 0o600
    fd, name = tempfile.mkstemp(dir=p.parent, prefix='.claude-clean-')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.chmod(name, mode)
        os.replace(name, p)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def apply(home, scopes, guard=check_processes):
    guard()
    moves, edits = plan(home, scopes)
    sources = list(dict.fromkeys(moves + [p for p, _ in edits]))
    if not sources:
        return {'status': 'nothing-to-do'}
    snapshots = {p: inventory(p) for p in sources}
    size = sum(v.get('size', 0) for tree in snapshots.values() for v in tree.values())
    if shutil.disk_usage(home).free < size + 100 * 1024 ** 2:
        raise RuntimeError('备份可用空间不足')
    stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup = safe_path(home, home / 'ClaudeBackups' / ('claude-ban-clean-' + stamp))
    trash = safe_path(home, home / '.Trash' / ('claude-ban-clean-' + stamp))
    backup.mkdir(parents=True, mode=0o700)
    report = {'status': 'backing-up', 'backup': str(backup), 'trash': str(trash),
              'moved': [], 'edited': [], 'scopes': sorted(scopes)}
    report_path = backup / 'report.json'
    try:
        write_json(report_path, report)
        for p in sources:
            dst = backup / p.relative_to(home)
            dst.parent.mkdir(parents=True, exist_ok=True)
            if p.is_dir():
                shutil.copytree(p, dst)
            else:
                shutil.copy2(p, dst)
            if inventory(dst) != snapshots[p]:
                raise RuntimeError('备份校验失败: ' + str(p))
        write_json(backup / 'hashes.json', {str(p.relative_to(home)): x for p, x in snapshots.items()})
        guard()
        for p in sources:
            safe_path(home, p)
            if inventory(p) != snapshots[p]:
                raise RuntimeError('备份期间源数据变化，停止: ' + str(p))
        report['status'] = 'applying'
        write_json(report_path, report)
        trash.mkdir(parents=True, mode=0o700)
        for p in moves:
            dst = trash / p.relative_to(home)
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.rename(p, dst)
            report['moved'].append(str(p.relative_to(home)))
            write_json(report_path, report)
            if inventory(dst) != snapshots[p]:
                raise RuntimeError('废纸篓副本校验失败')
        for p, keys in edits:
            data = json.loads(p.read_text())
            for k in keys:
                data.pop(k, None)
            write_json(p, data)
            report['edited'].append({'path': str(p.relative_to(home)), 'keys': keys})
            write_json(report_path, report)
            if json.loads(p.read_text()) != data:
                raise RuntimeError('JSON 写入校验失败')
        report['status'] = 'complete'
    except Exception as e:
        report['status'] = 'partial-or-stopped'
        report['error_type'] = type(e).__name__
        raise
    finally:
        write_json(report_path, report)
        print('操作报告: ' + str(report_path))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scope', action='append', choices=['cache', 'account', 'device-records'])
    parser.add_argument('--apply', action='store_true', help='备份后执行；仍需要终端确认')
    args = parser.parse_args()
    if sys.platform != 'darwin':
        parser.error('仅支持 macOS；不会执行清理')
    home = Path.home().resolve()
    scopes = set(args.scope or ['cache'])
    moves, edits = plan(home, scopes)
    print(json.dumps({'mode': 'apply' if args.apply else 'audit', 'scopes': sorted(scopes),
          'move_candidates': [str(p.relative_to(home)) for p in moves],
          'edit_candidates': [{'path': str(p.relative_to(home)), 'keys': k} for p, k in edits]},
          ensure_ascii=False, indent=2))
    if not args.apply:
        return
    check_processes()
    if not sys.stdin.isatty():
        raise RuntimeError('执行需要真实终端；不接受管道确认')
    print('备份及废纸篓仍含旧数据。account 会清登录状态；device-records 不更换底层密钥。')
    if input('按上述清单执行请输入 CONFIRM：').strip() != 'CONFIRM':
        print('取消，未修改数据。')
        return
    print(json.dumps(apply(home, scopes), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print('停止: ' + str(exc), file=sys.stderr)
        sys.exit(1)
