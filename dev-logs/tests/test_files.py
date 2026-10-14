import importlib.machinery
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader('logs_files', str(Path(__file__).resolve().parents[1] / 'bin/oma-devlogs'))
spec = importlib.util.spec_from_loader(loader.name, loader)
logs = importlib.util.module_from_spec(spec)
loader.exec_module(logs)


class FileTests(unittest.TestCase):
    def test_creation_preserves_existing_file_and_trash_keeps_recovery_path(self):
        with tempfile.TemporaryDirectory(prefix='logs files ') as directory, patch.object(Path, 'home', return_value=Path(directory)):
            home = Path(directory)
            original = logs.create_markdown(str(home), 'Release notes')
            original.write_text('# User notes\nKeep this content.\n')
            second = logs.create_markdown(str(home), 'Release notes')
            self.assertNotEqual(original, second)
            self.assertEqual(second.name, 'Release notes-2.md')
            target = logs.trash_markdown(str(original))
            self.assertFalse(original.exists())
            self.assertIn('Keep this content.', target.read_text())
            self.assertEqual(json.loads(target.with_suffix('.json').read_text())['original'], str(original))

    def test_home_boundary_and_symlink_deletion_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            home = Path(directory)
            with patch.object(Path, 'home', return_value=home):
                with self.assertRaises(ValueError):
                    logs.create_markdown(outside, 'Outside')
                original = logs.create_markdown(str(home), 'Real')
                link = home / 'link.md'
                link.symlink_to(original)
                with self.assertRaises(ValueError):
                    logs.trash_markdown(str(link))
                self.assertTrue(original.exists())
                for name in ('../outside', 'bad/name', 'two\nlines', '.hidden'):
                    with self.assertRaises(ValueError):
                        logs.create_markdown(str(home), name)


if __name__ == '__main__':
    unittest.main()
