VERSION 1.0 CLASS
BEGIN
  MultiUse = -1  'True
END
Attribute VB_Name = "Sheet1"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = True
Sub Main()

Dim rg As Range

Set rg = Range("A7").CurrentRegion

rg.TextToColumns Destination:=Range("A1"), ConsecutiveDelimiter:=True, DataType:=xlDelimited, Comma:=True

End Sub


