$gitPath = 'C:\Program Files\Git\cmd'
$userPath = [Environment]::GetEnvironmentVariable('Path','User')
if (-not [string]::IsNullOrEmpty($userPath) -and $userPath.Contains($gitPath)) {
    Write-Output "User PATH already contains $gitPath"
} else {
    $new = ($userPath + ';' + $gitPath).Trim(';')
    [Environment]::SetEnvironmentVariable('Path', $new, 'User')
    Write-Output "Added $gitPath to User PATH"
}
if (-not $env:Path.Contains($gitPath)) {
    $env:Path = $env:Path + ';' + $gitPath
    Write-Output "Updated session PATH"
} else {
    Write-Output "Session PATH already contains $gitPath"
}
try {
    & "${gitPath}\git.exe" --version
} catch {
    Write-Output "Error running git.exe: $_"
}
Write-Output "To fully apply the User PATH for all new terminals, please restart PowerShell or sign out and in."