# 教学管理系统主界面（frmMain）一键生成

照老师投影上的设计，给 `05291JXGL.accdb` 生成主界面：标题，加上“教务 / 教师 / 学生”三列共 9 个按钮。每个按钮背后的功能窗体也会一起生成，点开就能用。

| 文件 | 用途 |
| --- | --- |
| `modJXGL.bas` | **导入用**（GBK 编码，中文 Windows 的 VBA 编辑器直接认） |
| `modJXGL_paste.txt` | 复制粘贴用 / 在网页上看代码用（UTF-8） |

## 用法（3 步）

1. 打开 `05291JXGL.accdb`，点黄条上的 **【启用内容】**（不点的话代码跑不了）。
2. 按 `Alt+F11` 打开 VBA 编辑器，点 **文件 → 导入文件**，选择 `modJXGL.bas`。
3. 按 `Ctrl+G` 打开“立即窗口”，输入 `BuildJXGL`，回车。

看到“全部生成好啦！”的提示，`frmMain` 就会自动打开。

> 导入不了的话：VBA 编辑器里点 **插入 → 模块**，先 `Ctrl+A` 把里面自带的内容删掉，再把 `modJXGL_paste.txt` 整段粘贴进去，然后照样执行第 3 步。

## 生成了什么

原来的 `frmMain` 不会被删，会自动改名备份成 `frmMain_old`。登录宏 `mcrLogin` 登录后打开的还是 `frmMain`，所以会直接进新界面。

| 分组 | 按钮 | 打开 | 说明 |
| --- | --- | --- | --- |
| 教务 | 学生信息管理 | `frmStudent` | 用原有宏 `mcrMain.OpenStudent` |
| 教务 | 课程信息管理 | `frmCourse` | 用原有宏 `mcrMain.OpenCourse` |
| 教务 | 选课管理 | `frmSC` | 用原有宏 `mcrMain.OpenSC` |
| 教务 | 排课管理 | `frmTC`（新） | 维护 TC 表，用下拉框选教师和课程，可以新增、删除 |
| 教师 | 成绩录入 | `frmGradeEntry`（新） | 先选课程，再直接填成绩（限 0～100），页脚显示人数、平均分、最高分、最低分 |
| 教师 | 个人课表查询 | `frmTeacherSchedule`（新） | 选教师，列出他教的课和总学分 |
| 学生 | 先修课查询 | `frmPrereq`（新） | 选课程，显示直接先修课和间接先修课 |
| 学生 | 个人课表查询 | `frmStudentSchedule`（新） | 选学生，列出选的课和任课教师 |
| 学生 | 总评成绩查询 | `frmTotalGrade`（新） | 选学生，显示各科成绩和是否通过，页脚有平均分、加权平均分、已获学分 |

同时还会新建这几个查询：`qryGradeEntry`、`qryTeacherSchedule`、`qryPrereq`、`qryCourseTeacher`、`qryStudentSchedule`、`qryTotalGrade`。

**注意：** `modJXGL` 模块生成完也要留在库里，因为新按钮调用的是里面的 `JX_` 函数。改完想重新生成，再运行一次 `BuildJXGL` 就行，它只会覆盖自己生成的那几个窗体。

## 改标题

老师投影上的标题，中间有两个字太糊认不出来，所以默认写的是 `USST教学管理系统`。要改的话，在模块最上面找到这一行：

```vb
Public Const SYS_TITLE As String = "USST教学管理系统"      '<- 标题改这里
```

改完重新运行 `BuildJXGL`。

## 如果要求手动画（设计视图要点）

- **窗体属性**：记录选择器 = 否，导航按钮 = 否，分隔线 = 否，滚动条 = 两者均无，自动居中 = 是。
- **标题**：标签，字体 *华文彩云*，28 号，居中。
- **分组标题**：“教务”“教师”“学生”三个标签，14 号，加粗。
- **按钮**：每列 3 cm 宽，0.8 cm 高，上下间距 1.1 cm。在属性表 → 事件 → 单击里选宏，比如 `mcrMain.OpenStudent`。
