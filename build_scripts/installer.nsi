; Windows Whisper NSIS Installer Script
; Modern installer following Windows 11 best practices

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "WinVer.nsh"

; Installer Information
!define APP_NAME "Windows Whisper"
!define APP_VERSION "0.4.0"
!define APP_PUBLISHER "Windows Whisper"
!define APP_URL "https://github.com/pavel-zhur/windows-whisper"
!define APP_EXE "WindowsWhisper.exe"
!define APP_UNINSTALLER "Uninstall.exe"

; Registry keys
!define REG_UNINSTALL "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
!define REG_AUTOSTART "Software\Microsoft\Windows\CurrentVersion\Run"

; General Settings
Name "${APP_NAME}"
OutFile "WindowsWhisper-${APP_VERSION}-Setup.exe"
Unicode True
RequestExecutionLevel user ; User-level installation by default
InstallDir "$LOCALAPPDATA\${APP_NAME}"
InstallDirRegKey HKCU "Software\${APP_NAME}" "InstallPath"

; Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Installer Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Start ${APP_NAME}"
!insertmacro MUI_PAGE_FINISH

; Uninstaller Pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Version Information
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "${APP_NAME} Installer"
VIAddVersionKey "FileVersion" "${APP_VERSION}"

; Installation Sections
Section "!${APP_NAME} (Required)" SecMain
    SectionIn RO ; Read-only, cannot be deselected
    
    ; Check Windows version
    ${IfNot} ${AtLeastWin10}
        MessageBox MB_ICONSTOP "This application requires Windows 10 or later."
        Quit
    ${EndIf}
    
    SetOutPath "$INSTDIR"
    
    ; Install main executable
    File "dist\WindowsWhisper.exe"
    
    ; Install configuration files
    File "..\profiles.yaml"
    File /oname=.env.example "..\.env.example"
    File "..\README.md"
    File "..\LICENSE"
    
    ; Create .env file if it doesn't exist
    ${If} ${FileExists} "$INSTDIR\.env"
        DetailPrint ".env file already exists, keeping current configuration"
    ${Else}
        CopyFiles "$INSTDIR\.env.example" "$INSTDIR\.env"
        DetailPrint "Created .env configuration file"
    ${EndIf}
    
    ; Write registry entries
    WriteRegStr HKCU "Software\${APP_NAME}" "InstallPath" "$INSTDIR"
    WriteRegStr HKCU "Software\${APP_NAME}" "Version" "${APP_VERSION}"
    
    ; Write uninstaller
    WriteUninstaller "$INSTDIR\${APP_UNINSTALLER}"
    
    ; Registry entries for Add/Remove Programs
    WriteRegStr HKCU "${REG_UNINSTALL}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKCU "${REG_UNINSTALL}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKCU "${REG_UNINSTALL}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKCU "${REG_UNINSTALL}" "URLInfoAbout" "${APP_URL}"
    WriteRegStr HKCU "${REG_UNINSTALL}" "UninstallString" "$INSTDIR\${APP_UNINSTALLER}"
    WriteRegStr HKCU "${REG_UNINSTALL}" "QuietUninstallString" "$INSTDIR\${APP_UNINSTALLER} /S"
    WriteRegStr HKCU "${REG_UNINSTALL}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "${REG_UNINSTALL}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
    WriteRegDWORD HKCU "${REG_UNINSTALL}" "NoModify" 1
    WriteRegDWORD HKCU "${REG_UNINSTALL}" "NoRepair" 1
    
    ; Calculate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKCU "${REG_UNINSTALL}" "EstimatedSize" "$0"
    
SectionEnd

Section "Desktop Shortcut" SecDesktop
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
SectionEnd

Section "Start Menu Shortcut" SecStartMenu
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\${APP_UNINSTALLER}" "" "$INSTDIR\${APP_UNINSTALLER}" 0
SectionEnd

Section "Start with Windows" SecAutoStart
    WriteRegStr HKCU "${REG_AUTOSTART}" "${APP_NAME}" "$INSTDIR\${APP_EXE}"
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} "Core application files (required)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Create a desktop shortcut"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Create Start Menu shortcuts"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecAutoStart} "Automatically start ${APP_NAME} when Windows starts"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Uninstaller Section
Section "Uninstall"
    ; Stop the application if running
    ExecWait 'taskkill /f /im "${APP_EXE}"' $0
    
    ; Remove autostart entry
    DeleteRegValue HKCU "${REG_AUTOSTART}" "${APP_NAME}"
    
    ; Remove files
    Delete "$INSTDIR\${APP_EXE}"
    Delete "$INSTDIR\profiles.yaml"
    Delete "$INSTDIR\.env.example"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\LICENSE"
    Delete "$INSTDIR\${APP_UNINSTALLER}"
    
    ; Ask user about keeping configuration
    MessageBox MB_YESNO|MB_ICONQUESTION "Do you want to keep your configuration files (.env, .profile.txt)?" IDYES KeepConfig
    Delete "$INSTDIR\.env"
    Delete "$INSTDIR\.profile.txt"
    KeepConfig:
    
    ; Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    
    ; Remove registry entries
    DeleteRegKey HKCU "${REG_UNINSTALL}"
    DeleteRegKey HKCU "Software\${APP_NAME}"
    
    ; Remove installation directory if empty
    RMDir "$INSTDIR"
    
SectionEnd

; Functions
Function .onInit
    ; Check if already installed
    ReadRegStr $R0 HKCU "Software\${APP_NAME}" "InstallPath"
    ${If} $R0 != ""
        MessageBox MB_YESNO|MB_ICONQUESTION "${APP_NAME} is already installed. Do you want to reinstall?" IDYES Reinstall
        Quit
        Reinstall:
    ${EndIf}
FunctionEnd

Function .onInstSuccess
    ; Show configuration message
    MessageBox MB_ICONINFORMATION "Installation completed successfully!$\r$\n$\r$\nUse the 'Setup API Token' option in the system tray menu to configure your OpenAI API key."
FunctionEnd