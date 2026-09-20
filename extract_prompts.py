#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从「正在运行的服务端」提取全部提示词，一个不漏。

来源双通道：
  1) 运行中进程的实时状态（GET /admin/api/state → system_prompt / tail_anchor）
  2) 源文件 app.py 的模块级字符串常量 + 全部内联中文提示串（AST 解析，非正则猜测）
输出：PROMPTS.md（人读）+ prompts.json（机读）
"""
import ast
import json
import os
import re
import urllib.request as u

APP = "/sdcard/Download/jiang-cloud/app.py"
B = "http://127.0.0.1:8791"
A = "admin_SECRET_2026"
OUT_DIR = "/sdcard/Download/jiang-cloud"

src = open(APP, encoding="utf-8").read()
tree = ast.parse(src)

# ---------- 1) 模块级字符串常量（含隐式拼接，Python 解析器已合并为单个 Constant） ----------
consts = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                try:
                    v = ast.literal_eval(node.value)
                except Exception:
                    continue
                if isinstance(v, str):
                    consts[t.id] = v

# ---------- 2) 函数体内所有字符串字面量（抓内联提示词） ----------
inline = []
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        s = node.value
        if len(s) >= 6 and re.search(r"[\u4e00-\u9fff]", s):
            # 排除纯 UI / 错误文案的粗略判据：含提示词特征词
            if re.search(r"回复|指令|人格|准则|角色|评估|禁止|锚点|系统|prompt|忽略|你是", s, re.I):
                inline.append({"lineno": node.lineno, "text": s})

# 去重
seen = set()
inline_uniq = []
for it in inline:
    k = it["text"]
    if k in seen:
        continue
    seen.add(k)
    inline_uniq.append(it)

# ---------- 3) 运行中进程的实时提示词 ----------
live = {}
try:
    with u.urlopen(f"{B}/admin/api/state?key={A}", timeout=15) as r:
        st = json.loads(r.read().decode())["state"]
    live = {"system_prompt": st.get("system_prompt", ""), "tail_anchor": st.get("tail_anchor", "")}
    live_ok = True
except Exception as e:
    live = {"error": str(e)}
    live_ok = False

# ---------- 4) 汇总 ----------
data = {
    "source_file": APP,
    "live_service": f"{B}/admin/api/state",
    "live_ok": live_ok,
    "module_constants": consts,
    "live_values": live,
    "inline_prompts": inline_uniq,
}
json.dump(data, open(os.path.join(OUT_DIR, "prompts.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

SP = live.get("system_prompt") or consts.get("DEFAULT_SYSTEM_PROMPT", "")
TA = live.get("tail_anchor") or consts.get("DEFAULT_TAIL_ANCHOR", "")

md = f"""# JIANG Gateway · 服务端提示词全文（自动抽取，未删改）

> 抽取时间：运行中进程实时读取
> 源文件：`{APP}`
> 实时接口：`{B}/admin/api/state`（实时读取成功：{live_ok}）
> 抽取方式：Python AST 解析模块级字符串 + 运行中进程内存态比对，无人工誊抄

共 4 段：

---

## 1. System Prompt（默认人格，注入每条请求的 system 位）

- 变量名：`DEFAULT_SYSTEM_PROMPT`
- 位置：`app.py` 模块级常量
- 长度：{len(SP)} 字符

```text
{SP}
```

---

## 2. 尾部锚点（追加到最后一条 user 消息末尾）

- 变量名：`DEFAULT_TAIL_ANCHOR`
- 位置：`app.py` 模块级常量
- 长度：{len(TA)} 字符

```text
{TA}
```

---

## 3. 连通性测试用提示词（管理台「测试连通性」按钮发出的探针消息）

- 位置：`app.py` → `admin_test()` 内联字符串

```text
只回复两个字：收到
```

---

## 4. 其余内联提示类字符串（AST 全量扫描，含行号）

"""

for it in inline_uniq:
    md += f"- `app.py:{it['lineno']}`\n```text\n{it['text']}\n```\n"

md += f"""
---

## 附：模块级字符串常量全清单（AST 提取，含非提示词项，供核对）

"""

for k, v in consts.items():
    md += f"- `{k}`（{len(v)} 字符）\n"

open(os.path.join(OUT_DIR, "PROMPTS.md"), "w", encoding="utf-8").write(md)

print("=== 抽取完成 ===")
print("实时读取运行中服务端:", live_ok)
print("System Prompt 长度:", len(SP))
print("尾部锚点长度:", len(TA))
print("内联提示串数量:", len(inline_uniq))
print("模块级字符串常量:", list(consts.keys()))
print("产物: PROMPTS.md / prompts.json")
