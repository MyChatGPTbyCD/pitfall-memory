---
id: GEN-0001
kind: pitfall
title: 推 .github/workflows 被拒：OAuth App 缺 workflow scope
project: general
category: 环境与工具链
tags: [GitHub, gh, OAuth, 权限, CI, workflow-scope]
platform: GitHub
tool: gh CLI / git
severity: 一般
status: 已解决
date: 2026-11-08
source: 2026-11-08 建 pitfall-memory 仓库时遇到
---

## 现象

`git push` 一个新增的 `.github/workflows/validate.yml`，被远端拒绝：

```
! [remote rejected] main -> main (refusing to allow an OAuth App to
  create or update workflow `.github/workflows/validate.yml` without `workflow` scope)
```

但同一个仓库推普通代码完全正常。

## 原因

gh CLI 登录拿到的是 OAuth App token，GitHub 对「写 workflow 文件」额外要求 `workflow` scope。
而 `gh auth login` 默认只申请 `repo`、`read:org`、`gist`，所以代码能推、CI 文件不能推。

容易误判成：分支保护、仓库权限、Actions 没开——都不是。

## 解法

给 token 补 scope，然后重新 push：

```bash
gh auth refresh -h github.com -s workflow
```

再 `git push` 即可。验证：

```bash
gh auth status      # Token scopes 里要出现 'workflow'
```

如果走的是自己的 device flow / PAT，申请时把 `workflow` 一并写上。

## 排查路径

看到 `without 'workflow' scope` 这行字，直接补 scope，别去查分支保护和 Actions 开关。

## 相关

- GEN-0001 是这条记忆库自己的第一个"通用坑"
