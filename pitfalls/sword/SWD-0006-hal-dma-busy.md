---
id: SWD-0006
kind: pitfall
title: 灯只亮一次，第二次 HAL_TIM_PWM_Start_DMA 就失效
project: sword
category: 驱动-WS2812B
tags: [WS2812B, HAL, DMA, HAL_BUSY, 互锁, 状态机]
platform: STM32F103C8T6
tool: Keil MDK 5
severity: 致命
status: 已解决
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

第一次刷新灯带正常，第二次调用 `HAL_TIM_PWM_Start_DMA()` 直接没反应，或者程序卡住。

## 原因

DMA 传输完成后，HAL 内部的 `gState` 状态机没有回到 READY，还停在 BUSY；再次 Start 时函数一进来就返回 `HAL_BUSY`，什么都没做。

这不是 bug，是 HAL 的设计：DMA 完成中断里只置了标志，没有把状态复位。

## 解法

每次发送前先强制停掉上一次的 DMA：

```c
HAL_TIM_PWM_Stop_DMA(&htim3, TIM_CHANNEL_1);
HAL_TIM_PWM_Start_DMA(&htim3, TIM_CHANNEL_1, pwmData, len);
```

如果 Stop 也返回 BUSY，说明上一次传输还没结束，要等 `HAL_TIM_PWM_PulseFinishedCallback` 里的完成标志，别硬启。

## 排查路径

"只能亮一次"这类现象，先查 HAL 返回值：把 `Start_DMA` 的返回值打出来，是 `HAL_OK` 还是 `HAL_BUSY`，一眼就能定位。

## 相关

- SWD-0005 DMA 数据宽度
- SWD-0001 DMA 初始化顺序
