---
id: SWD-0007
kind: pitfall
title: 没有串口模块时，用 Keil Watch 窗口看变量（必须全局变量）
project: sword
category: 调试
tags: [Keil, Debug, Watch, 全局变量, 无串口, MPU6050]
platform: STM32F103C8T6
tool: Keil MDK 5
severity: 提示
status: 已解决
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

手头没有 CH340 / 串口助手，MPU6050 读出来的数不知道对不对，没法 `printf`。

## 原因

不是问题，是缺工具时的替代方案。

## 解法

用 Keil 的 Debug 模式直接看内存：

1. 在 `main.c` 定义**全局**变量：`int16_t ax, ay, az;`
   —— 局部变量在 Watch 窗口常常显示 `<cannot evaluate>` 或乱码，因为出了作用域就被优化掉了。
2. Ctrl+F5 进 Debug，在 `while(1)` 打断点。
3. `View -> Watch Windows -> Watch 1`，手动输入 `ax`、`ay`、`az`、`check`。
4. F5 运行，看数值变化。

小技巧：变量前加 `volatile` 可以防止被编译器优化掉，Watch 更稳。

## 排查路径

Watch 里显示不了，按顺序查：变量是不是局部 → 有没有被优化 → 编译优化等级是不是 -O0。

## 相关

- SWD-0008 MPU6050 读不到
- SWD-0011 Debug error 35
