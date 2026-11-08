---
id: SWD-0008
kind: pitfall
title: MPU6050 读 WHO_AM_I 一直是 0x00，先换 SCL/SDA 再怀疑芯片
project: sword
category: 驱动-I2C传感器
tags: [MPU6050, I2C, WHO_AM_I, 0x74, 接线, 上拉]
platform: MPU6050 模块（兼容片）
tool: Keil MDK 5
severity: 严重
status: 已解决
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

程序能跑，但 `check`（WHO_AM_I）读出来一直是 `0x00`，六轴数据全 0。

## 原因

按可能性排序：

1. SCL / SDA 接反（很多模块丝印和实物不符）
2. 没共地，或者 VCC 不是 3.3 V
3. 总线上没有上拉电阻
4. 模块本身是坏的

## 解法

1. 断电，把 SCL 和 SDA 两根杜邦线互换——本次就是这一步解决的。
2. 确认 VCC = 3.3 V，GND 严格共地。
3. 读到的值**不是 0x00 也不是 0xFF** 就说明 I2C 通了。本次模块返回的是 **0x74**，不是标准 6050 的 0x68。
4. 还不行就在 SDA/SCL 上外接 4.7 kΩ 上拉到 3.3 V。

**注意**：0x74 说明这是兼容/克隆片，寄存器大体兼容，但 DMP 固件和部分量程配置不一定通用，别直接照抄正品 MPU6050 的 DMP 初始化代码。

## 排查路径

I2C 不通就三步：换线 → 量电压和地 → 加上拉。三步都过了还是 0x00，换模块。

## 相关

- SWD-0009 数据是负数
- SWD-0007 没有串口怎么看数据
