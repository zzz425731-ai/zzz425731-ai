<h1 align="center">Zachary Chou</h1>

<p align="center">
  <strong>你好，我是 Zachary。 / Hi, I'm Zachary.</strong>
</p>

<p align="center">
  把想法写下来，把第一步做出来。<br />
  <em>Write ideas down. Take the first step.</em>
</p>

<p align="center">
  <img src="./assets/badges.svg" width="216" height="20" alt="AI-assisted · GitHub · Learning" />
</p>

<p align="center">
  <a href="https://github.com/zzz425731-ai?tab=repositories">我的项目 / My repositories ↗</a>
</p>

## 关于我 / About me

- **人工智能专业本科生，正在系统学习 Python 与 AI 工程基础。**<br />
  An Artificial Intelligence undergraduate building a foundation in Python and AI engineering.
- **通过项目练习代码组织、测试与交互设计。**<br />
  Learning to organize, test, and build usable software through hands-on projects.
- **关注 AI 工程、Python 开发与软件研发实习机会。**<br />
  Interested in internships in AI engineering, Python development, and software engineering.

## 技术栈 / Stack

**PyMem 中使用 / Used in PyMem:** Python 标准库 / standard library · HTML/CSS · JavaScript · Pyodide / WebAssembly · Web Worker · JSON · localStorage

## 项目一角 / Projects

### PyMem · Python 间隔复习工具 / Python practice with spaced repetition

一个 AI 辅助开发的学习项目，将 Python 练习、答案校验与到期复习串联起来。<br />
A learning project built with AI assistance, combining Python practice, answer checking, and scheduled review.

> **开发中 / In development:** [PR #1](https://github.com/zzz425731-ai/zzz425731-ai/pull/1) 仍开放，尚未合并，未正式发布。<br />
> PR #1 is open and unmerged; this is not a published release.

**PR 中已实现 / Implemented in the PR**

| 技术实践 / Area | 实现 / Implementation |
| :--- | :--- |
| Python 与题库 / Python & question bank | 使用 `dataclasses` 组织 **135 道题、14 个主题**，终端与网页复用题库；覆盖概念、输出预测、表达式与代码编写。<br />A shared card model supports 135 exercises across 14 topics and four question types. |
| 自动判题 / Answer checking | 运行 Python 生成输出预测答案；表达式用额外输入校验，编程题运行测试表达式，捕获输出与异常；概念题自评。<br />Python execution supplies expected output and checks expressions and code against additional inputs or tests. Concept cards are self-graded. |
| 学习算法 / Review scheduling | 六级 Leitner 盒子，间隔为 **0 / 1 / 3 / 7 / 14 / 30 天**；优先安排到期题，新题按主题交错选取。<br />Six Leitner boxes prioritize due reviews and interleave new cards across topics. |
| 网页技术 / Web interface | 手机友好页面，使用 Pyodide 在 Web Worker 中执行 Python；支持超时终止，运行时不可用时退回自评。<br />A phone-oriented interface runs Python through Pyodide in a worker, with timeout handling and a self-grading fallback. |
| 进度保存 / Persistence | 终端以临时文件和原子替换保存 JSON；网页通过 localStorage 保存并回放事件日志，支持兼容终端格式的 JSON 备份导入与导出。<br />Atomic JSON saves in the CLI; localStorage event replay and compatible JSON backup import/export on the web. |

**已验证 / Verified locally**（2026-10-29 · [源码 / source `a13d5c2`](https://github.com/zzz425731-ai/zzz425731-ai/commit/a13d5c2bd31dbbd524bf96865a458b769ebce022)）：在 Python 3.12.14 下运行 `python pymem.py selftest`，结果为 **135 道题、0 跳过、0 问题**。<br />
The existing question-bank self-test checked 135 cards with no skips or reported problems under Python 3.12.14.

**待验证 / Pending validation:** 浏览器内 Pyodide 加载与完整判题流程、手机浏览器兼容性及依赖宿主环境的账号同步尚未完成端到端验证。<br />
Pyodide loading and the full browser checking flow, mobile compatibility, and host-dependent account sync have not been validated end to end.

[项目说明 / Guide](https://github.com/zzz425731-ai/zzz425731-ai/blob/a13d5c2bd31dbbd524bf96865a458b769ebce022/python-memory-trainer/README.md) · [源码 / Code](https://github.com/zzz425731-ai/zzz425731-ai/tree/a13d5c2bd31dbbd524bf96865a458b769ebce022/python-memory-trainer) · [开发进展 / PR #1](https://github.com/zzz425731-ai/zzz425731-ai/pull/1)

<p align="center">
  <em>慢慢积累，持续更新。 / Keep learning. Keep building.</em>
</p>
