# One-time secure collection. No credentials are written to files or command arguments.
$ErrorActionPreference = 'Stop'
$repository = 'openverifyproject/openverify'
$gh = (Get-Command gh -ErrorAction SilentlyContinue).Source
if (-not $gh) { $gh = 'C:\Program Files\GitHub CLI\gh.exe' }

function Set-PrivateInput(
    [string]$environment, [string]$name, [switch]$KeyFile, [switch]$AllowEmpty
) {
    $known = & $gh secret list -R $repository --env $environment --json name --jq '.[].name'
    if ($LASTEXITCODE -ne 0) { throw "Cannot inspect $environment secret names" }
    if ($known -contains $name) { Write-Host "$environment/$name already configured"; return }
    if ($KeyFile) {
        $keyPath = Read-Host 'Path to the existing ASCII-armored Maven signing private key'
        $plain = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $keyPath))
    } else {
        $hint = if ($AllowEmpty) { 'blank only for an unprotected key' } else { 'required' }
        $secure = Read-Host "$environment/$name (hidden input; $hint)" -AsSecureString
        $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        try { $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
        finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    }
    try {
        if ($AllowEmpty -and [string]::IsNullOrEmpty($plain)) { return }
        if ([string]::IsNullOrWhiteSpace($plain)) { throw "Missing $name" }
        $plain | & $gh secret set $name -R $repository --env $environment
        if ($LASTEXITCODE -ne 0) { throw "Secure upload failed: $environment/$name" }
    } finally { $plain = $null; $secure = $null }
}

function Set-AccountName([string]$environment, [string]$name, [string]$prompt) {
    $known = & $gh variable list -R $repository --env $environment --json name --jq '.[].name'
    if ($LASTEXITCODE -ne 0) { throw "Cannot inspect $environment variables" }
    if ($known -contains $name) { return }
    $value = Read-Host $prompt
    if ([string]::IsNullOrWhiteSpace($value)) { throw "Missing $name" }
    & $gh variable set $name -R $repository --env $environment --body $value
    if ($LASTEXITCODE -ne 0) { throw "Cannot configure $environment/$name" }
}

Set-AccountName sdk-dotnet NUGET_USER 'Your NuGet profile username (not email)'
Set-AccountName sdk-php PACKAGIST_USERNAME 'Your Packagist username'
Set-PrivateInput sdk-rust CARGO_REGISTRY_TOKEN
Set-PrivateInput sdk-jvm CENTRAL_USERNAME
Set-PrivateInput sdk-jvm CENTRAL_PASSWORD
Set-PrivateInput sdk-jvm MAVEN_GPG_PRIVATE_KEY -KeyFile
Set-PrivateInput sdk-jvm MAVEN_GPG_PASSPHRASE -AllowEmpty
Set-PrivateInput sdk-php SDK_PHP_MIRROR_TOKEN
Set-PrivateInput sdk-php PACKAGIST_API_TOKEN
Write-Host 'Release inputs configured. No registry upload or release tag was created.'
