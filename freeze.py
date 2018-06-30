import cx_Freeze
import os
import sys

cx_Freeze.setup(
    name='Wizard of the Search',
    version='1.0',
    description='',
    options={
        'build_exe': {
            'create_shared_zip': False,
            'append_script_to_exe': True,
            'path': sys.path + [os.path.abspath('app')],
            'includes': [
                'cssselect',
                'lxml._elementpath',
            ],
            'include_files': [
                'res',
                'app/wizard.ui',
            ],
        },
    },
    executables=[cx_Freeze.Executable(
        script='app/wizard.py',
        targetName='wizard.exe',
        base='Win32GUI',
    )]
)
