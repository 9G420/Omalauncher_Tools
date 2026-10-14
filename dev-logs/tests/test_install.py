import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('desk_build', ROOT / 'tools/build_store.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class InstallTests(unittest.TestCase):
    def test_github_and_embedded_setup_preserve_user_data(self):
        with tempfile.TemporaryDirectory(prefix='desk install ') as directory:
            home = Path(directory)
            env = dict(os.environ, HOME=str(home))
            journal = home / 'oma-devlogs/journal/2026-10.md'
            note = home / 'oma-devlogs/notes/private.md'
            agent = home / 'AGENTS.md'
            journal.parent.mkdir(parents=True)
            note.parent.mkdir(parents=True)
            journal.write_text('# Journal\n- 2026-10-14 08:00 · existing entry\n')
            note.write_text('# Existing note\n')
            agent.write_text('Existing agent settings\n')
            originals = {p: p.read_bytes() for p in (journal, note, agent)}
            subprocess.run([sys.executable, str(ROOT / 'install.py'), '--skip-deps'], env=env, check=True, capture_output=True)
            subprocess.run(['bash', '-c', build.setup_script()], env=env, check=True, capture_output=True)
            for path, content in originals.items():
                self.assertEqual(path.read_bytes(), content)
            for relative, (text, executable) in build.payload().items():
                path = home / relative
                self.assertEqual(path.read_text(), text)
                self.assertEqual(bool(path.stat().st_mode & 0o100), executable)
            marker = home / '.local/share/oma-devlogs/store-version'
            self.assertEqual(marker.read_text(), build.payload_id())
            installed = home / '.config/omalauncher/widgets/65-dev-logs.owl'
            self.assertEqual(installed.read_text(), build.render())
            self.assertTrue(list((home / '.local/share/oma-devlogs/install-backups').rglob('oma-devlogs')))

    def test_new_install_starts_with_no_sample_journal(self):
        with tempfile.TemporaryDirectory() as directory:
            env = dict(os.environ, HOME=directory)
            subprocess.run(['bash', '-c', build.setup_script()], env=env, check=True, capture_output=True)
            cli = Path(directory) / '.local/bin/oma-devlogs'
            result = subprocess.run([sys.executable, str(cli), 'status'], env=env, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout)['entries'], 0)
            self.assertEqual(list((Path(directory) / 'oma-devlogs/journal').glob('*.md')), [])

    def test_rename_preserves_legacy_data_and_command(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            old = home / 'oma-devdesk/journal/2026-10.md'
            old.parent.mkdir(parents=True)
            old.write_text('# Journal\n- 2026-10-14 08:00 · legacy data\n')
            widget = home / '.config/omalauncher/widgets/65-dev-desk.owl'
            widget.parent.mkdir(parents=True)
            widget.write_text('widget "DEV DESK" {}')
            env = dict(os.environ, HOME=directory)
            subprocess.run([sys.executable, str(ROOT / 'install.py'), '--skip-deps'], env=env, check=True, capture_output=True)
            new = home / 'oma-devlogs/journal/2026-10.md'
            self.assertIn('legacy data', new.read_text())
            self.assertFalse(old.exists())
            self.assertFalse(widget.exists())
            self.assertTrue(list((home / '.local/share/oma-devlogs/install-backups').rglob('65-dev-desk.owl')))
            result = subprocess.run([sys.executable, str(home / '.local/bin/oma-devdesk'), 'status'], env=env, capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(result.stdout)['entries'], 1)

    def test_generated_store_widget_is_current_and_portable(self):
        text = build.render()
        self.assertEqual((build.STORE / 'widget.owl').read_text(), text)
        self.assertLess(len(text.encode()), 256 * 1024)
        for personal in ('/root/', '__SETUP_COMMAND__', '__VERSION__', '__PAYLOAD_ID__'):
            self.assertNotIn(personal, text)
        self.assertIn('${sh(value)}', text)
        self.assertIn('state errorLevel = "error" persist', text)
        self.assertIn('Settings', text)


if __name__ == '__main__':
    unittest.main()
