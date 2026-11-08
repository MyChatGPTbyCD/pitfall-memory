---
id: SWD-0001
kind: pitfall
title: DMA 没初始化就绑定 TIM，灯带不亮或程序卡死
project: sword
category: 外设初始化
tags: [CubeMX, HAL, DMA, TIM3, 初始化顺序, F103]
platform: STM32F103C8T6
tool: STM32CubeMX / Keil MDK 5
severity: 致命
status: 已解决
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

代码生成完，WS2812B 灯珠死活不亮；有时候直接卡死。业务代码怎么改都没反应，单步也看不出异常。

## 原因

F1 系列 HAL 在 `MX_TIM3_Init()` 里会经 `HAL_TIM_PWM_MspInit` 去绑定 DMA 句柄。此时 DMA 还没初始化，句柄是空的，绑定失败；后面 `HAL_TIM_PWM_Start_DMA()` 自然发不出数据。

这类问题的坑在于：CubeMX 生成的 `main()` 顺序是固定的，它不会替你判断依赖关系。

## 解法

在 `main.c` 里手动调换初始化顺序，**DMA 必须排在 TIM 前面**：

```c
MX_GPIO_Init();
MX_DMA_Init();     // 先 DMA
MX_TIM3_Init();    // 再 TIM
MX_I2C1_Init();
MX_USART1_UART_Init();
```

改完重新编译，灯带恢复。

## 排查路径

灯带不亮按这个顺序排除，别一上来就怀疑业务逻辑：

1. 供电和接线（见 SWD-0004）
2. 初始化顺序（本条）
3. DMA 数据宽度（SWD-0005）
4. DMA 互锁 / HAL_BUSY（SWD-0006）
5. PWM 占空比与周期是否算对

## 相关

- SWD-0005 DMA 数据宽度不匹配
- SWD-0006 HAL_TIM_PWM_Start_DMA 第二次失效
