#!/usr/bin/env python3
"""Install/update per-user files; never copy conversations or personal config."""
import argparse
import datetime
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-deps', action='store_true', help='Dependencies already installed')
    args = parser.parse_args()
    home = Path.home()
    if not args.skip_deps:
        if not shutil.which('pacman'):
            sys.exit('Requires Omalauncher Arch Linux. Install Python, curl, util-linux, espeak-ng, libpulse first, then --skip-deps.')
        cmd = ['pacman', '-S', '--needed', '--noconfirm', 'python', 'curl', 'util-linux', 'espeak-ng', 'libpulse', 'mpg123']
        if os.geteuid() != 0:
            cmd.insert(0, 'sudo')
        subprocess.run(cmd, check=True)
    venv = home / '.local/share/oma-voice/venv'
    if not args.skip_deps:
        if not (venv/'bin/python').exists():
            subprocess.run([sys.executable, '-m', 'venv', str(venv)], check=True)
        subprocess.run([str(venv/'bin/python'), '-m', 'pip', 'install', '-r', str(ROOT/'requirements.txt')], check=True)
    backup = home / '.local/share/oma-voice/install-backups' / datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    installed = []
    def write(relative, data, executable=False):
        target = home / relative
        if target.exists():
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_name(target.name+'.install-tmp')
        temp.write_bytes(data)
        temp.chmod(0o700 if executable else 0o600)
        temp.replace(target)
        installed.append(relative)
    for folder, destination in [('voice', '.local/share/oma-voice'), ('dictation', '.local/share/oma-speak'), ('bin', '.local/bin')]:
        for file in sorted((ROOT/folder).iterdir()):
            if file.is_file():
                write(destination+'/'+file.name, file.read_bytes(), folder=='bin')
    for file in sorted((ROOT/'widgets').glob('*.owl')):
        # OWL strings contain shell commands; quote the home path for shell and OWL independently.
        import json, shlex
        quoted = shlex.quote(str(home))
        escaped = json.dumps(quoted, ensure_ascii=False)[1:-1]
        write('.config/omalauncher/widgets/'+file.name, file.read_text().replace('__HOME__', escaped).encode())
    print('Installed Codex 播報 and 語音輸入. Personal settings and conversation data were preserved.')
    print('Updated files backed up at:', backup)
    print('After updating an already-running version, restart Linux once to reload its voice service.')
    print('Start or resume a Codex conversation, then tap 同步 on the home-screen widget.')
    print('Online voice sends reply text to Microsoft Edge TTS. Choose 聲音：離線 for local basic speech.')
    checker = shutil.which('owl-check')
    if checker and not args.skip_deps:
        for name in ('46-speak.owl', '47-voice-input.owl'):
            subprocess.run([checker, str(home/'.config/omalauncher/widgets'/name)], check=True)

if __name__ == '__main__':
    main()
