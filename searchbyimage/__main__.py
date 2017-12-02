import os
import sys
import shutil
import subprocess
import argparse
import glob

from . import search_providers
from . import gui_qt as gui
# from . import gui_tk as gui
# from . import gui_gtk as gui


def install_desktop_entry():
    here = os.path.dirname(__file__)

    for icon_file in glob.glob(os.path.join(here, 'res', 'searchbyimage-*.png')):
        print('installing:', icon_file)
        subprocess.run(['xdg-icon-resource', 'install', '--novendor', '--size', '48', icon_file])

    app_dir = os.path.expanduser('~/.local/share/applications')
    for desktop_file in glob.glob(os.path.join(here, 'res', 'searchbyimage-*.desktop')):
        print('installing:', desktop_file)
        dst = os.path.join(app_dir, os.path.basename(desktop_file))
        shutil.copy(desktop_file, dst)
    subprocess.run(['update-desktop-database', app_dir])


def main():
    providers = {
        'imgops': search_providers.ImgOps,
        'google': search_providers.Google,
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('image_file')
    parser.add_argument('--provider', default='imgops', help=f'which provider to use {list(providers.keys())}')
    parser.add_argument('--install', action='store_true', help=f'install icons and file assotiations')

    if '--install' in sys.argv:
        install_desktop_entry()
        return

    args, rest = parser.parse_known_args()

    sys.argv = sys.argv[:1] + rest

    assert args.provider in providers
    gui.run(args.image_file, providers[args.provider])


if __name__ == '__main__':
    main()
