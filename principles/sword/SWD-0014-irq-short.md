---
id: SWD-0014
kind: principle
title: 中断里只置标志位，运算放主循环
project: sword
category: 架构原则
tags: [架构, 中断, EXTI, 定时器, 实时性, 标志位]
platform: STM32F103C8T6
tool: 代码规范
severity: 必守
status: 生效中
date: 2026-11-05
source: Problems/问题记录.md
---

## 现象

在 EXTI 或 1 ms 定时器中断里做滤波、算姿态、刷灯带，结果串口丢字节、按键响应迟滞，偶尔整个系统像卡住。

## 原因

中断上下文里做耗时运算，会阻塞同优先级和低优先级中断；HAL 的延时、I2C 读写更是不能放进中断。

## 解法

中断只做最短的事：

```c
void HAL_GPIO_EXTI_Callback(uint16_t pin) {
    if (pin == KEY_PIN) g_key_pressed = 1;   // 只置标志
}
```

主循环里判断标志再处理：

```c
while (1) {
    if (g_key_pressed) { g_key_pressed = 0; App_HandleKey(); }
}
```

共享变量加 `volatile`；多字节数据要考虑原子性（关中断或用临界区）。

## 排查路径

系统"偶尔卡一下"、串口丢数据，先量中断服务函数的执行时间，超过几微秒就要怀疑。

## 相关

- SWD-0013 业务与硬件解耦
