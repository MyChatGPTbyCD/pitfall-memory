---
id: SWD-0010
kind: pitfall
title: 一加 printf 就卡死在 BKPT 0xAB，勾上 MicroLIB
project: sword
category: 环境与工具链
tags: [Keil, printf, MicroLIB, BKPT, Semihosting, 半主机]
platform: STM32F103C8T6
tool: Keil MDK 5
severity: 致命
status: 已解决
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

代码里加了 `printf`，一运行就停在汇编的 `0x08000564 BKPT 0xAB`，点 Run 也不走。

## 原因

Keil 默认不开 MicroLIB，也没配串口重定向。`printf` 底层走的是半主机（Semihosting）路径，向调试器请求 I/O，没有宿主响应就死锁在 BKPT 指令上。

## 解法

魔术棒（Options for Target）→ `Target` 标签页 → 勾选 **Use MicroLIB**，重新编译。

临时办法：把暂时不用的 `printf` 注释掉。但治本还是勾 MicroLIB，或者自己重定向 `fputc` 到 USART。

## 排查路径

程序停在 `BKPT` / `SVC` 这类指令上，先想到半主机和未实现的中断向量，而不是业务代码。

## 相关

- SWD-0011 Debug error 35
