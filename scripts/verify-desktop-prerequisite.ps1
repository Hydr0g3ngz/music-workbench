param([Parameter(Mandatory=$true)][string]$Path)
$ErrorActionPreference = 'Stop'
$desktopRuntimeSignature = Get-AuthenticodeSignature -LiteralPath $Path
if ($desktopRuntimeSignature.Status -ne 'Valid' -or $desktopRuntimeSignature.SignerCertificate.Subject -notlike '*Microsoft Corporation*') {
    throw 'The WebView runtime installer does not have a valid Microsoft signature.'
}
