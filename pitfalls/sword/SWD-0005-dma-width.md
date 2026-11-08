---
id: SWD-0005
kind: pitfall
title: DMA 内存宽度设成 Word，uint16 数组发出去全是乱码
project: sword
category: 驱动-WS2812B
tags: [WS2812B, DMA, 数据宽度, uint16, PWM]
platform: STM32F103C8T6
tool: STM32CubeMX / Keil MDK 5
severity: 致命
status: 已解决
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

DMA 启动后灯带颜色全乱，或者干脆没反应；单看数组内容又是对的。

## 原因

CubeMX 里 DMA 的 Memory Data Width 设成了 `Word`（32 位），但代码里的数组是 `uint16_t`（16 位）。DMA 按 32 位搬运，把两个半字拼成一个字，时序自然全错。

## 解法

让两边宽度一致。本次做法是把数组改成 32 位：

```c
uint32_t pwmData[LED_NUM * 24];
HAL_TIM_PWM_Start_DMA(&htim3, TIM_CHANNEL_1, (uint32_t *)pwmData, len);
```

也可以反过来把 DMA 改成 Half Word，但要注意 CCR 寄存器宽度和后续计算，别改一半。

## 排查路径

灯带乱码先查三处：DMA 宽度、数组类型、`Start_DMA` 传的长度（是"传输次数"不是字节数）。

## 相关

- SWD-0001 DMA 初始化顺序
- SWD-0006 HAL_BUSY 互锁
