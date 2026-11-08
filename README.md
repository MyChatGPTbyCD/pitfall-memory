# 踩坑记忆库 · pitfall memory

一个给「下一次开工的自己」看的记忆库。

每踩一个坑，写成一条结构化记录；下次开新会话、换项目、或者隔几个月回来，**先读索引再动手**。目标只有一个：同一个坑不踩第二次。

这个仓库是我自己在用的实例（内容以 STM32 光剑项目为主），格式和工具是通用的，你可以照搬到自己项目。

## 目录

```
_memory/
├── INDEX.md              总索引（自动生成）—— 开工前读这个
├── pitfalls/<项目>/      每个坑一个 md，带 ID（如 SWD-0005），方便引用和 diff
├── principles/<项目>/    项目级架构原则
├── templates/pitfall.md  新坑模板
└── tools/mem.py          建索引 / 检索 / 校验 / 新建草稿
```

## 一条记录长什么样

```markdown
---
id: SWD-0005
kind: pitfall
title: DMA 内存宽度设成 Word，uint16 数组发出去全是乱码
project: sword
category: 驱动-WS2812B
tags: [WS2812B, DMA, 数据宽度, uint16]
severity: 致命
status: 已解决
date: 2026-11-05
---

## 现象   ← 写当时的原话：报错文本、灯不亮、卡死
## 原因   ← 一句话说清机制
## 解法   ← 能给代码就给代码
## 排查路径 ← 下次按什么顺序查
## 相关   ← 关联条目的 ID
```

关键在「现象」：写你当时真正看到的字，别写"不工作"。检索就是靠这些词命中的。

## 用法

```bash
# 开工速读：标题 + 一句解法
python tools/mem.py brief --project sword

# 按症状搜
python tools/mem.py search "灯不亮"
python tools/mem.py search "I2C 读不到" --long

# 看全文
python tools/mem.py show SWD-0005

# 记新坑
python tools/mem.py new --project sword --title "一句话症状"
python tools/mem.py index

# 体检：缺字段、重复 ID、目录和 project 对不上
python tools/mem.py check
```

只需要 Python 3.9+，检索零依赖；`--semantic`（可选）要 numpy。

## 接到自己的项目上

在项目根目录的 `AGENTS.md`（或 `CLAUDE.md`）里写三行，让 AI 每次开工自己先读：

```markdown
## 开工前
1. 读 <路径>/_memory/INDEX.md
2. 遇到报错先 python <路径>/_memory/tools/mem.py search "症状关键词"
3. 解决新坑后写进 pitfalls/<项目>/ 并 mem.py index
```

不放 `AGENTS.md` 也行，自己记得"先读记忆"就够了——但人是会忘的，文件不会。

## 关于「向量记忆」

默认检索是 **TF-IDF + 字符 bigram 的余弦相似度**，经典向量空间模型：零依赖、离线、中文短句够用。

两个实话：

1. 条目少于两三百条时，**直接读 INDEX.md 比检索更快更准**。这个库现在 14 条，索引不到 3 KB。
2. TF-IDF 是字面匹配，不是语义匹配。搜"灯带颜色不对"能命中，是因为条目里写了这几个字；只写"灯不亮"就搜不到。

真要语义检索，加一层 embedding（需要 OpenAI 兼容接口，DeepSeek 官方没有 embedding）：

```bash
export MEM_EMBED_BASE=https://api.siliconflow.cn/v1
export MEM_EMBED_MODEL=BAAI/bge-m3
export MEM_EMBED_KEY=sk-xxx
python tools/mem.py embed
python tools/mem.py search "灯带颜色不对" --semantic
```

没有装向量数据库（Chroma/FAISS）是故意的：这个体量下，多一个依赖就多一个以后跑不起来的原因。

## 现在库里的内容

| 项目 | 路径（我的本机） | 条数 |
|---|---|---|
| `sword` | `D:\My_Project\Sword` | 14（12 个坑 + 2 条架构原则） |

覆盖：CubeMX/PLL、DMA 初始化顺序与宽度、WS2812B 接线、HAL_BUSY、MPU6050 的 I2C 与 WHO_AM_I、Keil 的 MicroLIB / error 35 / ST-Link、BSP 分层与中断原则。

## License

MIT，见 [LICENSE](LICENSE)。
