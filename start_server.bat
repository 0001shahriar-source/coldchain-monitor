@echo off
title ColdChain Server Runner
echo ========================================================
echo Starting ColdChain Backend Server & IoT Stream...
echo ========================================================
cd /d "%~dp0backend"
node src/server.js
pause

