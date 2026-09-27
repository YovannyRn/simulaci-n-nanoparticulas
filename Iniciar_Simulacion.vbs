' Doble clic: abre la interfaz sin ventana de consola (pythonw).
Option Explicit

Dim sh, fso, root, pyw, cmd
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
pyw = root & "\.venv\Scripts\pythonw.exe"

If Not fso.FileExists(pyw) Then
  MsgBox "No se encontro el entorno .venv." & vbCrLf & vbCrLf & _
    "Una sola vez, en esta carpeta:" & vbCrLf & _
    "  python -m venv .venv" & vbCrLf & _
    "  .\.venv\Scripts\Activate.ps1" & vbCrLf & _
    "  pip install -r requirements.txt" & vbCrLf & vbCrLf & _
    "Despues vuelva a hacer doble clic en este archivo." & vbCrLf & _
    "Detalle: docs\GUI_WIAM.md", _
    vbExclamation, "Simulacion MB"
  WScript.Quit 1
End If

sh.CurrentDirectory = root
sh.Environment("PROCESS")("PYTHONPATH") = root & "\src"
cmd = """" & pyw & """ -m go_mb"
' 0 = ventana oculta (sin CMD)
sh.Run cmd, 0, False
