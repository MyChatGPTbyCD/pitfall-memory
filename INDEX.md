# 踩坑记忆索引

> 由 `tools/mem.py index` 自动生成，最后更新 2026-11-08 22:58。共 14 条。
> 开工前读这份；遇到症状先 `python tools/mem.py search "关键词"`。

## 怎么用

```
python tools/mem.py brief --project sword      # 速读：标题 + 一句解法
python tools/mem.py search "灯不亮"            # 按症状搜
python tools/mem.py show SWD-0005               # 看全文
```

## sword（14 条）

| ID | 类型 | 分类 | 标题 | 严重度 | 标签 | 日期 |
|---|---|---|---|---|---|---|
| SWD-0002 | 坑 | 环境与工具链 | 时钟树报 No solution found，多半是 APB1 超频 | 严重 | CubeMX、时钟树、PLL、APB1 | 2026-11-05 |
| SWD-0003 | 坑 | 环境与工具链 | 引脚分给外设后，CubeMX 里改不了输出速度 | 一般 | CubeMX、GPIO、复用、输出速度 | 2026-11-05 |
| SWD-0010 | 坑 | 环境与工具链 | 一加 printf 就卡死在 BKPT 0xAB，勾上 MicroLIB | 致命 | Keil、printf、MicroLIB、BKPT | 2026-11-05 |
| SWD-0012 | 坑 | 环境与工具链 | ST-Link 找不到芯片 / 程序下不进去，先查 SWD 和 BOOT0 | 致命 | Keil、ST-Link、SWD、BOOT0 | 2026-11-05 |
| SWD-0001 | 坑 | 外设初始化 | DMA 没初始化就绑定 TIM，灯带不亮或程序卡死 | 致命 | CubeMX、HAL、DMA、TIM3 | 2026-11-05 |
| SWD-0004 | 坑 | 硬件接线 | WS2812B 模块引脚顺序和常规 5050 不一样，接反差点烧灯 | 致命 | WS2812B、接线、丝印、供电 | 2026-11-05 |
| SWD-0005 | 坑 | 驱动-WS2812B | DMA 内存宽度设成 Word，uint16 数组发出去全是乱码 | 致命 | WS2812B、DMA、数据宽度、uint16 | 2026-11-05 |
| SWD-0006 | 坑 | 驱动-WS2812B | 灯只亮一次，第二次 HAL_TIM_PWM_Start_DMA 就失效 | 致命 | WS2812B、HAL、DMA、HAL_BUSY | 2026-11-05 |
| SWD-0008 | 坑 | 驱动-I2C传感器 | MPU6050 读 WHO_AM_I 一直是 0x00，先换 SCL/SDA 再怀疑芯片 | 严重 | MPU6050、I2C、WHO_AM_I、0x74 | 2026-11-05 |
| SWD-0009 | 坑 | 驱动-I2C传感器 | 六轴数据全是负数（0xE864），不是坏了，是 int16 | 提示 | MPU6050、int16、负数、原始数据 | 2026-11-05 |
| SWD-0007 | 坑 | 调试 | 没有串口模块时，用 Keil Watch 窗口看变量（必须全局变量） | 提示 | Keil、Debug、Watch、全局变量 | 2026-11-05 |
| SWD-0011 | 坑 | 调试 | 改完代码进 Debug 报 error 35，Clean + Rebuild 就好 | 一般 | Keil、Debug、error35、断点 | 2026-11-05 |
| SWD-0013 | 原则 | 架构原则 | 业务逻辑不许碰 HAL 实例，硬件操作一律走 BSP 层 | 必守 | 架构、BSP、解耦、移植 | 2026-11-05 |
| SWD-0014 | 原则 | 架构原则 | 中断里只置标志位，运算放主循环 | 必守 | 架构、中断、EXTI、定时器 | 2026-11-05 |
