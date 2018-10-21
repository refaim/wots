import datetime
import math
import os
import sys

import PyQt5
import dotenv
from PyInstaller.archive.pyz_crypto import PyiBlockCipher
from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis

from app import version
from app.core.utils import OsUtils, PathUtils

APP_NAME = 'wizard'
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
BUILD_DIRECTORY = os.path.join(PROJECT_ROOT, 'build')
DISTR_DIRECTORY = os.path.join(PROJECT_ROOT, 'dist', APP_NAME)
RESOURCES_DIRECTORY = os.path.join(PROJECT_ROOT, 'res')
BINARY_RESOURCE_EXTENSIONS = {'.png'}

dotenv.load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

extra_path = []
app_version_file = None
app_version_ints = None
if OsUtils.is_windows():
    extra_path.append(os.path.join(os.path.dirname(PyQt5.__file__), 'Qt', 'bin'))
    extra_path.append(os.path.dirname(sys.executable))
    if OsUtils.is_win10():
        for program_files_var in ['ProgramFiles', 'ProgramFiles(x86)']:
            for arch in ['x86', 'x64']:
                dll_path = os.path.join(os.getenv(program_files_var), 'Windows Kits\\10\\Redist\\ucrt\\DLLs', arch)
                if os.path.isdir(dll_path):
                    extra_path.append(dll_path)

    app_version = version.VERSION
    app_version_ints = [int(x) for x in app_version.split('.')]
    while len(app_version_ints) < 4:
        app_version_ints.append(0)

    app_version_file = os.path.join(BUILD_DIRECTORY, 'exe_version.txt')
    with open(os.path.join(PROJECT_ROOT, 'exe_version.template.txt')) as version_template_fobj:
        with open(app_version_file, 'w') as version_fobj:
            version_fobj.write(version_template_fobj.read().format(
                version_string=str(app_version),
                version_tuple=tuple(app_version_ints),
                current_year=datetime.datetime.today().year))

txt_resources = []
if os.path.exists('.env'):
    txt_resources.append(('.env', '.'))

bin_resources = []
for filename in os.listdir(RESOURCES_DIRECTORY):
    target = txt_resources
    if os.path.splitext(filename)[1] in BINARY_RESOURCE_EXTENSIONS:
        target = bin_resources
    target.append((os.path.join(RESOURCES_DIRECTORY, filename), os.path.relpath(RESOURCES_DIRECTORY, PROJECT_ROOT)))

block_cipher = None
cipher_key = os.getenv('PYINSTALLER_CIPHER_KEY')
if cipher_key:
    block_cipher = PyiBlockCipher(key=cipher_key)

a = Analysis([os.path.join(PROJECT_ROOT, 'app', 'wizard.py')],
             pathex=extra_path, binaries=bin_resources, datas=txt_resources, hiddenimports=[], hookspath=[],
             runtime_hooks=[], excludes=[], win_no_prefer_redirects=True, win_private_assemblies=True,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, exclude_binaries=True, name=APP_NAME, debug=False, strip=False, upx=False, console=False, version=app_version_file)
COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name=APP_NAME)

if OsUtils.is_windows():
    nsis_license = os.path.join(BUILD_DIRECTORY, 'license.txt')
    with open(os.path.join(PROJECT_ROOT, 'LICENSE')) as src_license_fobj:
        with open(nsis_license, 'w') as dst_license_fobj:
            dst_license_fobj.write(src_license_fobj.read().replace('\n', '\r\n'))

    with open(os.path.join(PROJECT_ROOT, 'setup.template.nsi')) as nsis_template_fobj:
        config = nsis_template_fobj.read()

    distr_directories = []
    distr_files = []
    for root, dirs, files in os.walk(DISTR_DIRECTORY):
        for dir_name in dirs:
            distr_directories.append(os.path.join(root, dir_name))
        for file_name in files:
            distr_files.append(os.path.join(root, file_name))

    def make_inst_path(path: str) -> str:
        return PathUtils.quote(os.path.join('$INSTDIR', os.path.relpath(path, DISTR_DIRECTORY)))

    def add_command(commands: list, command: str) -> None:
        commands.append((' ' * 4) + command)

    indent = ' ' * 4
    install_commands = []
    for path in distr_directories:
        add_command(install_commands, 'CreateDirectory {}'.format(make_inst_path(path)))
    for path in distr_files:
        add_command(install_commands, 'File {} {}'.format(PathUtils.quote('/oname={}'.format(os.path.relpath(path, DISTR_DIRECTORY))), PathUtils.quote(path)))

    uninstall_commands = []
    for path in distr_files:
        add_command(uninstall_commands, 'Delete {}'.format(make_inst_path(path)))
    for path in reversed(distr_directories):
        add_command(uninstall_commands, 'RMDir {}'.format(make_inst_path(path)))

    arch = 'x64' if OsUtils.is_x64() else 'x86'
    NSIS_VARS = {
        '%license_file%': os.path.basename(nsis_license),
        '%version_major%': str(app_version_ints[0]),
        '%version_minor%': str(app_version_ints[1]),
        '%version_build%': str(app_version_ints[2]),
        '%install_size_kb%': str(math.ceil(PathUtils.get_folder_size(DISTR_DIRECTORY) / 1024)),
        '%program_arch%': arch,
        '%exe_name%': APP_NAME,
        '%setup_name%': 'WizardOfTheSearch_v{}_Setup_{}'.format(version.VERSION, arch),
        '%distr_directory%': DISTR_DIRECTORY,
        '%install_commands%': '\r\n'.join(install_commands),
        '%uninstall_commands%': '\r\n'.join(uninstall_commands),
    }
    for k, v in NSIS_VARS.items():
        config = config.replace(k, v)

    with open(os.path.join(BUILD_DIRECTORY, 'setup.nsi'), 'w') as nsis_fobj:
        nsis_fobj.write(config)
