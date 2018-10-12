import datetime
import os
import platform
import sys

import PyQt5
import dotenv
from PyInstaller.archive.pyz_crypto import PyiBlockCipher
from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis

from app import version

RESOURCES_DIRECTORY = 'res'
BINARY_RESOURCE_EXTENSIONS = {'.png'}

dotenv.load_dotenv('.env')

extra_path = []
version_file = None
if platform.system() == 'Windows':
    extra_path.append(os.path.join(os.path.dirname(PyQt5.__file__), 'Qt', 'bin'))
    extra_path.append(os.path.dirname(sys.executable))
    if platform.version().startswith('10.'):
        for program_files_var in ['ProgramFiles', 'ProgramFiles(x86)']:
            for arch in ['x86', 'x64']:
                dll_path = os.path.join(os.getenv(program_files_var), 'Windows Kits\\10\\Redist\\ucrt\\DLLs', arch)
                if os.path.isdir(dll_path):
                    extra_path.append(dll_path)

    app_version = version.VERSION
    version_list = [int(x) for x in app_version.split('.')]
    while len(version_list) < 4:
        version_list.append(0)

    version_file = 'exe_version.txt'
    with open('{}.template'.format(version_file)) as version_template:
        with open(version_file, 'w') as version_file_object:
            version_file_object.write(version_template.read().format(
                version_string=str(app_version),
                version_tuple=tuple(version_list),
                current_year=datetime.datetime.today().year))

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
cipher_key = os.getenv('PYINSTALLER_CIPHER_KEY')
if cipher_key:
    block_cipher = PyiBlockCipher(key=cipher_key)

a = Analysis([os.path.join('app', 'wizard.py')],
             pathex=extra_path, binaries=bin_resources, datas=txt_resources, hiddenimports=[], hookspath=[],
             runtime_hooks=[], excludes=[], win_no_prefer_redirects=True, win_private_assemblies=True,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, exclude_binaries=True, name='wizard', debug=False, strip=False, upx=False, console=False, version=version_file)
COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name='wizard')
