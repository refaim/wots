!include LogicLib.nsh
!include x64.nsh

!define ERROR_ABORTED_BY_SCRIPT 2
!define ERROR_ELEVATION_REQUIRED 740

!define APPNAME "Wizard of the Search"
!define HELPURL "https://github.com/refaim/wots/issues"
!define UPDATEURL "https://github.com/refaim/wots/releases"
!define ABOUTURL "https://github.com/refaim/wots/blob/master/README.md"
!define VERSIONMAJOR %version_major%
!define VERSIONMINOR %version_minor%
!define VERSIONBUILD %version_build%
!define INSTALLSIZE %install_size_kb%
!define PROGRAMARCH "%program_arch%"

!macro VerifyUserIsAdmin
    UserInfo::GetAccountType
    Pop $0
    ${If} $0 != "admin"
        MessageBox mb_iconstop "Administrator rights required"
        SetErrorLevel ${ERROR_ELEVATION_REQUIRED}
        Quit
    ${EndIf}
!macroend

RequestExecutionLevel admin
LicenseData "%license_file%"
Name "${APPNAME}"
OutFile "%setup_name%.exe"
Page license
Page directory
Page instfiles

function .onInit
    SetShellVarContext all
    !insertmacro VerifyUserIsAdmin
    ${If} ${RunningX64}
        StrCpy $INSTDIR "$PROGRAMFILES64\${APPNAME}"
    ${Else}
        ${If} ${PROGRAMARCH} == "x64"
            MessageBox mb_iconstop "This program cannot be installed in x86 environment"
            SetErrorLevel ${ERROR_ABORTED_BY_SCRIPT}
            Quit
        ${EndIf}
        StrCpy $INSTDIR "$PROGRAMFILES32\${APPNAME}"
    ${EndIf}
functionEnd

function un.onInit
    SetShellVarContext all
    MessageBox MB_OKCANCEL "Uninstall ${APPNAME}?" IDOK next
        Abort
next:
    !insertmacro VerifyUserIsAdmin
functionEnd

Section "install"
    SetOutPath $INSTDIR
%install_commands%
    WriteUninstaller "$INSTDIR\uninstall.exe"
    # TODO !!!!!!!!!!!!
    # CreateShortcut "$SMPROGRAMS\${APPNAME}.lnk" "$INSTDIR\%exe_name%.exe" "" "$INSTDIR\logo.ico"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$INSTDIR\uninstall.exe /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$INSTDIR"
    # TODO !!!!!!!!!!!!
    # WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\logo.ico$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "Roman Kharitonov"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
SectionEnd

Section "uninstall"
    Delete "$SMPROGRAMS\${APPNAME}.lnk"
%uninstall_commands%
    Delete $INSTDIR\uninstall.exe
    RMDir $INSTDIR
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd
