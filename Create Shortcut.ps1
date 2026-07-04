$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$shortcutPath = Join-Path $scriptDir 'Launch Battle Monsters.lnk'
$targetPath = $null
$arguments = ''

$venvPythonw = Join-Path $scriptDir '.venv\Scripts\pythonw.exe'
if (Test-Path $venvPythonw) {
    $targetPath = $venvPythonw
    $arguments = '"' + (Join-Path $scriptDir 'battle_gui.py') + '"'
} else {
    $pythonw = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($pythonw) {
        $targetPath = $pythonw.Source
        $arguments = '"' + (Join-Path $scriptDir 'battle_gui.py') + '"'
    } else {
        $python = Get-Command python.exe -ErrorAction SilentlyContinue
        if ($python) {
            $targetPath = $python.Source
            $arguments = '"' + (Join-Path $scriptDir 'battle_gui.py') + '"'
        } else {
            throw 'Python was not found on PATH.'
        }
    }
}

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.Arguments = $arguments
$shortcut.WorkingDirectory = $scriptDir
$shortcut.WindowStyle = 7
$shortcut.IconLocation = "$env:SystemRoot\System32\cmd.exe,0"
$shortcut.Save()

Write-Host "Created shortcut: $shortcutPath"
