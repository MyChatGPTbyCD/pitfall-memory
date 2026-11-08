---
id: SWD-0002
kind: pitfall
title: 时钟树报 No solution found，多半是 APB1 超频
project: sword
category: 环境与工具链
tags: [CubeMX, 时钟树, PLL, APB1, HSE, F103]
platform: STM32F103C8T6
tool: STM32CubeMX
severity: 严重
status: 已解决
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

Clock Configuration 页配完，系统提示 `No solution found`，或者频率怎么调都对不上。

## 原因

PLL 倍频系数与系统时钟源没正确映射；另一个常见原因是 APB1 分频设错，导致 APB1 超过 36 MHz 上限，CubeMX 直接判定无解。

## 解法

本次可用配置：

- HSE = 8 MHz
- PLLMul = ×9 → 72 MHz
- System Clock Mux = PLLCLK
- **APB1 Prescaler = /2**（F103 的 APB1 最高 36 MHz）
- APB2 Prescaler = /1

## 排查路径

报 No solution 时，先看 APB1/APB2 分频，再看 PLL 输入源（HSE 还是 HSI），最后才怀疑晶振实际频率。

## 相关

- SWD-0001 初始化顺序
