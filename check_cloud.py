#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端版网关的真实对话结果"""
import json

p = '/sdcard/Download/cloud_t1.json'
try:
    d = json.load(open(p))
except Exception as e:
    print("读取失败:", e)
    print(open(p).read()[:500])
    raise SystemExit

if 'error' in d:
    print("上游错误:", json.dumps(d['error'], ensure_ascii=False)[:400])
    raise SystemExit

ch = d['choices'][0]
msg = ch.get('message', {})
c = msg.get('content') or ''
u = d.get('usage', {})

print("finish_reason        :", ch.get('finish_reason'))
print("reasoning_content 剥离:", 'reasoning_content' not in msg)
print("客户端恶意system被丢 :", ('抱歉' not in c and '拒绝' not in c))
print("completion_tokens    :", u.get('completion_tokens'))
print("正文长度             :", len(c))
print("--- 正文前 400 字 ---")
print(c[:400])