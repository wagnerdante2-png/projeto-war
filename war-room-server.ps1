param([int]$Port = 8080)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$Port/")

try {
    $listener.Start()
    Write-Host "ULTIMECIA War Room ativa em http://localhost:$Port" -ForegroundColor Green
    Write-Host "Mantenha esta janela aberta. Pressione Ctrl+C para encerrar." -ForegroundColor DarkGray

    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $requestPath = [Uri]::UnescapeDataString($context.Request.Url.AbsolutePath.TrimStart('/'))
        if ([string]::IsNullOrWhiteSpace($requestPath)) { $requestPath = 'index.html' }

        $fullPath = [System.IO.Path]::GetFullPath((Join-Path $root $requestPath))
        if (-not $fullPath.StartsWith([System.IO.Path]::GetFullPath($root), [System.StringComparison]::OrdinalIgnoreCase)) {
            $context.Response.StatusCode = 403
            $context.Response.Close()
            continue
        }

        if (-not (Test-Path $fullPath -PathType Leaf)) {
            $context.Response.StatusCode = 404
            $context.Response.Close()
            continue
        }

        $ext = [System.IO.Path]::GetExtension($fullPath).ToLowerInvariant()
        $mime = switch ($ext) {
            '.html' { 'text/html; charset=utf-8' }
            '.css'  { 'text/css; charset=utf-8' }
            '.js'   { 'application/javascript; charset=utf-8' }
            '.json' { 'application/json; charset=utf-8' }
            '.svg'  { 'image/svg+xml' }
            '.png'  { 'image/png' }
            '.jpg'  { 'image/jpeg' }
            '.jpeg' { 'image/jpeg' }
            '.ico'  { 'image/x-icon' }
            default { 'application/octet-stream' }
        }

        $bytes = [System.IO.File]::ReadAllBytes($fullPath)
        $context.Response.ContentType = $mime
        $context.Response.ContentLength64 = $bytes.Length
        $context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
        $context.Response.OutputStream.Close()
    }
}
catch {
    Write-Host "Falha ao iniciar o servidor local: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    if ($listener.IsListening) { $listener.Stop() }
    $listener.Close()
}
