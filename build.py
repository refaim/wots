import os
import platform
import sys

import PyQt5
from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis

RESOURCES_DIRECTORY = 'res'
BINARY_RESOURCE_EXTENSIONS = {'.png'}

path = []
if platform.system() == 'Windows':
    path.append(os.path.join(os.path.dirname(PyQt5.__file__), 'Qt', 'bin'))
    path.append(os.path.dirname(sys.executable))

txt_resources = []
if os.path.exists('.env'):
    txt_resources.append(('.env', '.'))

bin_resources = []
for filename in os.listdir(RESOURCES_DIRECTORY):
    target = txt_resources
    if os.path.splitext(filename)[1] in BINARY_RESOURCE_EXTENSIONS:
        target = bin_resources
    target.append((os.path.join(RESOURCES_DIRECTORY, filename), RESOURCES_DIRECTORY))

block_cipher = None
a = Analysis([os.path.join('app', 'wizard.py')],
             pathex=path, binaries=bin_resources, datas=txt_resources, hiddenimports=[], hookspath=[],
             runtime_hooks=[], excludes=[], win_no_prefer_redirects=False, win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, exclude_binaries=True, name='wizard', debug=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name='Wizard of the Search')
