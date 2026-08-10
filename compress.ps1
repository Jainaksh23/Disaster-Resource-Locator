$source = "d:\AI-powered disaster resource locator"
$destination = "d:\AI-powered disaster resource locator\AI_Project_Compressed.zip"

If (Test-Path $destination) { Remove-Item $destination }

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zipArchive = [System.IO.Compression.ZipFile]::Open($destination, 'Create')

Get-ChildItem -Path $source -Recurse | Where-Object {
    $_.FullName -notmatch '\\venv\\' -and
    $_.FullName -notmatch '\\__pycache__\\' -and
    $_.FullName -notmatch '\\node_modules\\' -and
    $_.FullName -notmatch '\\\.git\\' -and
    $_.FullName -notmatch 'AI_Project_Compressed.zip'
} | ForEach-Object {
    $relativePath = $_.FullName.Substring($source.Length + 1)
    if (-not $_.PSIsContainer) {
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zipArchive, $_.FullName, $relativePath)
    }
}
$zipArchive.Dispose()
Write-Host "Compression complete! Saved as AI_Project_Compressed.zip"
