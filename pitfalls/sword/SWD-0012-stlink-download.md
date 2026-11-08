---
id: SWD-0012
kind: pitfall
title: ST-Link 找不到芯片 / 程序下不进去，先查 SWD 和 BOOT0
project: sword
category: 环境与工具链
tags: [Keil, ST-Link, SWD, BOOT0, 下载, SYS]
platform: STM32F103C8T6
tool: Keil MDK 5 / ST-Link
severity: 致命
status: 已解决
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

点 Download 报找不到目标，或者连上但 `Cannot access target`，程序根本下不进去。

## 原因

两个最常见的原因：

1. CubeMX 里没配调试口，芯片的 SWD 引脚没使能，ST-Link 连不上。
2. BOOT0 跳线不对，芯片从错误的存储区启动。

## 解法

1. CubeMX → `System Core -> SYS` → Debug 选 **Serial Wire**（不是 Disable，也不是 JTAG）。
2. F103 核心板 **BOOT0 接地**（BOOT0 = 0），从 Flash 启动。
3. 还连不上就按着复位键点 Download，或者把 ST-Link 的 Connect under Reset 打开。

## 排查路径

连不上按顺序：线序（SWDIO/SWCLK/GND/3V3）→ SYS 里的 Debug 配置 → BOOT0 → Connect under Reset → 换 ST-Link。

## 相关

- SWD-0010 printf 卡 BKPT
- SWD-0011 Debug error 35
