#!/usr/bin/env python3
'''Install DEV LOGS independently of the voice and dictation tools.'''
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'lib'))
import build_store
from setup import install_files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-deps', action='store_true', help='Required Arch packages are already installed')
    args = parser.parse_args()
    if not args.skip_deps:
        if not shutil.which('pacman'):
            parser.error('Requires Omalauncher Arch Linux; use --skip-deps only if dependencies are present.')
        subprocess.run(['pacman', '-S', '--needed', '--noconfirm', 'python', 'bash', 'coreutils', 'gum', 'less', 'micro', 'foot'], check=True)
    files = build_store.payload()
    files['.config/omalauncher/widgets/65-dev-logs.owl'] = (build_store.render(), False)
    install_files(files, build_store.payload_id())
    print('Open DEV LOGS. Settings contains language selection and agent logging instructions.')
    checker = shutil.which('owl-check')
    if checker and not args.skip_deps:
        subprocess.run([checker, str(Path.home() / '.config/omalauncher/widgets/65-dev-logs.owl')], check=True)


if __name__ == '__main__':
    main()
