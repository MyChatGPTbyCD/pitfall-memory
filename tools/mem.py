#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_memory 记忆库工具

  python mem.py index                    重建 INDEX.md
  python mem.py brief [--project sword]  开工前速读（标题 + 一句解法）
  python mem.py search "灯不亮"          检索（默认 TF-IDF 向量余弦）
  python mem.py show SWD-0001            看条目全文
  python mem.py check                    校验格式 / 重复 ID
  python mem.py new --project sword --title "一句话症状"   新建草稿
  python mem.py embed  --base URL --model NAME            生成神经向量（可选）
  python mem.py search "..." --semantic                   语义检索（需先 embed）

默认检索是字符 bigram 的 TF-IDF 余弦：经典向量空间模型，零依赖、离线可用。
配置 embedding 服务后可走语义检索；没配也不影响主流程。
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIT_DIR = ROOT / "pitfalls"
PRIN_DIR = ROOT / "principles"
INDEX = ROOT / "INDEX.md"
TEMPLATE = ROOT / "templates" / "pitfall.md"
VEC = ROOT / "tools" / "vectors.npz"
VEC_META = ROOT / "tools" / "vectors.json"

REQUIRED = ["id", "kind", "title", "project", "category", "tags", "severity", "status", "date"]
KINDS = ("pitfall", "principle")
CAT_ORDER = ["环境与工具链", "外设初始化", "硬件接线", "驱动-WS2812B",
             "驱动-I2C传感器", "调试", "架构原则"]
K1, B = 1.2, 0.75
CJK = r"[\u4e00-\u9fff]"


# ---------------------------------------------------------------- 解析

def norm(s: str) -> str:
    return str(s or "").lower()


def as_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in str(v).split(",") if x.strip()]


def _scalar(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_meta(block: str) -> dict:
    meta: dict = {}
    for line in block.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        if not key:
            continue
        if val.startswith("[") and val.endswith("]"):
            meta[key] = [_scalar(x) for x in val[1:-1].split(",") if x.strip()]
        else:
            meta[key] = _scalar(val)
    return meta


def parse_doc(path: Path):
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    m = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    return parse_meta(m.group(1)), m.group(2)


def load_docs() -> list[dict]:
    docs = []
    for base, default_kind in ((PIT_DIR, "pitfall"), (PRIN_DIR, "principle")):
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.md")):
            meta, body = parse_doc(p)
            if not meta or "id" not in meta:
                continue
            meta.setdefault("kind", default_kind)
            meta["_path"] = p
            meta["_body"] = body
            meta["project"] = str(meta.get("project", "general")).strip()
            docs.append(meta)
    docs.sort(key=lambda d: str(d.get("id", "")))
    return docs


# ---------------------------------------------------------------- 分词 / 检索

def tokenize(s: str) -> list[str]:
    out = []
    for run in re.findall(r"[a-z0-9][a-z0-9_+#.\-]*|" + CJK + "+", norm(s)):
        if re.match(CJK, run[0]):
            if len(run) == 1:
                out.append(run)
            else:
                out.extend(run[i:i + 2] for i in range(len(run) - 1))
        else:
            t = run.strip(".-")
            if t:
                out.append(t)
    return out


def doc_terms(meta: dict) -> dict:
    tf: dict[str, float] = {}

    def add(text: str, w: float) -> None:
        for t in tokenize(text):
            tf[t] = tf.get(t, 0.0) + w

    add(meta.get("title", ""), 3)
    add(" ".join(as_list(meta.get("tags"))), 3)
    add(meta.get("category", ""), 2)
    add(meta.get("platform", ""), 1)
    add(meta.get("tool", ""), 1)
    add(_main_body(meta.get("_body", "")), 1)
    return tf


def _main_body(body: str) -> str:
    """去掉「相关」小节：那里只有链接，会把检索带偏。"""
    return re.sub(r"(?ms)^##\s*相关\s*$.*?(?=^##\s|\Z)", "", body)


def cjk_runs(s: str) -> list[str]:
    return re.findall(CJK + "+", norm(s))


class Searcher:
    def __init__(self, docs: list[dict]):
        self.docs = docs
        self.tfs = [doc_terms(d) for d in docs]
        self.lens = [sum(tf.values()) for tf in self.tfs]
        self.avg = (sum(self.lens) / len(self.lens)) if self.lens else 1.0
        df: dict[str, int] = {}
        for tf in self.tfs:
            for t in tf:
                df[t] = df.get(t, 0) + 1
        n = len(docs) or 1
        self.idf = {t: math.log((n - c + 0.5) / (c + 0.5) + 1) for t, c in df.items()}

    def rank(self, query: str) -> list[tuple[int, float]]:
        q_tokens = sorted(set(tokenize(query)))
        runs = [r for r in cjk_runs(query) if len(r) >= 2]
        scored = []
        for i, d in enumerate(self.docs):
            tf = self.tfs[i]
            dl = self.lens[i] or 1
            score = 0.0
            for t in q_tokens:
                f = tf.get(t, 0.0)
                if not f:
                    continue
                score += self.idf.get(t, 0.0) * (f * (K1 + 1)) / (
                    f + K1 * (1 - B + B * dl / self.avg)
                )
            if score <= 0:
                continue
            title = norm(d.get("title", ""))
            tags = norm(" ".join(as_list(d.get("tags"))))
            body = norm(_main_body(d.get("_body", "")))
            for r in runs:
                if r in title:
                    score += 2.0
                if r in tags:
                    score += 1.5
                if r in body:
                    score += 0.4
            scored.append((i, score))
        scored.sort(key=lambda x: -x[1])
        return scored


# ---------------------------------------------------------------- 输出辅助

def clip(text: str, width: int = 80) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= width else text[: width - 1] + "…"


def section_lines(body: str, heading: str) -> list[str]:
    out, inside = [], False
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("#"):
            if inside:
                break
            if heading in s:
                inside = True
            continue
        if inside:
            out.append(s)
    return out


def section_line(body: str, heading: str, width: int = 90) -> str:
    lines, fence = [], False
    for line in section_lines(body, heading):
        if line.startswith("```"):
            fence = not fence
            continue
        if fence or not line:
            continue
        lines.append(line)
    for s in lines:
        t = re.sub(r"^\d+[.、)]\s*", "", s)
        t = re.sub(r"^[-*]\s*", "", t)
        if t.endswith(("：", ":")):
            if len(t) >= 8:  # 「必须按丝印接。顺序如下：」这种截断后仍有信息
                return clip(t.rstrip("：:") + "…", width)
            continue  # 「两种选择：」这类引导句，跳过看下一行
        if len(t) < 6:
            continue
        return clip(t, width)
    return ""


def snippet(meta: dict, query: str, width: int = 70) -> str:
    body = meta.get("_body", "")
    runs = [r for r in cjk_runs(query) if len(r) >= 2]
    symptom = [l.strip(" -*`") for l in section_lines(body, "现象")
               if l.strip() and not l.strip().startswith(("```", "|"))]
    for line in symptom:
        if any(r in line for r in runs):
            return clip(line, width)
    if symptom:
        return clip(symptom[0], width)
    others = [l.strip(" -*`") for l in body.splitlines()
              if l.strip() and not l.lstrip().startswith("#")]
    for line in others:
        if any(r in line for r in runs):
            return clip(line, width)
    return clip(others[0], width) if others else ""


def cat_key(d: dict):
    cat = str(d.get("category", ""))
    return (CAT_ORDER.index(cat) if cat in CAT_ORDER else len(CAT_ORDER), str(d.get("id", "")))


# ---------------------------------------------------------------- 筛选

def filter_docs(docs: list[dict], args) -> list[dict]:
    out = []
    for d in docs:
        if args.project and str(d.get("project", "")).lower() != args.project.lower():
            continue
        if getattr(args, "kind", None) and str(d.get("kind")) != args.kind:
            continue
        if getattr(args, "category", None) and str(d.get("category")) != args.category:
            continue
        tags = [t.lower() for t in as_list(d.get("tags"))]
        if getattr(args, "tag", None) and not all(t.lower() in tags for t in args.tag):
            continue
        out.append(d)
    return out


# ---------------------------------------------------------------- 命令

def cmd_index(args) -> None:
    docs = load_docs()
    projects: dict[str, list[dict]] = {}
    for d in docs:
        projects.setdefault(str(d.get("project")), []).append(d)

    now = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 踩坑记忆索引",
        "",
        f"> 由 `tools/mem.py index` 自动生成，最后更新 {now}。共 {len(docs)} 条。",
        "> 开工前读这份；遇到症状先 `python tools/mem.py search \"关键词\"`。",
        "",
        "## 怎么用",
        "",
        "```",
        "python tools/mem.py brief --project sword      # 速读：标题 + 一句解法",
        "python tools/mem.py search \"灯不亮\"            # 按症状搜",
        "python tools/mem.py show SWD-0005               # 看全文",
        "```",
        "",
    ]
    for proj in sorted(projects):
        rows = sorted(projects[proj], key=cat_key)
        lines.append(f"## {proj}（{len(rows)} 条）")
        lines.append("")
        lines.append("| ID | 类型 | 分类 | 标题 | 严重度 | 标签 | 日期 |")
        lines.append("|---|---|---|---|---|---|---|")
        for d in rows:
            kind = "坑" if d.get("kind") == "pitfall" else "原则"
            tags = "、".join(as_list(d.get("tags"))[:4])
            title = str(d.get("title", "")).replace("|", "\\|")
            lines.append(
                f"| {d.get('id')} | {kind} | {d.get('category', '')} | {title} | "
                f"{d.get('severity', '')} | {tags} | {d.get('date', '')} |"
            )
        lines.append("")
    INDEX.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"已生成 {INDEX}（{len(docs)} 条，项目：{', '.join(sorted(projects))}）")


def cmd_brief(args) -> None:
    docs = filter_docs(load_docs(), args)
    if not docs:
        print("没有匹配的条目。先 mem.py index 看看库是不是空的。")
        return
    newest = max((d["_path"].stat().st_mtime for d in docs), default=0)
    if INDEX.exists() and INDEX.stat().st_mtime < newest:
        print("提醒：INDEX.md 比条目旧，建议先 python mem.py index\n")

    projects: dict[str, list[dict]] = {}
    for d in docs:
        projects.setdefault(str(d.get("project")), []).append(d)
    for proj in sorted(projects):
        rows = sorted(projects[proj], key=cat_key)
        print(f"[{proj}] 共 {len(rows)} 条")
        for d in rows:
            sev = d.get("severity", "")
            print(f"  {d.get('id')}  [{d.get('category')}/{sev}]  {d.get('title')}")
            sol = section_line(d.get("_body", ""), "解法")
            if sol:
                print(f"        -> {sol}")
        print()


def cmd_search(args) -> None:
    docs = filter_docs(load_docs(), args)
    if not docs:
        print("没有匹配的条目。")
        return
    if args.semantic:
        ranked = semantic_rank(docs, args)
    else:
        ranked = Searcher(docs).rank(args.query)
    if not ranked:
        print("没搜到。换个说法试试，比如只保留症状里的名词。")
        return
    print(f"命中 {len(ranked)} 条，显示前 {min(args.limit, len(ranked))} 条：\n")
    for n, (idx, score) in enumerate(ranked[: args.limit], 1):
        d = docs[idx]
        rel = d["_path"].relative_to(ROOT).as_posix()
        print(f"{n}. {d.get('id')}  [{d.get('severity', '')}]  {d.get('title')}   ({score:.1f})")
        print(f"   {rel}")
        if args.long:
            print(f"   现象：{snippet(d, args.query)}")
            sol = section_line(d.get("_body", ""), "解法")
            if sol:
                print(f"   解法：{sol}")
        print()


def cmd_show(args) -> None:
    key = args.id.strip()
    docs = load_docs()
    hit = [d for d in docs if str(d.get("id", "")).upper() == key.upper()]
    if not hit:
        hit = [d for d in docs if key.upper() in str(d.get("id", "")).upper()]
    if not hit:
        sys.exit(f"找不到条目 {key}")
    d = hit[0]
    print(f"{d.get('id')}  {d.get('title')}")
    print(f"{d.get('project')} / {d.get('category')} / {d.get('severity')} / {d.get('date')}")
    print(f"标签：{'、'.join(as_list(d.get('tags')))}")
    print(f"文件：{d['_path']}")
    print("-" * 60)
    print(d.get("_body", "").strip())


def cmd_check(args) -> None:
    docs = load_docs()
    errors, seen = [], {}
    for d in docs:
        p = d["_path"]
        rel = p.relative_to(ROOT).as_posix()
        for k in REQUIRED:
            if k not in d or d[k] == "":
                errors.append(f"{rel}: 缺字段 {k}")
        did = str(d.get("id", ""))
        if not re.fullmatch(r"[A-Z]{2,4}-\d{4}", did):
            errors.append(f"{rel}: id 格式不对（应如 SWD-0001）")
        if did in seen:
            errors.append(f"{rel}: id 与 {seen[did]} 重复")
        seen[did] = rel
        if d.get("kind") not in KINDS:
            errors.append(f"{rel}: kind 应为 {'/'.join(KINDS)}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(d.get("date", ""))):
            errors.append(f"{rel}: date 应为 YYYY-MM-DD")
        if p.parent.name != str(d.get("project")):
            errors.append(f"{rel}: 所在目录与 project={d.get('project')} 不一致")
        if not p.name.upper().startswith(did.upper()):
            errors.append(f"{rel}: 文件名应以 {did} 开头")
        if "## 解法" not in d.get("_body", ""):
            errors.append(f"{rel}: 缺少 ## 解法 段")
    if errors:
        print(f"发现 {len(errors)} 个问题：")
        for e in errors:
            print("  - " + e)
        sys.exit(1)
    print(f"OK：{len(docs)} 条，格式与 id 都正常。")


def cmd_new(args) -> None:
    proj = args.project
    docs = [d for d in load_docs() if str(d.get("project")) == proj]
    prefix = str(docs[0].get("id", "GEN-0000")).split("-")[0] if docs else proj[:3].upper()
    nums = [int(str(d["id"]).split("-")[1]) for d in docs
            if re.fullmatch(r"[A-Z]{2,4}-\d{4}", str(d.get("id", "")))]
    nid = f"{prefix}-{(max(nums) + 1) if nums else 1:04d}"
    slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-") or "entry"
    slug = slug[:40]
    target = PIT_DIR / proj / f"{nid}-{slug}.md"
    target.parent.mkdir(parents=True, exist_ok=True)

    tpl = TEMPLATE.read_text(encoding="utf-8")
    body = (tpl.replace("{{id}}", nid)
               .replace("{{title}}", args.title)
               .replace("{{project}}", proj)
               .replace("{{date}}", __import__("datetime").date.today().isoformat()))
    target.write_text(body, encoding="utf-8")
    print(f"已创建 {target}")
    print("填完 现象 / 原因 / 解法 后运行：python tools/mem.py index")


# ---------------------------------------------------------------- 可选：神经向量

def embed_texts(texts: list[str], args) -> list[list[float]]:
    base = (args.base or os.environ.get("MEM_EMBED_BASE", "")).rstrip("/")
    model = args.model or os.environ.get("MEM_EMBED_MODEL", "")
    if not base or not model:
        sys.exit("需要 --base 和 --model（或环境变量 MEM_EMBED_BASE / MEM_EMBED_MODEL）")
    url = base if base.endswith("/embeddings") else base + "/embeddings"
    key = args.key or os.environ.get(args.key_env, "")
    payload = json.dumps({"model": model, "input": texts}).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"embedding 请求失败：{exc}")
    rows = data.get("data")
    if not rows:
        sys.exit(f"返回里没有 data：{str(data)[:200]}")
    rows.sort(key=lambda r: r.get("index", 0))
    return [r["embedding"] for r in rows]


def cmd_embed(args) -> None:
    try:
        import numpy as np
    except ImportError:
        sys.exit("需要 numpy：请用 DSH 自带 python 运行")
    docs = load_docs()
    texts = [f"{d.get('title', '')}\n{' '.join(as_list(d.get('tags')))}\n{d.get('_body', '')}"
             for d in docs]
    vecs = embed_texts(texts, args)
    np.savez(VEC,
             ids=np.array([d["id"] for d in docs]),
             mtimes=np.array([d["_path"].stat().st_mtime for d in docs]),
             vecs=np.asarray(vecs, dtype="float32"))
    VEC_META.write_text(json.dumps({
        "model": args.model or os.environ.get("MEM_EMBED_MODEL", ""),
        "count": len(docs), "dim": len(vecs[0]),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 {len(docs)} 条向量 -> {VEC}")


def semantic_rank(docs: list[dict], args) -> list[tuple[int, float]]:
    try:
        import numpy as np
    except ImportError:
        sys.exit("需要 numpy：请用 DSH 自带 python 运行")
    if not VEC.exists():
        sys.exit("还没有向量文件，先运行：python tools/mem.py embed --base ... --model ...")
    z = np.load(VEC, allow_pickle=True)
    ids = [str(x) for x in z["ids"]]
    mat_all = z["vecs"].astype("float32")
    pos = {did: i for i, did in enumerate(ids)}
    pairs = [(i, pos[str(d["id"])]) for i, d in enumerate(docs) if str(d["id"]) in pos]
    if not pairs:
        return []
    qv = np.asarray(embed_texts([args.query], args), dtype="float32")[0]
    qn = np.linalg.norm(qv) or 1.0
    out = []
    for i, j in pairs:
        v = mat_all[j]
        out.append((i, float(v @ qv / ((np.linalg.norm(v) or 1.0) * qn))))
    out.sort(key=lambda x: -x[1])
    return out


# ---------------------------------------------------------------- CLI

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="_memory 踩坑记忆库")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("index", help="重建 INDEX.md").set_defaults(func=cmd_index)

    p = sub.add_parser("brief", help="开工前速读")
    p.add_argument("--project")
    p.add_argument("--kind", choices=KINDS)
    p.set_defaults(func=cmd_brief)

    p = sub.add_parser("search", help="检索")
    p.add_argument("query")
    p.add_argument("--project")
    p.add_argument("--kind", choices=KINDS)
    p.add_argument("--category")
    p.add_argument("--tag", action="append")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--long", action="store_true", help="附带现象/解法摘要")
    p.add_argument("--semantic", action="store_true", help="用 embedding 语义检索")
    p.add_argument("--base")
    p.add_argument("--model")
    p.add_argument("--key")
    p.add_argument("--key-env", default="MEM_EMBED_KEY")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("show", help="看条目全文")
    p.add_argument("id")
    p.set_defaults(func=cmd_show)

    sub.add_parser("check", help="校验").set_defaults(func=cmd_check)

    p = sub.add_parser("new", help="新建草稿")
    p.add_argument("--project", required=True)
    p.add_argument("--title", required=True)
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("embed", help="生成神经向量")
    p.add_argument("--base")
    p.add_argument("--model")
    p.add_argument("--key")
    p.add_argument("--key-env", default="MEM_EMBED_KEY")
    p.set_defaults(func=cmd_embed)
    return ap


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
