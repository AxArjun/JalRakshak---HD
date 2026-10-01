# JalRakshak-HD: Safe Demo Startup Script
# Checks prerequisites and active ports, launches services if not running

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  JalRakshak-HD v1.0-SIH Demo Launcher" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

# Function to test port availability
function Test-PortOccupied([int]$port) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $connect = $tcp.BeginConnect("127.0.0.1", $port, $null, $null)
        $wait = $connect.AsyncWaitHandle.WaitOne(500, $false)
        if ($wait) {
            $tcp.EndConnect($connect)
            $tcp.Close()
            return $true
        }
        $tcp.Close()
        return $false
    } catch {
        return $false
    }
}

# 1. Backend Port 8000 Check
$BackendRunning = Test-PortOccupied 8000
if ($BackendRunning) {
    Write-Host "[OK] Backend already running on http://127.0.0.1:8000" -ForegroundColor Green
} else {
    Write-Host "[*] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot'; python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"
    Start-Sleep -Seconds 2
}

# 2. Frontend Port 5173 Check
$FrontendRunning = Test-PortOccupied 5173
if ($FrontendRunning) {
    Write-Host "[OK] Frontend already running on http://localhost:5173" -ForegroundColor Green
} else {
    Write-Host "[*] Starting Vite React Frontend on http://localhost:5173..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ProjectRoot\frontend'; npm run dev"
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host "  JalRakshak-HD is active and ready for demonstration!" -ForegroundColor Green
Write-Host "  Backend API:  http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "  GIS Command:  http://localhost:5173" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

Start-Process "http://localhost:5173"
