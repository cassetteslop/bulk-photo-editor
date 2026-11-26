# Creates "Bulk Photo Editor" shortcuts on the Desktop and in the Start menu (used by install_from_source.bat).
param([Parameter(Mandatory = $true)][string]$Root)
$shell = New-Object -ComObject WScript.Shell
foreach ($dir in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {
    $lnk = $shell.CreateShortcut((Join-Path $dir 'Bulk Photo Editor.lnk'))
    $lnk.TargetPath       = Join-Path $Root '.venv\Scripts\pythonw.exe'
    $lnk.Arguments        = '"' + (Join-Path $Root 'run.py') + '"'
    $lnk.WorkingDirectory = $Root
    $lnk.IconLocation     = Join-Path $Root 'packaging\windows\BulkPhotoEditor.ico'
    $lnk.Description      = 'Bulk Photo Editor'
    $lnk.Save()
}
