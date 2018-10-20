@echo off
call install_requirements.cmd || exit /b 1
pip install -r requirements.test.txt || exit /b 1
pytest --cov=app || exit /b 1
pyinstaller wizard.spec -y || exit /b 1
