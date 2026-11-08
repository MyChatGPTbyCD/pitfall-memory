---
id: SWD-0003
kind: pitfall
title: 引脚分给外设后，CubeMX 里改不了输出速度
project: sword
category: 环境与工具链
tags: [CubeMX, GPIO, 复用, 输出速度, TIM3, PA6]
platform: STM32F103C8T6
tool: STM32CubeMX
severity: 一般
status: 已解决
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

TIM3_CH1 对应 PA6，在 GPIO Settings 里 Maximum output speed 是灰的，改不动。

## 原因

引脚被分配给外设（Alternate Function）时，CubeMX 会锁住速度选项，改由外设的 MSP 初始化决定。

## 解法

两种选择：

1. 接受默认 Low。能跑，但 PWM 边沿不够陡，长灯带或高时序要求下可能出错。
2. 生成代码后，在 `stm32f1xx_hal_msp.c` 的 `HAL_TIM_PWM_MspInit` 里手动改：

```c
GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
```

注意：手动改 MSP 后，CubeMX 重新生成会覆盖，改完记得重新加，或者把它挪到用户代码区。

## 排查路径

波形边沿软、灯带末端颜色不对时，先量 PA6 上升沿，再回来查这个速度设置。

## 相关

- SWD-0005 DMA 数据宽度
