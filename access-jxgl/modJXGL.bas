Attribute VB_Name = "modJXGL"
Option Compare Database
Option Explicit

'==================================================================
'  教学管理系统 主界面 一键生成模块
'  ------------------------------------------------------------------
'  用法：
'    1. 打开 05291JXGL.accdb，黄条上点【启用内容】
'    2. Alt+F11 打开 VBA 编辑器 → 文件 → 导入文件 → 选 modJXGL.bas
'    3. Ctrl+G 打开“立即窗口”，输入  BuildJXGL  回车
'
'  会生成：
'    窗体 frmMain            主界面（原来的 frmMain 自动备份成 frmMain_old）
'         frmTC              排课管理
'         frmGradeEntry      成绩录入
'         frmTeacherSchedule 教师个人课表查询
'         frmPrereq          先修课查询
'         frmStudentSchedule 学生个人课表查询
'         frmTotalGrade      总评成绩查询
'    查询 qryGradeEntry / qryTeacherSchedule / qryPrereq /
'         qryCourseTeacher / qryStudentSchedule / qryTotalGrade
'
'  注意：本模块生成完也要留在数据库里，按钮会调用最下面的 JX_ 函数。
'        想重新生成就再运行一次 BuildJXGL，自动生成的窗体会被覆盖。
'==================================================================

Public Const SYS_TITLE As String = "USST教学管理系统"      '<- 标题改这里

Private Const FONT_TITLE As String = "华文彩云"
Private Const FONT_CN As String = "宋体"
Private Const AUTO_TAG As String = "JXGL_AUTO"

Private Const SQL_TEACHER As String = "SELECT Tno, Tno & '  ' & Tname FROM Teacher ORDER BY Tno;"
Private Const SQL_COURSE As String = "SELECT Cno, Cno & '  ' & Cname FROM Course ORDER BY Cno;"
Private Const SQL_STUDENT As String = "SELECT Sno, Sno & '  ' & Sname FROM Student ORDER BY Sno;"


'==================================================================
'  入口：运行这个
'==================================================================
Public Sub BuildJXGL()
    On Error GoTo EH

    CloseAllForms

    ' ---------- 1. 查询 ----------
    MakeQuery "qryGradeEntry", _
        "SELECT SC.Sno, Student.Sname, SC.Cno, Course.Cname, SC.Grade " & _
        "FROM (SC INNER JOIN Student ON SC.Sno = Student.Sno) " & _
        "INNER JOIN Course ON SC.Cno = Course.Cno ORDER BY SC.Cno, SC.Sno;"

    MakeQuery "qryTeacherSchedule", _
        "SELECT TC.Tno, Teacher.Tname, Teacher.Title, TC.Cno, Course.Cname, Course.Ccredit " & _
        "FROM (TC INNER JOIN Teacher ON TC.Tno = Teacher.Tno) " & _
        "INNER JOIN Course ON TC.Cno = Course.Cno ORDER BY TC.Tno, TC.Cno;"

    MakeQuery "qryPrereq", _
        "SELECT C.Cno, C.Cname, C.Ccredit, C.Cpno, P.Cname AS PreName, PP.Cname AS PrePreName " & _
        "FROM (Course AS C LEFT JOIN Course AS P ON C.Cpno = P.Cno) " & _
        "LEFT JOIN Course AS PP ON P.Cpno = PP.Cno ORDER BY C.Cno;"

    MakeQuery "qryCourseTeacher", _
        "SELECT TC.Cno, Teacher.Tname FROM TC INNER JOIN Teacher ON TC.Tno = Teacher.Tno;"

    MakeQuery "qryStudentSchedule", _
        "SELECT SC.Sno, Student.Sname, SC.Cno, Course.Cname, Course.Ccredit, qryCourseTeacher.Tname " & _
        "FROM ((SC INNER JOIN Student ON SC.Sno = Student.Sno) " & _
        "INNER JOIN Course ON SC.Cno = Course.Cno) " & _
        "LEFT JOIN qryCourseTeacher ON SC.Cno = qryCourseTeacher.Cno ORDER BY SC.Sno, SC.Cno;"

    MakeQuery "qryTotalGrade", _
        "SELECT SC.Sno, Student.Sname, SC.Cno, Course.Cname, Course.Ccredit, SC.Grade " & _
        "FROM (SC INNER JOIN Student ON SC.Sno = Student.Sno) " & _
        "INNER JOIN Course ON SC.Cno = Course.Cno ORDER BY SC.Sno, SC.Cno;"

    ' ---------- 2. 功能窗体 ----------
    ' 列定义格式： "类型|字段或表达式|列标题|宽度(厘米)[|附加]"
    '   R = 只读字段   E = 可编辑字段(附加：有效性规则|有效性文本)
    '   X = 计算列     K = 下拉框字段(附加：下拉列表SQL)

    ' 教务：排课管理
    BuildListForm "frmTC", "排课管理", _
        "SELECT TC.Tno, TC.Cno FROM TC ORDER BY TC.Tno, TC.Cno;", _
        Array("K|Tno|授课教师|4.6|" & SQL_TEACHER, _
              "K|Cno|课程|4.6|" & SQL_COURSE), _
        "Tno", "按教师筛选：", SQL_TEACHER, True, Array(), _
        "提示：在最下面带 * 号的空白行选好教师和课程，就能新增一条排课。"

    ' 教师：成绩录入
    BuildListForm "frmGradeEntry", "成绩录入", "qryGradeEntry", _
        Array("R|Cno|课程号|1.5", "R|Cname|课程名称|3", "R|Sno|学号|2.8", "R|Sname|姓名|2", _
              "E|Grade|成绩|1.8|Is Null Or Between 0 And 100|成绩要在 0～100 之间"), _
        "Cno", "选择课程：", SQL_COURSE, False, _
        Array("选课人数|=Count(*)|1.2", "平均分|=Round(Avg([Grade]),1)|1.3", _
              "最高分|=Max([Grade])|1.2", "最低分|=Min([Grade])|1.2"), _
        "提示：先选课程，再在“成绩”列直接输入分数，按回车自动保存。"

    ' 教师：个人课表查询
    BuildListForm "frmTeacherSchedule", "教师个人课表查询", "qryTeacherSchedule", _
        Array("R|Tno|教师号|1.6", "R|Tname|姓名|1.8", "R|Title|职称|1.8", _
              "R|Cno|课程号|1.5", "R|Cname|课程名称|3", "R|Ccredit|学分|1.2"), _
        "Tno", "选择教师：", SQL_TEACHER, False, _
        Array("授课门数|=Count(*)|1.2", "总学分|=Sum([Ccredit])|1.2"), ""

    ' 学生：先修课查询
    BuildListForm "frmPrereq", "先修课查询", "qryPrereq", _
        Array("R|Cno|课程号|1.5", "R|Cname|课程名称|2.8", "R|Ccredit|学分|1.2", _
              "X|=Nz([Cpno],""—"")|先修课号|1.6", _
              "X|=Nz([PreName],""无"")|直接先修课|2.8", _
              "X|=Nz([PrePreName],""无"")|间接先修课|2.8"), _
        "Cno", "选择课程：", SQL_COURSE, False, Array(), _
        "说明：学这门课之前要先修完“直接先修课”；“间接先修课”是先修课的先修课。"

    ' 学生：个人课表查询
    BuildListForm "frmStudentSchedule", "学生个人课表查询", "qryStudentSchedule", _
        Array("R|Sno|学号|2.6", "R|Sname|姓名|1.8", "R|Cno|课程号|1.5", _
              "R|Cname|课程名称|3", "R|Ccredit|学分|1.2", _
              "X|=Nz([Tname],""待安排"")|任课教师|2"), _
        "Sno", "选择学生：", SQL_STUDENT, False, Array(), ""

    ' 学生：总评成绩查询
    BuildListForm "frmTotalGrade", "总评成绩查询", "qryTotalGrade", _
        Array("R|Sno|学号|2.6", "R|Sname|姓名|1.8", "R|Cno|课程号|1.5", "R|Cname|课程名称|3", _
              "R|Ccredit|学分|1.2", "R|Grade|成绩|1.4", _
              "X|=IIf(IsNull([Grade]),""未录入"",IIf([Grade]>=60,""通过"",""未通过""))|结果|1.6"), _
        "Sno", "选择学生：", SQL_STUDENT, False, _
        Array("平均分|=Round(Avg([Grade]),1)|1.3", _
              "加权平均分|=Round(Sum(Nz([Grade],0)*[Ccredit])/IIf(Sum(IIf(IsNull([Grade]),0,[Ccredit]))=0,Null,Sum(IIf(IsNull([Grade]),0,[Ccredit]))),1)|1.3", _
              "已获学分|=Sum(IIf(Nz([Grade],0)>=60,[Ccredit],0))|1.2"), _
        "提示：加权平均分 = Σ(成绩×学分) ÷ Σ学分；60 分及以上才算拿到学分。"

    ' ---------- 3. 主界面 ----------
    BuildFrmMain

    Application.RefreshDatabaseWindow
    MsgBox "全部生成好啦！" & vbCrLf & vbCrLf & _
           "主界面：frmMain（原来的已备份为 frmMain_old）" & vbCrLf & _
           "新窗体：frmTC、frmGradeEntry、frmTeacherSchedule、" & vbCrLf & _
           "        frmPrereq、frmStudentSchedule、frmTotalGrade", _
           vbInformation, SYS_TITLE
    DoCmd.OpenForm "frmMain"
    Exit Sub

EH:
    MsgBox "生成时出错了：" & vbCrLf & Err.Number & "  " & Err.Description & vbCrLf & vbCrLf & _
           "把没保存的“窗体1”之类的窗口关掉（不保存），再运行一次 BuildJXGL 试试。", _
           vbExclamation, SYS_TITLE
End Sub


'==================================================================
'  主界面 frmMain（照着老师的设计：标题 + 教务/教师/学生 三列按钮）
'==================================================================
Private Sub BuildFrmMain()
    Dim frm As Form, c As Control
    Dim x1 As Double, x2 As Double, x3 As Double

    x1 = 1: x2 = 5.5: x3 = 10           ' 三列按钮的左边距（厘米）

    Set frm = NewForm("frmMain", False)
    With frm
        .Caption = SYS_TITLE
        .RecordSelectors = False
        .NavigationButtons = False
        .DividingLines = False
        .ScrollBars = 0
        .AutoCenter = True
        .Tag = AUTO_TAG
        .Width = cm(14)
        .Section(acDetail).Height = cm(8.2)
        .Section(acDetail).BackColor = RGB(255, 255, 255)
    End With

    ' 大标题（华文彩云，空心字）
    Set c = AddLabel(frm, acDetail, "lblTitle", SYS_TITLE, 0.5, 0.35, 13, 1.7, 28, False, FONT_TITLE)
    c.TextAlign = 2
    c.ForeColor = ClrDark()

    ' 三个分组标题
    AddGroup frm, "lblAdmin", "教务", x1
    AddGroup frm, "lblTeacher", "教师", x2
    AddGroup frm, "lblStudent", "学生", x3

    ' 教务（前三个用你库里现成的 mcrMain 宏）
    MenuBtn frm, "cmdStudent", "学生信息管理", "mcrMain.OpenStudent", x1, 1
    MenuBtn frm, "cmdCourse", "课程信息管理", "mcrMain.OpenCourse", x1, 2
    MenuBtn frm, "cmdSC", "选课管理", "mcrMain.OpenSC", x1, 3
    MenuBtn frm, "cmdTC", "排课管理", OpenExpr("frmTC"), x1, 4

    ' 教师
    MenuBtn frm, "cmdGradeEntry", "成绩录入", OpenExpr("frmGradeEntry"), x2, 1
    MenuBtn frm, "cmdTeacherSchedule", "个人课表查询", OpenExpr("frmTeacherSchedule"), x2, 2

    ' 学生
    MenuBtn frm, "cmdPrereq", "先修课查询", OpenExpr("frmPrereq"), x3, 1
    MenuBtn frm, "cmdStudentSchedule", "个人课表查询", OpenExpr("frmStudentSchedule"), x3, 2
    MenuBtn frm, "cmdTotalGrade", "总评成绩查询", OpenExpr("frmTotalGrade"), x3, 3

    SaveFormAs frm, "frmMain"
End Sub

Private Sub AddGroup(ByVal frm As Form, ByVal nm As String, ByVal cap As String, ByVal x As Double)
    Dim c As Control
    Set c = AddLabel(frm, acDetail, nm, cap, x, 2.3, 3, 0.75, 14, True)
    c.TextAlign = 2
    c.ForeColor = ClrDark()
    Set c = CreateControl(frm.Name, acLine, acDetail, "", "", cm(x + 0.4), cm(3.05), cm(2.2), 0)
    c.Name = "lin" & nm
    c.BorderColor = ClrLine()
    c.BorderWidth = 2
End Sub

Private Sub MenuBtn(ByVal frm As Form, ByVal nm As String, ByVal cap As String, ByVal act As String, _
                    ByVal x As Double, ByVal rowNo As Integer)
    AddButton frm, acDetail, nm, cap, act, x, 3.3 + (rowNo - 1) * 1.1, 3, 0.8, 12, True
End Sub

Private Function OpenExpr(ByVal formName As String) As String
    OpenExpr = "=JX_Open(""" & formName & """)"
End Function


'==================================================================
'  通用“列表 + 筛选”窗体（连续窗体：页眉放标题/筛选/列标题，页脚放统计/按钮）
'==================================================================
Private Sub BuildListForm(ByVal formName As String, ByVal frmCaption As String, ByVal recSrc As String, _
                          ByVal cols As Variant, ByVal fltField As String, ByVal fltCaption As String, _
                          ByVal fltSql As String, ByVal canAddDel As Boolean, ByVal sums As Variant, _
                          ByVal tip As String)
    Const ML As Double = 0.5            ' 左右留白（厘米）
    Dim frm As Form, c As Control
    Dim i As Integer, p As Variant
    Dim colsW As Double, sumsW As Double, totalW As Double
    Dim x As Double, y As Double, w As Double, x0 As Double, tipH As Double

    ' ---- 先算宽度 ----
    For i = LBound(cols) To UBound(cols)
        p = Split(cols(i), "|")
        colsW = colsW + Val(p(3))
    Next i
    For i = LBound(sums) To UBound(sums)
        p = Split(sums(i), "|")
        sumsW = sumsW + LabelW(CStr(p(0))) + Val(p(2)) + 0.3
    Next i
    totalW = colsW
    If sumsW > totalW Then totalW = sumsW
    If totalW < 10.5 Then totalW = 10.5
    totalW = totalW + ML * 2
    x0 = (totalW - colsW) / 2

    ' ---- 窗体属性 ----
    Set frm = NewForm(formName, True)
    With frm
        .RecordSource = recSrc
        .Caption = frmCaption
        .DefaultView = 1                ' 连续窗体
        .RecordSelectors = canAddDel
        .NavigationButtons = False
        .DividingLines = False
        .ScrollBars = 2                 ' 只要垂直滚动条
        .AllowEdits = True              ' 必须为“是”，否则页眉里的筛选下拉框也没法选
        .AllowAdditions = canAddDel
        .AllowDeletions = canAddDel
        .AutoCenter = True
        .Tag = AUTO_TAG
        .Width = cm(totalW)
        .Section(acHeader).Height = cm(4)
        .Section(acDetail).Height = cm(0.7)
        .Section(acFooter).Height = cm(3)
    End With
    SetRowColors frm

    ' ---- 窗体页眉：标题 ----
    Set c = AddLabel(frm, acHeader, "lblTitle", frmCaption, ML, 0.25, totalW - ML * 2, 0.9, 16, True)
    c.TextAlign = 2
    c.ForeColor = ClrDark()
    y = 1.35

    ' ---- 窗体页眉：筛选行 ----
    If Len(fltField) > 0 Then
        Set c = AddLabel(frm, acHeader, "lblFilter", fltCaption, ML, y + 0.05, 2.4, 0.55, 10, True)
        c.TextAlign = 3
        Set c = AddCombo(frm, acHeader, "cboFilter", "", fltSql, ML + 2.5, y, 4.6, 0.6)
        c.AfterUpdate = "=JX_Filter(""" & formName & """,""" & fltField & """,""cboFilter"")"
        AddButton frm, acHeader, "cmdShowAll", "显示全部", _
            "=JX_ShowAll(""" & formName & """,""cboFilter"")", ML + 7.4, y, 2, 0.6
        y = y + 0.9
    End If

    ' ---- 窗体页眉：列标题 ----
    x = x0
    For i = LBound(cols) To UBound(cols)
        p = Split(cols(i), "|")
        w = Val(p(3))
        Set c = AddLabel(frm, acHeader, "lblHead" & i, CStr(p(2)), x, y, w, 0.6, 10, True)
        c.TextAlign = 2
        c.BackStyle = 1
        c.BackColor = ClrHead()
        c.BorderStyle = 1
        c.BorderColor = ClrLine()
        x = x + w
    Next i
    frm.Section(acHeader).Height = cm(y + 0.65)

    ' ---- 主体：每列一个控件 ----
    x = x0
    For i = LBound(cols) To UBound(cols)
        p = Split(cols(i), "|")
        w = Val(p(3))
        Select Case CStr(p(0))
            Case "R"
                AddText frm, acDetail, "txt" & p(1), CStr(p(1)), x, 0.05, w, 0.6, False
            Case "E"
                Set c = AddText(frm, acDetail, "txt" & p(1), CStr(p(1)), x, 0.05, w, 0.6, True)
                If UBound(p) >= 5 Then
                    c.ValidationRule = CStr(p(4))
                    c.ValidationText = CStr(p(5))
                End If
            Case "X"
                AddText frm, acDetail, "txtCalc" & i, CStr(p(1)), x, 0.05, w, 0.6, False
            Case "K"
                AddCombo frm, acDetail, "cbo" & p(1), CStr(p(1)), CStr(p(4)), x, 0.05, w, 0.6
        End Select
        x = x + w
    Next i
    frm.Section(acDetail).Height = cm(0.7)

    ' ---- 窗体页脚：统计 ----
    y = 0.25
    If UBound(sums) >= LBound(sums) Then
        x = ML
        For i = LBound(sums) To UBound(sums)
            p = Split(sums(i), "|")
            w = LabelW(CStr(p(0)))
            Set c = AddLabel(frm, acFooter, "lblSum" & i, p(0) & "：", x, y + 0.05, w, 0.55, 10, True)
            c.TextAlign = 3
            Set c = AddText(frm, acFooter, "txtSum" & i, CStr(p(1)), x + w, y, Val(p(2)), 0.6, False)
            c.FontBold = True
            c.ForeColor = ClrDark()
            x = x + w + Val(p(2)) + 0.3
        Next i
        y = y + 0.85
    End If

    ' ---- 窗体页脚：提示 ----
    If Len(tip) > 0 Then
        tipH = 0.5 * -Int(-(Len(tip) * 0.34) / (totalW - ML * 2)) + 0.1
        Set c = AddLabel(frm, acFooter, "lblTip", tip, ML, y, totalW - ML * 2, tipH, 9, False)
        c.ForeColor = ClrGray()
        y = y + tipH + 0.15
    End If

    ' ---- 窗体页脚：按钮 ----
    x = totalW - ML - 2
    AddButton frm, acFooter, "cmdClose", "关闭", "=JX_Close(""" & formName & """)", x, y, 2, 0.65
    If canAddDel Then
        AddButton frm, acFooter, "cmdDelete", "删除当前行", _
            "=JX_DeleteRecord(""" & formName & """)", x - 2.7, y, 2.5, 0.65
    End If
    frm.Section(acFooter).Height = cm(y + 0.9)

    SaveFormAs frm, formName
End Sub


'==================================================================
'  建控件的小工具
'==================================================================
Private Function AddLabel(ByVal frm As Form, ByVal sec As Integer, ByVal nm As String, ByVal cap As String, _
                          ByVal l As Double, ByVal t As Double, ByVal w As Double, ByVal h As Double, _
                          Optional ByVal fs As Integer = 10, Optional ByVal isBold As Boolean = False, _
                          Optional ByVal fontNm As String = FONT_CN) As Control
    Dim c As Control
    Set c = CreateControl(frm.Name, acLabel, sec, "", "", cm(l), cm(t), cm(w), cm(h))
    c.Name = nm
    c.Caption = cap
    c.FontName = fontNm
    c.FontSize = fs
    c.FontBold = isBold
    Set AddLabel = c
End Function

Private Function AddText(ByVal frm As Form, ByVal sec As Integer, ByVal nm As String, ByVal src As String, _
                         ByVal l As Double, ByVal t As Double, ByVal w As Double, ByVal h As Double, _
                         ByVal editable As Boolean) As Control
    Dim c As Control
    Set c = CreateControl(frm.Name, acTextBox, sec, "", "", cm(l), cm(t), cm(w), cm(h))
    c.Name = nm
    c.ControlSource = src
    c.FontName = FONT_CN
    c.FontSize = 10
    c.TextAlign = 2
    If editable Then
        c.BackStyle = 1
        c.BackColor = RGB(255, 255, 255)
        c.BorderStyle = 1
        c.BorderColor = ClrLine()
    Else
        c.Locked = True
        c.TabStop = False
        c.BackStyle = 0
        c.BorderStyle = 0
    End If
    Set AddText = c
End Function

' 两列下拉框：第 1 列(编号)隐藏并作为绑定列，第 2 列显示“编号  名称”
Private Function AddCombo(ByVal frm As Form, ByVal sec As Integer, ByVal nm As String, ByVal src As String, _
                          ByVal rowSql As String, ByVal l As Double, ByVal t As Double, _
                          ByVal w As Double, ByVal h As Double) As Control
    Dim c As Control
    Set c = CreateControl(frm.Name, acComboBox, sec, "", "", cm(l), cm(t), cm(w), cm(h))
    c.Name = nm
    c.ControlSource = src
    c.RowSourceType = "Table/Query"
    c.RowSource = rowSql
    c.ColumnCount = 2
    c.BoundColumn = 1
    c.ColumnWidths = "0;" & CStr(cm(w))
    c.ListWidth = cm(w)
    c.ListRows = 12
    c.LimitToList = True
    c.FontName = FONT_CN
    c.FontSize = 10
    Set AddCombo = c
End Function

Private Function AddButton(ByVal frm As Form, ByVal sec As Integer, ByVal nm As String, ByVal cap As String, _
                           ByVal act As String, ByVal l As Double, ByVal t As Double, ByVal w As Double, _
                           ByVal h As Double, Optional ByVal fs As Integer = 10, _
                           Optional ByVal isBold As Boolean = False) As Control
    Dim c As Control
    Set c = CreateControl(frm.Name, acCommandButton, sec, "", "", cm(l), cm(t), cm(w), cm(h))
    c.Name = nm
    c.Caption = cap
    c.OnClick = act
    c.FontName = FONT_CN
    c.FontSize = fs
    c.FontBold = isBold
    ' 下面这些是 Access 2010 及以后才有的外观属性，老版本没有就自动跳过
    SetProp c, "UseTheme", True
    SetProp c, "BackColor", ClrBtn()
    SetProp c, "BorderColor", ClrLine()
    SetProp c, "HoverColor", ClrHover()
    SetProp c, "PressedColor", ClrLine()
    SetProp c, "ForeColor", ClrDark()
    SetProp c, "HoverForeColor", ClrDark()
    SetProp c, "PressedForeColor", ClrDark()
    Set AddButton = c
End Function

Private Sub SetProp(ByVal ctl As Object, ByVal propName As String, ByVal v As Variant)
    On Error Resume Next
    ctl.Properties(propName).Value = v
    Err.Clear
End Sub

Private Sub SetRowColors(ByVal frm As Form)
    On Error Resume Next
    frm.Section(acDetail).BackColor = RGB(255, 255, 255)
    frm.Section(acDetail).AlternateBackColor = RGB(242, 246, 252)
    Err.Clear
End Sub

Private Function cm(ByVal x As Double) As Long
    cm = CLng(x * 567)                  ' 1 厘米 = 567 缇
End Function

Private Function LabelW(ByVal s As String) As Double
    LabelW = (Len(s) + 1) * 0.42 + 0.2
End Function

Private Function ClrDark() As Long
    ClrDark = RGB(31, 78, 121)
End Function

Private Function ClrHead() As Long
    ClrHead = RGB(221, 235, 247)
End Function

Private Function ClrLine() As Long
    ClrLine = RGB(157, 195, 230)
End Function

Private Function ClrBtn() As Long
    ClrBtn = RGB(232, 242, 251)
End Function

Private Function ClrHover() As Long
    ClrHover = RGB(189, 215, 238)
End Function

Private Function ClrGray() As Long
    ClrGray = RGB(118, 118, 118)
End Function


'==================================================================
'  建 / 存 / 删 窗体和查询
'==================================================================
Private Function NewForm(ByVal targetName As String, ByVal withHdrFtr As Boolean) As Form
    Dim frm As Form
    PrepareName targetName
    Set frm = CreateForm()
    If withHdrFtr Then
        On Error Resume Next
        DoCmd.SelectObject acForm, frm.Name, False
        On Error GoTo 0
        DoCmd.RunCommand acCmdFormHdrFtr        ' 打开“窗体页眉/页脚”
        If Not HasSection(frm, acHeader) Then
            Err.Raise vbObjectError + 513, , "没能给 " & targetName & " 加上窗体页眉/页脚"
        End If
    End If
    Set NewForm = frm
End Function

Private Sub SaveFormAs(ByVal frm As Form, ByVal targetName As String)
    Dim tmp As String
    tmp = frm.Name
    DoCmd.Close acForm, tmp, acSaveYes
    If StrComp(tmp, targetName, vbBinaryCompare) <> 0 Then
        DoCmd.Rename targetName, acForm, tmp
    End If
End Sub

' 名字被占用时：本模块生成的直接删掉；别的（比如原来的 frmMain）改名备份成 xxx_old
Private Sub PrepareName(ByVal n As String)
    Dim isAuto As Boolean, bak As String, k As Integer
    If Not FormExists(n) Then Exit Sub
    If CurrentProject.AllForms(n).IsLoaded Then DoCmd.Close acForm, n, acSavePrompt

    DoCmd.OpenForm n, acDesign, , , , acHidden
    isAuto = (Forms(n).Tag = AUTO_TAG)
    DoCmd.Close acForm, n, acSaveNo

    If isAuto Then
        DoCmd.DeleteObject acForm, n
    Else
        bak = n & "_old"
        k = 1
        Do While FormExists(bak)
            k = k + 1
            bak = n & "_old" & k
        Loop
        DoCmd.Rename bak, acForm, n
    End If
End Sub

Private Function FormExists(ByVal n As String) As Boolean
    Dim ao As AccessObject
    For Each ao In CurrentProject.AllForms
        If StrComp(ao.Name, n, vbTextCompare) = 0 Then
            FormExists = True
            Exit Function
        End If
    Next ao
End Function

Private Function HasSection(ByVal frm As Form, ByVal s As Integer) As Boolean
    Dim h As Long
    On Error Resume Next
    h = frm.Section(s).Height
    HasSection = (Err.Number = 0)
    Err.Clear
End Function

Private Sub CloseAllForms()
    Dim guard As Integer
    Do While Forms.Count > 0 And guard < 50
        DoCmd.Close acForm, Forms(0).Name, acSavePrompt
        guard = guard + 1
    Loop
End Sub

Private Sub MakeQuery(ByVal qName As String, ByVal sqlText As String)
    Dim db As Object, qd As Object
    Set db = CurrentDb
    On Error Resume Next
    Set qd = db.QueryDefs(qName)
    On Error GoTo 0
    If qd Is Nothing Then
        db.CreateQueryDef qName, sqlText
    Else
        qd.SQL = sqlText
    End If
End Sub


'==================================================================
'  按钮 / 下拉框调用的函数 —— 生成完也不要删！
'==================================================================
Public Function JX_Open(ByVal frmName As String)
    DoCmd.OpenForm frmName
End Function

Public Function JX_Close(ByVal frmName As String)
    DoCmd.Close acForm, frmName, acSaveNo
End Function

Public Function JX_Filter(ByVal frmName As String, ByVal fieldName As String, ByVal ctlName As String)
    Dim f As Form, v As Variant
    Set f = Forms(frmName)
    v = f.Controls(ctlName).Value
    If IsNull(v) Then
        f.FilterOn = False
    Else
        f.Filter = "[" & fieldName & "]='" & Replace(CStr(v), "'", "''") & "'"
        f.FilterOn = True
    End If
End Function

Public Function JX_ShowAll(ByVal frmName As String, ByVal ctlName As String)
    Dim f As Form
    Set f = Forms(frmName)
    f.Controls(ctlName).Value = Null
    f.Filter = ""
    f.FilterOn = False
End Function

Public Function JX_DeleteRecord(ByVal frmName As String)
    On Error GoTo EH
    If Forms(frmName).NewRecord Then
        MsgBox "先点一下要删除的那一行，再点“删除当前行”。", vbInformation
        Exit Function
    End If
    DoCmd.RunCommand acCmdDeleteRecord
    Exit Function
EH:
    If Err.Number <> 2501 Then MsgBox Err.Description, vbExclamation
End Function
