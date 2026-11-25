' run_ASTRA.vbs
' Silent launcher with NO console window.
' Uses .venv if available, otherwise falls back to clean Python install.

Option Explicit

Dim WshShell, oFSO, strDir, strScript, strPython

Set WshShell = CreateObject("WScript.Shell")
Set oFSO    = CreateObject("Scripting.FileSystemObject")

strDir    = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
strScript = strDir & "main.py"

' Prefer .venv pythonw.exe
strPython = strDir & ".venv\Scripts\pythonw.exe"
If Not oFSO.FileExists(strPython) Then
    ' Fall back through standard Python installs (skip Anaconda paths)
    Dim username
    username  = WshShell.ExpandEnvironmentStrings("%USERNAME%")
    strPython = "C:\Users\" & username & "\AppData\Local\Programs\Python\Python312\pythonw.exe"
    If Not oFSO.FileExists(strPython) Then
        strPython = "C:\Users\" & username & "\AppData\Local\Programs\Python\Python311\pythonw.exe"
    End If
    If Not oFSO.FileExists(strPython) Then
        strPython = "C:\Python312\pythonw.exe"
    End If
    If Not oFSO.FileExists(strPython) Then
        strPython = "C:\Python311\pythonw.exe"
    End If
End If

' Launch silently (0 = hidden window, False = don't wait)
WshShell.Run """" & strPython & """ """ & strScript & """", 0, False

Set WshShell = Nothing
Set oFSO     = Nothing
