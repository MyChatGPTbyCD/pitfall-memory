---
id: SWD-0009
kind: pitfall
title: 六轴数据全是负数（0xE864），不是坏了，是 int16
project: sword
category: 驱动-I2C传感器
tags: [MPU6050, int16, 负数, 原始数据, 补码]
platform: MPU6050 模块
tool: Keil MDK 5
severity: 提示
status: 已解决
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

Watch 窗口里 `ax`、`ay`、`az` 显示成 `0xE864` 这样的值，看着像乱码，或者全是负数。

## 原因

`int16_t` 是有符号 16 位，最高位为 1 就是负数。`0xE864` 的十进制是 **-6044**，这是加速度计原始 ADC 值，静止时本来就该在 0 附近小幅波动，晃动板子会剧烈变化。

不是错误，是补码表示。

## 解法

不用修。要做的是换算：

- 量程 ±2 g 时，灵敏度 16384 LSB/g
- 所以 `ax_g = ax / 16384.0f`

如果 Watch 里想看十进制而不是十六进制，右键变量改显示格式即可。

## 排查路径

数值"看起来不对"时，先确认量程设置和换算系数，再怀疑芯片。

## 相关

- SWD-0008 MPU6050 读不到
