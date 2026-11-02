Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
ScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = ScriptDir

' Cek pythonw di folder sistem atau instalasi default
PythonW = "pythonw.exe"
If fso.FileExists(WshShell.ExpandEnvironmentStrings("%LocalAppData%\Programs\Python\Python311\pythonw.exe")) Then
    PythonW = """" & WshShell.ExpandEnvironmentStrings("%LocalAppData%\Programs\Python\Python311\pythonw.exe") & """"
ElseIf fso.FileExists(WshShell.ExpandEnvironmentStrings("%ProgramFiles%\Python311\pythonw.exe")) Then
    PythonW = """" & WshShell.ExpandEnvironmentStrings("%ProgramFiles%\Python311\pythonw.exe") & """"
End If

WshShell.Run PythonW & " run.py", 0, False
