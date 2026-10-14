'''Install only DEV LOGS program files; never overwrite log entries or notes.'''
import datetime
import os
from pathlib import Path
import shutil
import uuid


def install_files(files, version):
    home = Path.home()
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
        state.write_text('done')
    except Exception:
        state.write_text('failed')
        raise
    print('DEV LOGS installed. Existing notes and logs were left as they are.')
    if backup.exists():
        print('Replaced program files backed up at:', backup)
