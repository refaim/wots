@echo off
rem PyCrypto build workaround
set STDINTH="C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\INCLUDE\stdint.h"
if not exist %STDINTH% echo "File not found: %STDINTH%" && exit /b 1
set CL=-FI%STDINTH%
python -m pip install -r requirements.windows.txt || exit /b 1
exit /b 0
