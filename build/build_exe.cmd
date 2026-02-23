@echo off
REM Build GASMonitor.exe on Windows
REM Run from project root:
REM   build\build_exe.cmd

powershell -ExecutionPolicy Bypass -File "%~dp0build_exe.ps1"
