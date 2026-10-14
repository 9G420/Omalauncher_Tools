from contextlib import redirect_stdout
import datetime as dt
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader('devdesk', str(Path(__file__).resolve().parents[1] / 'bin/oma-devlogs'))
spec = importlib.util.spec_from_loader(loader.name, loader)
desk = importlib.util.module_from_spec(spec)
loader.exec_module(desk)


class MonthlyJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        for name, value in [('ROOT', root), ('JOURNAL', root / 'journal'), ('NOTES', root / 'notes')]:
            p = patch.object(desk, name, value)
            p.start()
            self.addCleanup(p.stop)
        desk.ensure_dirs()

    def history(self, day='', offset=0):
        output = io.StringIO()
        with redirect_stdout(output):
            desk.history(day, offset)
        return json.loads(output.getvalue())

    def test_daily_views_and_pagination_from_monthly_file(self):
        lines = ['- 2026-10-13 09:00 · 舊日紀錄']
        lines += [f'- 2026-10-14 10:{i:02} · 紀錄 {i}' for i in range(45)]
        (desk.JOURNAL / '2026-10.md').write_text('# 開發日誌\n\n' + '\n'.join(lines))
        latest = self.history()
        self.assertEqual(latest['days'], ['2026-10-14', '2026-10-13'])
        self.assertEqual(latest['day'], '2026-10-14')
        self.assertEqual(latest['total'], 45)
        self.assertEqual(len(latest['entries']), 40)
        self.assertTrue(latest['more'])
        self.assertEqual(latest['entries'][0], '10:44 · 紀錄 44')
        self.assertEqual(len(self.history('2026-10-14', 40)['entries']), 5)
        self.assertEqual(self.history('2026-10-13')['entries'], ['09:00 · 舊日紀錄'])

    def test_legacy_daily_files_and_month_boundaries(self):
        (desk.JOURNAL / '2026-09-30.md').write_text('# daily\n- 23:00 · 舊格式\n')
        (desk.JOURNAL / '2026-10.md').write_text('# monthly\n- 2026-10-01 08:00 · 新格式\n')
        self.assertEqual(self.history()['days'], ['2026-10-01', '2026-09-30'])
        self.assertEqual(self.history('2026-09-30')['entries'], ['23:00 · 舊格式'])
        self.assertEqual(desk.read_latest(), ('2026-10-01', '08:00 · 新格式'))

    def test_log_writes_monthly_file_with_full_timestamp(self):
        with patch.object(desk, 'refresh_widget'), redirect_stdout(io.StringIO()):
            desk.log_entry('專案：功能完成；驗證通過。')
            desk.log_entry('另一個重要變更。')
        now = dt.datetime.now().astimezone()
        files = list(desk.JOURNAL.glob('*.md'))
        self.assertEqual([p.name for p in files], [now.strftime('%Y-%m.md')])
        content = files[0].read_text()
        self.assertEqual(content.count('# 開發日誌'), 1)
        self.assertIn('- ' + now.date().isoformat() + ' ', content)
        self.assertEqual(self.history(now.date().isoformat())['total'], 2)

    def test_invalid_dates_and_empty_days(self):
        self.assertEqual(self.history('2026-10-12')['entries'], [])
        for day in ('../README', '2026-10', '2026-02-30'):
            with self.assertRaises(SystemExit):
                self.history(day)


if __name__ == '__main__':
    unittest.main()
