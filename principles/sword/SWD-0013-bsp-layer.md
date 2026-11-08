---
id: SWD-0013
kind: principle
title: 业务逻辑不许碰 HAL 实例，硬件操作一律走 BSP 层
project: sword
category: 架构原则
tags: [架构, BSP, 解耦, 移植, G030, 分层]
platform: STM32F103C8T6 -> STM32G030F6P6
tool: 代码规范
severity: 必守
status: 生效中
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

前期图快，状态机里直接写 `HAL_GPIO_WritePin(GPIOA, GPIO_PIN_6, ...)`、直接引用 `htim3`。等要换 G030 时，发现业务代码和 F1 的引脚、外设、HAL 版本全绑死了。

## 原因

没有分层。硬件细节泄漏到业务层，换芯片等于重写。

## 解法

业务层只调用 BSP 提供的语义接口，不出现任何 HAL 符号、引脚号、外设实例名：

```c
// 业务层
BSP_LED_SetColor(i, r, g, b);
BSP_IMU_Read(&accel, &gyro);

// BSP 层内部才允许出现
HAL_TIM_PWM_Start_DMA(&htim3, ...);
```

判断标准：把 `bsp_f103.c` 整个换掉，业务层一行都不用改，才算分对了。

## 排查路径

代码评审时搜 `HAL_`、`htim`、`GPIO_PIN` 出现在 `app/` 或 `logic/` 目录里，就是漏了。

## 相关

- SWD-0014 中断里不做耗时操作
