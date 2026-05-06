@echo off
echo GBP Ops Dashboard を起動しています...
echo.
echo [1/2] ファイルスキャン中（投稿・レポート検知）...
powershell -ExecutionPolicy Bypass -File "%~dp0sync-posts.ps1"
echo.
echo [2/2] サーバー起動中...
start http://localhost:3000
node "%~dp0server.js"
pause
