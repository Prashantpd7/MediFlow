# fix_git_shell.ps1 - make git available in current PowerShell session and persistent profile
$gitCmdPath = 'C:\Program Files\Git\cmd\git.exe'
Write-Output "Checking git at: $gitCmdPath"
if (-not (Test-Path $gitCmdPath)) {
    Write-Output "ERROR: git.exe not found at $gitCmdPath"
    exit 1
}
Write-Output "where.exe git:"; where.exe git | ForEach-Object { Write-Output "  $_" }
Write-Output "Session PATH contains git cmd?:"
$p = 'C:\Program Files\Git\cmd'
Write-Output ($env:Path -split ';' | Where-Object { $_ -eq $p } | Measure-Object).Count -gt 0
if (-not ($env:Path -split ';' | Where-Object { $_ -eq $p })) {
    $env:Path = $env:Path + ';' + $p
    Write-Output "Added $p to session PATH"
} else {
    Write-Output "Session PATH already contains $p"
}
# Create a global alias so `git` works in this session
try {
    Set-Alias -Name git -Value $gitCmdPath -Scope Global -Force
    Write-Output "Set global alias 'git' -> $gitCmdPath"
} catch {
    Write-Output "Failed to set alias: $_"
}
# Add a persistent wrapper to the user's profile so new shells get it
$profilePath = $PROFILE
if (-not (Test-Path $profilePath)) { New-Item -ItemType File -Force -Path $profilePath | Out-Null; Write-Output "Created profile: $profilePath" }
$wrapper = "function git { & 'C:\\Program Files\\Git\\cmd\\git.exe' @args }"
$profileContent = Get-Content $profilePath -ErrorAction SilentlyContinue
if (-not ($profileContent -contains $wrapper)) {
    Add-Content -Path $profilePath -Value "`n# Ensure git command available`n$wrapper`n"
    Write-Output "Appended git wrapper to profile: $profilePath"
} else {
    Write-Output "Profile already contains git wrapper"
}
# Final tests
Write-Output "Testing via full path:"; & $gitCmdPath --version
Write-Output "Testing via alias 'git':"; git --version
Write-Output "Attempting git add . (will show exit code):"; git add .; Write-Output "git add exit code: $LASTEXITCODE"
Write-Output "Done. Restart any other PowerShell windows to pick up the profile changes."