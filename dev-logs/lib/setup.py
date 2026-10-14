'''Install only DEV LOGS program files; never overwrite journal or note data.'''
import datetime
import os
from pathlib import Path
import shutil
import sqlite3
import uuid


def install_files(files, version):
    home = Path.home()
    # Upgrade the local prototype without exporting or overwriting its data.
    for old, new in (('oma-devdesk', 'oma-devlogs'),
                     ('.local/share/oma-devdesk', '.local/share/oma-devlogs')):
        previous, current = home / old, home / new
        if previous.exists() and not current.exists():
            previous.rename(current)
        elif old == 'oma-devdesk' and previous.exists() and current.exists():
            raise RuntimeError('Both legacy and new journal folders exist; preserve and consolidate them before installing.')
    database = home / 'oma-devlogs/logs/system-errors.sqlite3'
    if database.exists():
        old_prefix, new_prefix = str(home / 'oma-devdesk') + '/', str(home / 'oma-devlogs') + '/'
        db = sqlite3.connect(database)
        try:
            with db:
                for table, column in (('cursors', 'path'), ('events', 'source')):
                    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
                        continue
                    if table == 'cursors':
                        rows = db.execute('SELECT path FROM cursors WHERE substr(path,1,?)=?', (len(old_prefix), old_prefix)).fetchall()
                        for (path,) in rows:
                            target = new_prefix + path[len(old_prefix):]
                            if db.execute('SELECT 1 FROM cursors WHERE path=?', (target,)).fetchone():
                                db.execute('DELETE FROM cursors WHERE path=?', (path,))
                            else:
                                db.execute('UPDATE cursors SET path=? WHERE path=?', (target, path))
                    else:
                        db.execute('UPDATE events SET source=? || substr(source,?) WHERE substr(source,1,?)=?',
                                   (new_prefix, len(old_prefix) + 1, len(old_prefix), old_prefix))
        finally:
            db.close()
    share = home / '.local/share/oma-devlogs'
    share.mkdir(parents=True, exist_ok=True, mode=0o700)
    state = share / 'setup-state'
    state.write_text('installing')
    backup = share / 'install-backups' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    try:
        for name in ('notes', 'journal', 'logs/terminals'):
            (home / 'oma-devlogs' / name).mkdir(parents=True, exist_ok=True, mode=0o700)
        payload = dict(files)
        payload['.local/share/oma-devlogs/store-version'] = (version, False)
        for relative, (text, executable) in payload.items():
            target = home / relative
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            if target.exists():
                saved = backup / relative
                saved.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                shutil.copy2(target, saved)
            temporary = target.with_name(target.name + '.' + uuid.uuid4().hex + '.install-tmp')
            try:
                temporary.write_text(text, encoding='utf-8')
                temporary.chmod(0o700 if executable else 0o600)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        previous_widget = home / '.config/omalauncher/widgets/65-dev-desk.owl'
        if previous_widget.exists() and previous_widget.read_text().lstrip().startswith(('widget "DEV DESK"', 'widget "DEV // DESK"')):
            saved = backup / '.config/omalauncher/widgets/65-dev-desk.owl'
            saved.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copy2(previous_widget, saved)
            previous_widget.unlink()
        state.write_text('done')
    except Exception:
        state.write_text('failed')
        raise
    print('DEV LOGS installed. Your notes, journal and agent settings were preserved.')
    if backup.exists():
        print('Replaced program files backed up at:', backup)
