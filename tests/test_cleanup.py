import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('cleanup', Path(__file__).parents[1] / 'scripts/cleanup.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

class CleanupTests(unittest.TestCase):
    def test_account_preserves_history_mcp_and_unknown_fields(self):
        with tempfile.TemporaryDirectory() as t:
            h = Path(t)
            p = h / '.claude.json'
            original = {'oauthAccount': {'email': 'synthetic@example.invalid'}, 'projects': {'x': 1},
                        'mcpServers': {'demo': {}}, 'userID': 'stable', 'unknown': [1]}
            p.write_text(json.dumps(original))
            history = h / '.claude/history.jsonl'
            history.parent.mkdir()
            history.write_text('synthetic history')
            r = c.apply(h, {'account'}, guard=lambda: None)
            expected = dict(original)
            expected.pop('oauthAccount')
            self.assertEqual(json.loads(p.read_text()), expected)
            self.assertEqual(history.read_text(), 'synthetic history')
            self.assertEqual(json.loads((Path(r['backup']) / '.claude.json').read_text()), original)

    def test_cache_backup_and_trash_match(self):
        with tempfile.TemporaryDirectory() as t:
            h = Path(t)
            p = h / '.claude/cache'
            p.mkdir(parents=True)
            (p / 'data').write_bytes(b'synthetic cache')
            r = c.apply(h, {'cache'}, guard=lambda: None)
            self.assertFalse(p.exists())
            self.assertEqual(c.inventory(Path(r['backup']) / '.claude/cache'),
                             c.inventory(Path(r['trash']) / '.claude/cache'))

    def test_symlink_parent_refused(self):
        with tempfile.TemporaryDirectory() as t:
            h = Path(t) / 'home'
            h.mkdir()
            external = Path(t) / 'external'
            external.mkdir()
            (h / '.claude').symlink_to(external)
            (external / 'cache').mkdir()
            with self.assertRaises(RuntimeError):
                c.plan(h, {'cache'})
            self.assertTrue((external / 'cache').exists())

    def test_backup_failure_leaves_original(self):
        with tempfile.TemporaryDirectory() as t:
            h = Path(t)
            p = h / '.claude/stats-cache.json'
            p.parent.mkdir()
            p.write_text('{}')
            with patch.object(c.shutil, 'copy2', side_effect=OSError('simulated failure')):
                with self.assertRaises(OSError):
                    c.apply(h, {'cache'}, guard=lambda: None)
            self.assertEqual(p.read_text(), '{}')
            report = next((h / 'ClaudeBackups').glob('*/report.json'))
            self.assertEqual(json.loads(report.read_text())['moved'], [])

    def test_audit_is_read_only(self):
        with tempfile.TemporaryDirectory() as t:
            h = Path(t)
            p = h / '.claude.json'
            p.write_text('{"oauthAccount": {}}')
            before = c.inventory(h)
            c.plan(h, {'account', 'cache'})
            self.assertEqual(before, c.inventory(h))

if __name__ == '__main__':
    unittest.main()
