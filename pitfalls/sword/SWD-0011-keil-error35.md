---
id: SWD-0011
kind: pitfall
title: 改完代码进 Debug 报 error 35，Clean + Rebuild 就好
project: sword
category: 调试
tags: [Keil, Debug, error35, 断点, Rebuild, 符号表]
platform: STM32F103C8T6
tool: Keil MDK 5
severity: 一般
status: 已解决
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

改了几行代码重新进 Debug，左下角报：

```
*** error 35: undefined line number
```

程序起不来，断点全是灰的。

## 原因

Keil 的调试符号表和当前源码行号错位——增量编译没有把调试信息更新干净，常见于改头文件、删函数、或者切换 Target 之后。

## 解法

退出 Debug → `Project -> Clean` → `Project -> Rebuild` → 再进 Debug。

不要只点 Build（F7），Clean 会把中间文件清掉重来，这才是关键。

## 排查路径

Debug 一进去就报错、断点位置不对，基本是符号表问题，先 Clean/Rebuild，别去改代码。

## 相关

- SWD-0010 printf 卡 BKPT
- SWD-0012 程序下不进
