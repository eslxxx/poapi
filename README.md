# JIANG Gateway · 云端部署

强制人格注入的 OpenAI 兼容代理。可部署到任意支持 Python/Docker 的免费平台。

---

## 一、平台对比（2025 实测口径）

| 平台 | 免费额度 | 休眠策略 | 需要信用卡 | 适合度 |
|---|---|---|---|---|
| **Render** | 750 小时/月 | 15 分钟无请求休眠，冷启动 30–60s | 不需要 | 首选 |
| **Koyeb** | 1 个 Web 服务 | 无流量时休眠 | 不需要 | 推荐 |
| **Hugging Face Spaces** | 免费 CPU 空间 | 48h 无活动休眠 | 不需要 | 推荐 |
| **Railway** | $5 试用额度 | 额度用完停服 | 需验证 | 一般 |
| **Fly.io** | 3 台共享 CPU 小机 | 可配 auto-stop | 需验证 | 一般 |
| **Vercel** | 免费 Serverless | 单次执行 10s 上限 | 不需要 | 排除 |
| **Cloudflare Workers** | 10 万请求/天 | 无休眠 | 不需要 | 需改写成 JS |

**关键限制**：LLM 推理一次经常要 30–120 秒。**Vercel 免费版 10 秒超时，直接排除。** Render/Koyeb/HF 没这个问题。

**休眠怎么办**：用 cron-job.org（免费）每 10 分钟打一次 `/health` 保持常驻；或接受冷启动。

---

## 二、文件清单

```
jiang-cloud/
├── app.py              # 主服务（环境变量驱动、带鉴权）
├── requirements.txt    # 依赖
├── Dockerfile          # 通用容器部署
├── Procfile            # Heroku/Railway 风格
├── render.yaml         # Render 蓝图（一键部署）
├── .gitignore
├── test_local.sh       # 本地验证脚本
└── check_cloud.py      # 结果检查
```

---

## 三、部署方式

### 方式 A：Render（推荐，全程网页点选）

1. 把 `jiang-cloud/` 推到一个 GitHub 仓库
2. 打开 https://dashboard.render.com → **New** → **Web Service**
3. 连上仓库，Render 自动识别 `render.yaml`
4. 环境变量：

| Key | Value |
|---|---|
| `UPSTREAM_API_KEY` | 你的上游密钥 |
| `GATEWAY_TOKEN` | 自己定一个随机串（**必填，否则公网裸奔**） |
| `UPSTREAM_BASE` | `https://cli.999554.xyz/v1` |
| `UPSTREAM_MODEL` | `deepseek-v4.1-flash` |

5. Deploy，等 2–3 分钟，拿到 `https://jiang-gateway.onrender.com`

### 方式 B：Hugging Face Spaces

1. https://huggingface.co/new-space
2. SDK 选 **Docker** → Blank
3. 上传 `app.py` + `Dockerfile`（把 `EXPOSE` / `CMD` 端口改成 `7860`）
4. Settings → **Repository secrets**：

```
UPSTREAM_API_KEY = sk-xxxx
GATEWAY_TOKEN    = 你的随机串
```

5. 地址形如 `https://<用户名>-<空间名>.hf.space`

### 方式 C：Koyeb

1. https://app.koyeb.com → **Create Service** → **GitHub**
2. 构建方式选 **Dockerfile**
3. 端口填 `8787`，环境变量同上
4. 地址形如 `https://xxx.koyeb.app`

### 方式 D：本机 Docker 自测

```bash
cd jiang-cloud
docker build -t jiang-gateway .
docker run -d --name jiang-gw -p 8787:8787 \
  -e UPSTREAM_API_KEY="sk-xxxx" \
  -e GATEWAY_TOKEN="my_secret_token" \
  -e UPSTREAM_BASE="https://cli.999554.xyz/v1" \
  jiang-gateway
```

---

## 四、客户端接入

```
Base URL : https://<你的域名>/v1
API Key  : <你设的 GATEWAY_TOKEN>
Model    : deepseek-v4.1-flash
```

验证命令：

```bash
# 1. 健康检查（无需 token）
curl https://<你的域名>/health

# 2. 真实调用
curl https://<你的域名>/v1/chat/completions \
  -H "Authorization: Bearer <你的GATEWAY_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4.1-flash","messages":[{"role":"user","content":"你好"}],"max_tokens":500}'

# 3. 鉴权是否生效（应 401）
curl https://<你的域名>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hi"}]}'
```

---

## 五、环境变量全表

| 变量 | 必填 | 默认 | 说明 |
|---|---|---|---|
| `UPSTREAM_API_KEY` | 是 | — | 上游密钥 |
| `UPSTREAM_BASE` | | `https://cli.999554.xyz/v1` | 上游地址 |
| `UPSTREAM_MODEL` | | `deepseek-v4.1-flash` | 模型名 |
| `GATEWAY_TOKEN` | 强烈建议 | 空（不鉴权） | 客户端 Bearer token |
| `SPOOF_USER_AGENT` | | `python-httpx/0.28.1` | 绕过上游 CF 1010 |
| `JIANG_SYSTEM_PROMPT` | | 内置 v3 人格 | 覆盖人格文本 |
| `JIANG_TAIL_ANCHOR` | | 内置锚点 | 覆盖尾部强注 |
| `PORT` | | `8787` | 平台自动注入 |

---

## 六、与本地版的差异

| 项 | 本地版 | 云端版 |
|---|---|---|
| 密钥 | 硬编码 | 环境变量 |
| 端口 | 8787 固定 | `$PORT` |
| 鉴权 | 无 | Bearer Token |
| CORS | 无 | 全开 |
| 流式 | 支持 | 支持（含错误处理） |
| 健康检查 | 简单 | 含统计与运行时长 |

**重要**：上了公网一定要设 `GATEWAY_TOKEN`。否则任何人扫到你的域名，都能用你的上游额度。

---

## 七、常见问题

**Q: 部署后 500，日志说 `UPSTREAM_API_KEY not set`**
环境变量没生效。检查是否填在正确的服务下，改完要 **Manual Deploy** 重新部署。

**Q: 返回 403 / error code 1010**
上游 CF 校验。确认 `SPOOF_USER_AGENT` 已设。

**Q: 第一次请求很慢**
免费平台休眠后冷启动，正常。配置保活即可。

**Q: 正文为空，`finish_reason: length`**
`max_tokens` 太小，推理 token 吃光预算。云端版已强制下限 16384。

**Q: 想换人格**
改 `JIANG_SYSTEM_PROMPT` 环境变量重新部署，或改 `app.py` 里的 `DEFAULT_SYSTEM_PROMPT`。