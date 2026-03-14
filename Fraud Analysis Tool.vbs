Set WshShell = CreateObject("WScript.Shell")

' Get the directory where this script is located
ScriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Change to the script directory
WshShell.CurrentDirectory = ScriptDir

' Check if Python is installed
On Error Resume Next
WshShell.Run "python --version", 0, True
If Err.Number <> 0 Then
    MsgBox "Python is not installed!" & vbCrLf & vbCrLf & "Please install Python from https://python.org", vbCritical, "Fraud Analysis Tool"
    WScript.Quit
End If
On Error GoTo 0

' Show starting message
MsgBox "Starting Fraud Analysis Tool..." & vbCrLf & vbCrLf & "The app will open in your browser in a few seconds." & vbCrLf & vbCrLf & "A command window will appear - DO NOT CLOSE IT while using the app.", vbInformation, "Fraud Analysis Tool"

' Start the batch file (which will open browser automatically)
WshShell.Run "cmd /c """ & ScriptDir & "\launcher.bat""", 1, False

' Wait 3 seconds and open browser
WScript.Sleep 3000
WshShell.Run "http://localhost:8501", 1, False
