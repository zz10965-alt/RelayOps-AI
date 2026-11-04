# Module 1 真实执行准备与验收（2026-11-03）

## 新手分步入口（每步确认后再继续）

我可以完成：云工作区代码审查、无模型回归、包完整性检查和命令准备。你必须完成：Windows 本机操作、账号内 Dify 配置和私密口令输入。隧道公开入口、执行开关开启、任何真实模型调用分别等待你的明确授权。

当前仅做第1步：在 Windows 资源管理器打开你已有的 RelayOps-AI 文件夹，在地址栏输入 `powershell` 并回车，然后执行：

```powershell
Get-Location
py -3.12 --version
Test-Path .\backend\app.py
Test-Path .\requirements.lock.txt
Get-FileHash .\workflows\relayops.ifpkg -Algorithm SHA256
```

预期：位置为你的仓库目录，Python 为3.12.x，两次 Test-Path 都为True，包 SHA256 为 `dbe9c56528576ff9fc1cd375c56f1ee48ab1ea56c221e09424e67b8da262d33c`（大小写不限）。若不匹配或报错，反馈非秘密输出，先不要安装、启动或执行后续步骤。本轮代码尚未推送，已有 GitHub 下载版可能仍是旧包；不能仅用旧版完成本轮验收。

后续依次确认：本机依赖与绝对数据库路径→关闭执行的后端启动→Dify导入及视觉配置→只读鉴权检查→获批后临时隧道→再次获批后三类真实图片测试→独立查库和保存证据。当前不要运行下方后续阶段命令。

真实验收时，将 CLI 输出、case_id/run_id、申请 ID、时间、预期/实际结果和只读查库结果保存在你本机仓库外的私有文件夹；保留成功与失败记录，不保存口令或完整环境转储。图像与客户信息按私密资料保管，不提交 Git。SQLite verifier 仅验证成功创建；交接/政策拒绝还需只读核对该案件事件和同订单申请记录，不能仅凭界面文字判断零副作用。

复审：20文件未发现新增阻断性代码问题或无关改动；凭据格式扫描未发现密钥，包内环境秘密为空；中文UI样式、模式客户端及部署配置保留。Cloud导入/视觉兼容、Windows及真实HTTPS回调仍待实测。

## 审计结论

基线 e425e142b3f748966f41cfbf9334a534c3b95333，工作区起始干净。只完成 Module 1，本轮不提交、不推送、不部署、不启用隧道或模型。

既有 Live 实现并非模拟：FastAPI 上传图片至 Dify，运行 DeepSeek Workflow，通过独立工具凭据和一次性案件执行凭据调用规则引擎；SQLite 的订单唯一约束防止重复申请，提交后用另一连接回读。当前业务订单、商品与政策是合成演示业务数据，并未接入真实店铺、支付、退款或物流系统。创建申请不等于批准、退款或退货完成。

Public Simulation 仍在浏览器内存独立运行，默认无需后端；同一中文紫色 Dashboard 可手动连接受保护的 HTTPS Live 后端。凭据仅内存，断开清除，不自动用模拟替代真实失败。GitHub Pages、Railway、Vercel、Docker 配置与既有业务数据保留。

## 本轮修复

- 原来 Dify 模糊/无关/不匹配/低置信度/订单冲突等早期分支丢失证据。本次保留严格解析后的 analysis，通过终端交接结果传给后端；后端再次严格校验，且仅允许负面证据进入这条路径，再实际查询订单/政策、执行确定性拒绝判断并记录事件。此路径禁止携带正向可执行证据，不能创建申请。
- 非法 JSON、上游 HTTP/模型错误仍安全交接，不补造 analysis 或未观测到的阶段。没有证据的阶段保持“未观测”。
- 签收日期损坏时明确转人工；不修写订单，不创建申请。适配器增加 SQLite 异常兜底。
- 前端与 Dify 的回读检查必须匹配订单、申请 ID、created 状态。独立 SQLite 验收还核对成功事件中的相同申请和相同 run_id，拒绝无关的“成功”日志。
- 真实验收 CLI 支持新鲜合成订单、预期人工交接和原因检查，避免长期保留的 DEMO-1001 因时间推移而过期。
- 重新生成 relayops.yml 与 relayops.ifpkg；Dify 中已导入的旧版本不会自动更新，必须导入本轮新包并核对节点。环境变量仍为空，不包含秘密。

## 可复现测试计划

| 场景 | 本地自动化证据 | 真实验收要求 |
|---|---|---|
| 成功创建 | 严格结构化证据→规则→SQLite 创建→独立回读；HTTP 替身集成 | 真实匹配的破损白色陶瓷杯照片，新鲜 eligible 订单 |
| 超期/未签收 | 日期与签收规则，不能创建 | expired/shipping 新订单；模型先正确识别图片，随后确定性拒绝 |
| 图片模糊/无关/商品不匹配/低分 | 打包 Code 节点 + 适配器 + 临时 SQLite，保留证据且零创建 | 真实对应图片；不能保证模型一定给出预期标签，须记录实际结果 |
| 无效订单/输入、非法模型 JSON | 查询失败/边界验证/安全交接 | 使用不存在订单；Dify 查询失败，无需视觉推理成功 |
| 重复请求 | 同案件重试、跨案件同订单唯一约束、丢失 HTTP 响应后重试 | 同一成功订单再提交，申请 ID 必须相同、SQLite 只有一行；会再次调用模型，需批准 |
| 外部 API/上传/Workflow 失败 | HTTP 401/500、超时、畸形响应、有界重试；不编造结果 | 仅隔离测试配置中验证，勿改生产凭据或破坏业务数据 |
| 人工交接、回读失败 | 模型证据不足、数据库写入/回读错误、重启中断 | 查看实际 trace；若已写入但核验失败，先人工查库，不能宣称没有副作用 |
| 前端与部署 | 真实本地 API/CORS/鉴权；独立 HTTP 替身验证成功/交接展示及不匹配回读；静态离线模拟 | Windows 浏览器 + Pages + 实际隧道仍需实机验收 |

复现命令（仓库根目录；Windows 将 .venv/bin/python 改为 .venv\Scripts\python.exe）：

```sh
.venv/bin/python -m pytest -q
npm --prefix web run build
npm --prefix web run test:e2e
npm --prefix web run build:pages
npm --prefix web run test:pages
.venv/bin/python scripts/check_deployment.py --pages
.venv/bin/python scripts/check_docs.py
.venv/bin/python -m pip check
# Docker 默认构建；受代理环境需遵循环境 CA 配置
 docker build -t relayops-module1:local .
.venv/bin/python scripts/container_smoke.py
```

自动化中的视觉证据与 Dify HTTP 都是明确的测试替身，不是模型准确率。浏览器根路径测试包含真正本机 FastAPI/SQLite/CORS/鉴权和明确的 HTTP 契约替身；Pages 测试包含完全离线 Simulation 和 HTTPS 连接协议替身。不得将这些统计为真实 Dify/DeepSeek 成功次数。

## Windows：先离线准备，不开公网、不调用模型

本轮代码尚未推送，请先审阅。需要交付时另行批准提交/推送；不要用 GitHub 旧版本代替本轮修复。使用已有 checkout，保留数据库，更新前按自己的备份流程备份数据；不要 reset/删除 .data。

PowerShell，在仓库根目录：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
npm --prefix web ci
npm --prefix web run build
$env:RELAYOPS_PUBLIC_DEMO='1'
$env:RELAYOPS_LOCAL_LIVE='1'
$env:RELAYOPS_ALLOW_MODEL_EXECUTION='0'
# 指向你已有数据库的绝对路径；不要误切到新空库或删除旧库。
$env:RELAYOPS_DB=(Resolve-Path '.data\windows-live.sqlite3').Path
$env:RELAYOPS_CORS_ORIGINS='https://zz10965-alt.github.io'
function Set-PrivateEnv([string]$Name) {
  $secure=Read-Host "$Name（不回显）" -AsSecureString
  $ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try { [Environment]::SetEnvironmentVariable($Name,[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr),'Process') }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
Set-PrivateEnv 'RELAYOPS_DEMO_TOKEN'
Set-PrivateEnv 'DIFY_TOOL_TOKEN'
```

两个口令均使用密码管理器生成的至少32字符 ASCII 随机值，且必须不同；不要贴到聊天、URL、代码或截图。若首次使用且文件不存在，显式选择新文件路径，例如 `$env:RELAYOPS_DB=[IO.Path]::GetFullPath('.data\windows-live.sqlite3')`；服务会初始化合成订单。这不是迁移真实店铺数据。已有数据库在服务启动时会将上次中断的 queued/running 案件安全转人工，因此不要在另一个正在运行的实例上同时启动同库服务。

## Dify：由你在 Dashboard 操作

1. 在现有 Dify Cloud Workspace 导入本轮 `workflows/relayops.ifpkg`（必要时使用同版 YAML），建议保留旧应用作为回退，勿覆盖导出含秘密的文件。
2. 检查官方 provider `langgenius/deepseek/deepseek`、模型 `deepseek-flash`，你的账号实际必须支持视觉输入。保留 JSON object 模式、vision high、关闭 native Structured Output；不能把纯文本模型当作图片分析器。当前 Cloud 插件/账号兼容性尚未实测。
3. 模型提供商 Key 仅放在 Dify 的模型配置。后端 `DIFY_API_KEY` 是该 Workflow 的应用 API Key，不是 DeepSeek provider Key。
4. 先检查节点图、必填单张图片、HTTP Bearer、失败分支及新增交接 analysis 输出。暂不点击 Test Run。
5. `BUSINESS_API_TOKEN` 是 Secret，填与本机 `DIFY_TOOL_TOKEN` 相同的值。`BUSINESS_API_URL` 必须是你随后批准启动的 HTTPS 隧道 origin，不能填 Pages 地址，也不能带 `/RelayOps-AI/` 或 `/api`。
6. 按 Dify UI 发布应用配置以供 API 调用；发布应用配置本身不代表真实执行成功。不要分享公开运行链接。若 Dashboard 要求购买额度/升级，停止并另行决定，勿开自动充值。

后端安全配置（仍然关闭执行）：

```powershell
$env:DIFY_BASE_URL='https://api.dify.ai/v1'
Set-PrivateEnv 'DIFY_API_KEY'
.\.venv\Scripts\python.exe scripts/dify_preflight.py
# 配齐后可自行执行只读检查：访问应用 info/parameters，不触发模型。
.\.venv\Scripts\python.exe scripts/dify_preflight.py --check-api
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --workers 1 --limit-concurrency 20
```

只读预检成功不证明 Dify 能访问你的本机，也不证明模型支持真实图片。

## HTTPS 隧道：需要另行明确批准公开入口

本轮没有启动。你批准后，可使用已安装的官方 cloudflared 免费临时隧道，在第二个 PowerShell 运行：

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

这会建立公开 HTTPS 入口，临时地址每次可能变化；将输出的 origin 填入 Dify `BUSINESS_API_URL`，重新发布应用配置。保留后端双凭据认证和执行开关，不开放未认证业务端点，不把操作者口令给 Dify。无需购买 Railway/Vercel 服务、域名或付费隧道。

打开 `https://zz10965-alt.github.io/RelayOps-AI/` → 连接真实后端，输入隧道 HTTPS origin 和操作者口令。CORS 只填 `https://zz10965-alt.github.io`，没有项目子路径。执行开关仍为0时只验证连接，不能提交真实模型案件。浏览器关闭/断开后需重新输入内存口令。

## 真实模型验收：需要单独批准调用与可能费用

GitHub Pages 免费不代表 Dify/DeepSeek 推理免费。确认账户额度和消费边界后才批准本节。将后端的 `RELAYOPS_ALLOW_MODEL_EXECUTION` 改为1并重启单实例（运行中案件先结束）；无需改变认证或前端构建。

第三个 PowerShell 要安全配置自己的两个口令，勿依赖另一个窗口的环境自动继承。将照片路径换成自己的真实、匹配且可分享至 Dify 的商品照片。

```powershell
# 只在明确批准后运行；本命令会创建新合成订单并触发真实模型。
.\.venv\Scripts\python.exe scripts/live_e2e.py --create-order eligible --image 'C:\evidence\damaged-cup.jpg'
# 记录输出的 case_id、run_id、申请 ID。然后独立只读查库：
.\.venv\Scripts\python.exe scripts/verify_case_db.py --db $env:RELAYOPS_DB --case '<实际case_id>'
# 超期：应经过模型并由业务规则拒绝；每条命令均为新的模型调用。
.\.venv\Scripts\python.exe scripts/live_e2e.py --create-order expired --image 'C:\evidence\damaged-cup.jpg' --expect handoff --reason-contains '30天'
# 模糊图片：核对实际模型结果；不强制伪造标签。
.\.venv\Scripts\python.exe scripts/live_e2e.py --create-order eligible --image 'C:\evidence\blurry-cup.jpg' --expect handoff --reason-contains '图片'
```

重复提交使用首次成功的实际订单号 `--order '<实际订单号>'` 和同一图片。核对相同申请 ID；SQLite 同订单只允许一条申请。模型可能重新分析，会消耗调用额度。

回读失败或 workflow 失败时保留实际日志，不伪造 PASS，不自动删除申请/重置订单。按照上表分批批准其余异常场景。当前脚本不是评测准确率工具，不输出估算费用/时延；费用仅记录 Dify 明确返回的元数据，否则未知。

结束时：前端断开连接，Ctrl+C 停隧道，Ctrl+C 停后端，将下一次启动的执行开关恢复0。保留 SQLite 数据和真实 run 证据，不将它们提交 Git。

## 本轮实际结果与剩余门槛

最终结果见本文件末尾的验收记录。当前离线预检明确缺少 `DIFY_BASE_URL`、`DIFY_API_KEY`、`DIFY_TOOL_TOKEN`，退出码2；没有发出真实 Dify 请求。Dify Cloud 导入/插件版本/图片识别、Windows 实机、公开 HTTPS 回调与 Pages→真实后端链路仍未验收。

结论：本地代码具备受控真实执行链路和自动化回归证据；尚不能宣称真实端到端验收完成或生产可用。下一步先审阅本轮代码，再安全配置 Dify/Windows；隧道公开和模型调用分别另行授权。

## 最终验收记录

| 检查 | 实际结果 |
|---|---|
| Python 全量 | **116 passed**，1项既有 Starlette/httpx 弃用警告；原99项保留 |
| TypeScript + Vite | 根路径及 GitHub Pages 两种生产构建通过 |
| Chromium 根路径 | **11 passed**；包含明确的 Live HTTP 展示契约替身 |
| Chromium Pages | **2 passed**；子路径资产/刷新、离线零API模拟及HTTPS协议替身 |
| Docker | 本地构建通过；PORT8123、CORS含401、鉴权401、默认执行403、临时卷重启持久化通过；无公开端口，临时容器/卷清理 |
| 部署/文档/依赖 | check_deployment.py --pages、check_docs.py、pip check、git diff --check 通过 |
| Dify 离线预检 | **BLOCKED / exit 2**，三项服务端变量缺失；未发真实请求 |
| 真实 Dify/DeepSeek | **未运行**；不声称准确率、费用、延迟或真实成功 |
| GitHub CI/发布 | 本轮未提交/推送，未触发新远端CI或部署 |

Docker首次命令引用了不存在的CA路径，构建未启动；随后使用实际 environment-proxy-ca.crt 重试成功。前端截图回归没有造成既有截图文件变化。数据库未迁移或改写；所有业务测试使用临时数据库。

新包 SHA256：`dbe9c56528576ff9fc1cd375c56f1ee48ab1ea56c221e09424e67b8da262d33c`。包内 CRC、manifest 长度/SHA 与 YAML 一致性由测试检查。

本轮精确20文件清单：

- `backend/app.py`
- `scripts/build_workflow.py`
- `scripts/live_e2e.py`
- `scripts/verify_case_db.py`
- `workflows/parse_evidence.py`
- `workflows/check_result.py`
- `workflows/relayops.yml`
- `workflows/relayops.ifpkg`
- `web/src/main.tsx`
- `web/src/types.ts`
- `web/e2e/live-evidence.spec.ts`（新增）
- `tests/test_api.py`
- `tests/test_dify_preparation.py`
- `tests/test_integration.py`
- `tests/test_workflow.py`
- `tests/test_live_acceptance.py`（新增）
- `docs/module1-live-readiness.md`（新增）
- `README.md`
- `PLANS.md`
- `progress/build-log.md`
