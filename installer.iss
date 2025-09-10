[Setup]
AppName=People Counter
AppVersion=1.0.0
AppPublisher=fkunnakkad-soft
DefaultDirName={pf}\People Counter
DefaultGroupName=People Counter
UninstallDisplayIcon={app}\PeopleCounter.exe
OutputBaseFilename=PeopleCounterSetup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Files]
Source: "dist\PeopleCounter\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\People Counter"; Filename: "{app}\PeopleCounter.exe"; IconFilename: "{app}\PeopleCounter.exe"
Name: "{commondesktop}\People Counter"; Filename: "{app}\PeopleCounter.exe"; IconFilename: "{app}\PeopleCounter.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional options:"

[Run]
Filename: "{app}\PeopleCounter.exe"; Description: "Launch People Counter"; Flags: nowait postinstall skipifsilent
