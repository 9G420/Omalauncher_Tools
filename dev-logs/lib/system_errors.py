'''Local Linux error history. Does not access Android logs or terminal contents.'''
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
from pathlib import Path
import sqlite3
from contextlib import closing

ROOT = Path.home() / 'oma-devlogs'
CONFIG = Path.home() / '.config/omalauncher'
TERMINALS = ROOT / 'logs/terminals'


def sources():
    for path in sorted((CONFIG / 'widgets/.errors').glob('*.txt')):
        yield path, True
    yield CONFIG / 'style/errors.txt', True
    for path in sorted(Path('/tmp').glob('.guest-shell-err-*')):
        yield path, False
    for path in sorted(TERMINALS.glob('*.log')):
        yield path, False
    for name in ('oma-voice/daemon.log', 'oma-speak/server.log', 'pixel-console/bridge.log'):
        yield Path.home() / '.cache' / name, False


def connect():
    directory = ROOT / 'logs'
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    dbpath = directory / 'system-errors.sqlite3'
    db = sqlite3.connect(dbpath, timeout=5)
    db.execute('CREATE TABLE IF NOT EXISTS cursors (path TEXT PRIMARY KEY, inode INTEGER, offset INTEGER, signature TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, time TEXT, source TEXT, text TEXT)')
    dbpath.chmod(0o600)
    return db


def collect(db):
    # One transaction protects offsets against simultaneous refreshes.
    db.execute('BEGIN IMMEDIATE')
    try:
        for path, snapshot in sources():
            key = str(path)
            old = db.execute('SELECT inode, offset, signature FROM cursors WHERE path=?', (key,)).fetchone()
            try:
                with path.open('rb') as stream:
                    stat = os.fstat(stream.fileno())
                    start = 0 if snapshot or not old or old[0] != stat.st_ino or stat.st_size < old[1] else old[1]
                    # Keep newest context, bounded even when a source is noisy.
                    stream.seek(max(start, stat.st_size - 32768))
                    raw = stream.read(32768)
                    end = stream.tell()
            except (OSError, ValueError):
                continue
            signature = hashlib.sha256(raw).hexdigest() if snapshot else ''
            text = raw.decode('utf-8', errors='replace').strip()
            if text and (not snapshot or not old or old[2] != signature):
                # Service files may include routine messages: only retain error contexts.
                service = '/.cache/' in key
                if not service or any(word in text.lower() for word in ('error', 'exception', 'traceback', 'fatal', 'failed', 'panic', 'segfault')):
                    now = dt.datetime.now().astimezone().isoformat(timespec='seconds')
                    db.execute('INSERT INTO events(time,source,text) VALUES(?,?,?)', (now, key, text))
            db.execute('INSERT OR REPLACE INTO cursors VALUES(?,?,?,?)', (key, stat.st_ino, end, signature))
        # Missing snapshot files represent cleared errors; allow future recurrences.
        for (key,) in db.execute('SELECT path FROM cursors').fetchall():
            if key.startswith(str(CONFIG)) and not Path(key).exists():
                db.execute('DELETE FROM cursors WHERE path=?', (key,))
        db.execute('DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT 500)')
        db.commit()
    except BaseException:
        db.rollback()
        raise


def single_report(entry):
    return ('# omalauncher Linux 系統錯誤\n\n'
            '時間為收集時間；來源檔內容可能早於此時間。\n\n'
            f"## {entry['time']}\n\n來源：{entry['source']}\n\n" +
            ''.join('    ' + line + '\n' for line in entry['text'].splitlines()))


def classify(text, source=''):
    '''Classify known diagnostics; unknown messages stay informational.'''
    if re.search(r'\b(?:error|exception|traceback|fatal|failed|panic|segfault|segmentation fault|enosys)\b|function not implemented|異常退出|錯誤|失敗', text, re.I):
        return 'error'
    if re.search(r'\b(?:warn|warning)\b|警告', text, re.I):
        return 'warning'
    if text.strip().startswith('runtime: drawing takes'):
        return 'info'
    if '/widgets/.errors/' in source or source.endswith('/style/errors.txt'):
        return 'error'
    return 'info'


def history(offset=0, level='all'):
    offset = max(0, int(offset))
    if level not in ('all', 'error', 'warning', 'info'):
        raise ValueError('Unknown error filter')
    with closing(connect()) as db:
        collect(db)
        rows = [dict(zip(('id', 'time', 'source', 'text'), row)) for row in db.execute(
            'SELECT id,time,source,text FROM events ORDER BY id DESC')]
    for row in rows:
        row['level'] = classify(row['text'], row['source'])
    counts = {kind: sum(row['level'] == kind for row in rows) for kind in ('error', 'warning', 'info')}
    filtered = [row for row in rows if level == 'all' or row['level'] == level]
    total = len(filtered)
    entries = filtered[offset:offset + 20]
    for entry in entries:
        lines = [line.strip() for line in entry['text'].splitlines() if line.strip()]
        relevant = [line for line in lines if any(word in line.lower() for word in ('error', 'exception', 'fatal', 'failed', '異常退出')) and not line.startswith(('File ', 'During '))]
        entry['summary'] = (relevant[-1] if relevant else (lines[0] if lines else ''))[:180]
        entry['name'] = Path(entry['source']).name
        entry['report'] = single_report(entry)
    return {'total': total, 'all_total': len(rows), 'error_total': counts['error'],
            'counts': counts, 'level': level, 'entries': entries, 'offset': offset, 'more': offset + 20 < total}


def report():
    with closing(connect()) as db:
        collect(db)
        rows = db.execute('SELECT time,source,text FROM events ORDER BY id DESC LIMIT 100').fetchall()
    text = '# omalauncher Linux 系統錯誤\n\n'
    text += '時間為收集時間；來源檔內容可能早於此時間。以下為最近 100 筆本機錯誤。\n\n'
    text += '終端紀錄只包含 stderr 與非零退出碼，無法判斷所有視窗關閉原因。\n\n'
    for time, source, body in rows:
        text += f'## {time}\n\n來源：{source}\n\n'
        text += ''.join('    ' + line + '\n' for line in body.splitlines()) + '\n'
    return text



if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'report':
        print(report())
    else:
        print(json.dumps(history(sys.argv[1] if len(sys.argv) > 1 else 0,
                                 sys.argv[2] if len(sys.argv) > 2 else 'all'), ensure_ascii=False))
