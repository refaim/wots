import os
import platform
import sys

import PyQt5
import dotenv
from PyInstaller.archive.pyz_crypto import PyiBlockCipher
from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis

RESOURCES_DIRECTORY = 'res'
BINARY_RESOURCE_EXTENSIONS = {'.png'}


class BytesPyiBlockCipher(PyiBlockCipher):
    def __init__(self, key: bytes):
        super().__init__('')
        self.key = key


dotenv.load_dotenv('.env')

extra_path = []
if platform.system() == 'Windows':
    extra_path.append(os.path.join(os.path.dirname(PyQt5.__file__), 'Qt', 'bin'))
    extra_path.append(os.path.dirname(sys.executable))
    version, *_ = platform.win32_ver()
    if int(version) >= 10:
        for program_files_var in ['ProgramFiles', 'ProgramFiles(x86)']:
            for arch in ['x86', 'x64']:
                dll_path = os.path.join(os.getenv(program_files_var), 'Windows Kits\\10\\Redist\\ucrt\\DLLs', arch)
                if os.path.isdir(dll_path):
                    extra_path.append(dll_path)

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
    block_cipher = BytesPyiBlockCipher(key=cipher_key.encode('utf-8'))

a = Analysis([os.path.join('app', 'wizard.py')],
             pathex=extra_path, binaries=bin_resources, datas=txt_resources, hiddenimports=[], hookspath=[],
             runtime_hooks=[], excludes=[], win_no_prefer_redirects=False, win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, exclude_binaries=True, name='wizard', debug=False, strip=False, upx=False, console=False)
COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name=os.getenv('APP_NAME'))
