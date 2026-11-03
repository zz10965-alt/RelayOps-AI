> 最新托管选择是GitHub Pages，见[Pages部署准备](github-pages-deployment.md)。下文Cloudflare/Vercel作为保留备选；双模式与Windows安全步骤继续适用，实际Pages CORS来源为`https://zz10965-alt.github.io`。

# Module 1：同一静态网站的 Public Simulation / Private Live

## 当前结论与授权

在 `a9d07a1` 基础上本地实现，尚未提交/推送/发布。默认纯浏览器Simulation不需要任何后端或云数据库；Live通过私有操作者连接使用现有本地FastAPI/SQLite/Dify/DeepSeek。只实现Module 1，Module 2/3保留Planned。

**本地代码审阅/提交候选 Go；公开静态发布仍需用户批准和免费套餐条款确认；真实Windows+tunnel+Dify验收仍未通过。** 不把HTTP替身或合成fixture当成模型实跑。

公网网站持续可用取决于所选静态平台的免费额度、条款和服务可用性，不能保证永久免费或永不宕机。本轮未开通任何服务或付款。已知免费方案应由用户在发布当日核实；本环境访问下述官方页面被网络代理403阻挡，不能声称已核实最新配额/资格：

- Vercel Hobby：https://vercel.com/docs/plans/hobby （确认个人/非商业用途限制和当前免费额度；不选择付费升级或自动按量付费）。
- Cloudflare Pages：https://developers.cloudflare.com/pages/platform/limits/ （如果Vercel用途不适用，核对Pages Free条款和构建限制）。
- Quick Tunnel：https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/ （用于临时开发/演示，非永久有SLA的生产入口，地址会变，有限制）。
- Dify Cloud：https://dify.ai/pricing （独立于DeepSeek provider credits，可能有应用、文件、额度、工作流执行等限制）。

严格$0持续托管预算的安全底线是：只发布静态Simulation；没有免费可用Dify额度/临时隧道时保留Simulation，显式说明不能Live，不购买后端或数据库，也不假装在线。

## 实现与界面

- 同一React界面，默认 `SIMULATION · BROWSER ONLY`，持续横幅说明所有证据、动作、trace、时间和指标均为模拟。
- `simulation.ts` 在Map中保存本次浏览会话的订单、案件、申请；刷新后清空，无localStorage/sessionStorage。
- 默认白色陶瓷杯合成订单；可生成eligible/expired/shipping新订单。输入描述，选择clear/blurry/unrelated/low-confidence证据fixture。照片可选，仅在本地预览，**不会分析、上传，也不会影响fixture的判断**。
- 证据、30天政策、幂等申请与内存回读均为可交互的确定性模拟。时间使用固定2026-01-15开始的合成时钟；不代表真实请求时间。模拟成本/耗时不编造，API费用未知。
- 五阶段Understand/Retrieve/Decide/Act/Verify、raw JSON、结果、人工队列和评估复用现有组件。内存Verify明确不是SQLite验证。
- Operator Live connection入口可以被访客看见，但可见入口不提供权限：只有HTTPS目标通过匿名health的保护模式检查，以及带token的真实`GET /api/cases`认证检查后，才切入Live。
- 操作者只输入当前HTTPS tunnel origin和操作者token；不会在前端输入Dify/DeepSeek/tool key。配置仅在内存，token不进入URL、日志或持久浏览器存储。退出Live会中止在途请求、清除连接token并切回独立的Simulation。JS内存清理由GC管理，不宣称密码学擦除。
- Live失败清除当前展示列表/指标，显示`LIVE · DISCONNECTED`与错误，没有自动模拟回退。用户必须明确点击Disconnect and return to Simulation。模式切换重建界面，避免迟到响应混入另一模式。
- 历史 `VITE_API_BASE_URL` 仅作为私有连接表单的可选预填值，不自动连接。**本方案不要设置它**，否则该URL会成为公开构建信息；临时私有地址只在操作者运行时输入。
- 模块2/3没有伪操作页面。

## Windows一次性准备（不触发模型）

以下命令在你自己的Windows PowerShell中执行。创建/发布静态网站、启动对外隧道和模型执行分别需要你明确批准；本轮没有代执行。

1. 安装官方Python 3.12+、Node 24、Git；使用现有项目目录，不重建或覆盖旧数据。当前修改尚未推送，你需要批准交付后获取包含这些文件的版本，`a9d07a1`本身没有双模式实现。
2. 进入现有仓库（将下面第一行替换成实际路径）：

```powershell
Set-Location 'C:\path\to\RelayOps-AI'
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
npm --prefix web ci
npm --prefix web run build
```

不需要Activate.ps1或修改PowerShell执行策略。venv已存在时先确认它属于这个仓库，不清除旧数据库。

3. 在当前PowerShell会话设置非秘密变量：

```powershell
$env:RELAYOPS_LOCAL_LIVE = '1'
$env:RELAYOPS_PUBLIC_DEMO = '1'
$env:RELAYOPS_ALLOW_MODEL_EXECUTION = '0'
$env:RELAYOPS_DB = Join-Path (Get-Location).Path '.data\windows-live.sqlite3'
$env:RELAYOPS_CORS_ORIGINS = 'https://你的实际静态网站域名'
```

将来源替换为真实HTTPS origin，不带末尾`/`、路径或通配符。若要继续使用已有业务库，显式选择其绝对路径并保留备份，不随意改名/复制/迁移。`windows-live.sqlite3`是新演示库示例，不会删除`.data/relayops.sqlite3`。`RELAYOPS_LOCAL_LIVE=1`只允许绝对本地路径与loopback HTTP开发来源；必须同时启用现有认证模式。它不关闭鉴权、限流、并发限制或执行开关。

4. 用密码管理器生成两个不同的高熵ASCII随机秘密（均至少32字符），分别作为操作者token和工具token。私密输入，不打印到控制台/录屏，不放入脚本或Git。PowerShell可用：

```powershell
function Read-Private([string]$Prompt) {
    $secure = Read-Host $Prompt -AsSecureString
    [System.Net.NetworkCredential]::new('', $secure).Password
}
$env:RELAYOPS_DEMO_TOKEN = Read-Private 'Private operator token'
$env:DIFY_TOOL_TOKEN = Read-Private 'Separate Dify tool token'
```

环境变量是在本地后端进程中使用的明文秘密，不能把进程环境dump、`.env`或终端截图公开。

5. 若暂不接Dify，保持`DIFY_BASE_URL`、`DIFY_API_KEY`未设置（不要只复制BASE_URL）。如当前会话已有旧值，应先确认其用途，不覆盖生产凭据；新开独立演示会话最简单。
6. 启动仅本机监听的后端：

```powershell
& .\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --workers 1 --limit-concurrency 20 --timeout-keep-alive 5
```

此时可在本机检查`http://127.0.0.1:8000/api/health`。应见`public_demo=true`、`execution_enabled=false`。认证失败401是正常保护行为。不要将绑定改成`0.0.0.0`来解决Cloud访问。

## 临时HTTPS隧道（单独批准后）

1. 从Cloudflare官方安装说明下载适合Windows的`cloudflared`，保留签名/校验验证；不要从不明二进制站点下载或关闭TLS。官方安装入口：https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/ 。Windows若已有winget，可先检查实际包信息，再确认安装：

```powershell
winget show --id Cloudflare.cloudflared --exact --source winget
winget install --id Cloudflare.cloudflared --exact --source winget
cloudflared --version
```

如果查询不到或发布者不符，不盲目继续，改用官方安装入口。不要添加自动接受协议、跳过哈希或关闭TLS选项。本轮未在Windows实际执行这些命令。
2. 在第二个PowerShell窗口运行：

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Quick Tunnel生成临时HTTPS origin。确认当前工具输出与官方免费使用限制，不配置付费域名/套餐，不承诺固定永久地址。若Cloudflare当前不提供免费入口，停止Live，使用Simulation，不擅自购买其他服务。
3. 不要把可能存在的本地tunnel配置与生产命名tunnel混用。网络若阻断隧道所需协议，按官方诊断处理；不通过关闭鉴权/TLS解决。
4. 打开同一个已部署的静态站，点击Operator Live connection，输入输出中的**准确HTTPS origin**和操作者token。不要输入`localhost`或`host.docker.internal`，不要在地址中添加`/api`或token。
5. 页面完成health与认证检查后进入Live；模型执行仍关闭。可查看记录、创建新合成订单；不能提交案件。私有token可以访问记录，工具token不能替代操作者token。
6. 隧道会让URL在公网可达，但只有health和静态资源匿名可读，业务接口保留操作者/工具认证、案件执行token及限制。这不是隐藏服务的网络隔离方案。不要上传真实客户数据，测试使用无敏感信息的图片与合成业务。
7. 如果普通访客没有操作者token，就不能创建Live案件或获取Live记录；不要把操作者token写入Vercel变量、公开链接或录屏。

## Dify Cloud连接（不自动运行模型）

1. 先确认Dify当前套餐允许所需自定义Provider、文件输入和Workflow API调用；DeepSeek已有credits不代表Dify免费无限使用。不符合$0新增费用要求时停止Live准备。
2. 使用现有测试Workflow，必要时先导出备份。按`DIFY_SETUP_GUIDE.md`核对现有`workflows/relayops.ifpkg`、官方`langgenius/deepseek/deepseek`、`deepseek-flash`、Vision→Start.image、json_object、原生Structured关闭。工作流包本轮不修改。
3. Dify Workflow环境变量：
   - `BUSINESS_API_URL` = 当前tunnel HTTPS origin，无末尾`/api`。
   - Secret `BUSINESS_API_TOKEN` = 本地后端的`DIFY_TOOL_TOKEN`。
4. 发布/更新测试Workflow也需你的明确批准。取得这个Workflow的App Key（不是DeepSeek Provider key），在后端PowerShell会话私密设置：

```powershell
$env:DIFY_BASE_URL = 'https://api.dify.ai/v1'
$env:DIFY_API_KEY = Read-Private 'Dify Workflow app key'
```

BASE_URL、API_KEY、TOOL_TOKEN需齐备。停止原uvicorn后在同一已设置变量的窗口重启，保持`RELAYOPS_ALLOW_MODEL_EXECUTION=0`。
5. 另一个具备这些保护变量的本地会话可执行只读预检：

```powershell
& .\.venv\Scripts\python.exe scripts\dify_preflight.py --check-api
```

新PowerShell不自动继承另一窗口新增的变量；应通过同样私密方式设置，不能打印或复制整个环境。只读预检不调用模型；实际Dify→tunnel可达性仍须另行验证。
6. origin变化后，更新Dify的`BUSINESS_API_URL`并重新发布测试Workflow（需批准），同时在网页重新连接；不需要重建静态网站。关闭/重开隧道不能假设保留原URL。

## 真实执行与关闭（真实执行需另行批准）

只有你确认模型/Dify额度、照片授权和本轮执行预算后，才在本地设置并重启后端：

```powershell
$env:RELAYOPS_ALLOW_MODEL_EXECUTION = '1'
```

这不是开放匿名执行；操作者token、工具Bearer和案件execution_token仍必需。按网页生成新订单，A为eligible+真实破损白色杯图，B为eligible+真实模糊/无关图，C为expired/shipping+真实图。检查实际run ID、提取、业务拒绝/创建、return_verify及handoff，不把创建等同批准/退款。

在**同一数据库所在Windows电脑**独立只读核验A：

```powershell
& .\.venv\Scripts\python.exe scripts\verify_case_db.py --db $env:RELAYOPS_DB --case 实际案件ID
```

B/C要单独只读查询returns确认没有对应order_id申请。不要将测试fixture输出或未执行阶段冒充真实模型与数据库结果。浏览器与Dify的业务读回不是独立离线数据库检查的替代。

关闭顺序：网页点击Disconnect and return to Simulation → tunnel窗口Ctrl+C → uvicorn窗口Ctrl+C → 在秘密会话清除变量或关闭整个专用会话：

```powershell
Remove-Item Env:RELAYOPS_DEMO_TOKEN,Env:DIFY_TOOL_TOKEN,Env:DIFY_API_KEY,Env:DIFY_BASE_URL -ErrorAction SilentlyContinue
$env:RELAYOPS_ALLOW_MODEL_EXECUTION = '0'
```

不要删除SQLite文件。未完成任务下次启动按既有逻辑转人工，不自动重放。隧道/后端关闭后其他访客的Simulation仍由静态主机提供，不受影响。关闭电脑后Live不可用是预期行为。

## 免费静态部署（发布需批准）

- 首选用户核实符合用途的Vercel Hobby；GitHub仓库不变，根目录`web`，安装`npm ci`、构建`npm run build`、输出`dist`。保留现有`web/vercel.json`。
- 不添加任何后端、数据库、Dify/DeepSeek/token环境变量；本方案不需要`VITE_API_BASE_URL`。不创建Railway服务。
- Cloudflare Pages为备选：确认Free条款，Git项目根目录`web`，构建`npm run build`，产物`dist`；不增加Functions/Workers/付费绑定。
- 保持单个Production站点URL；没有自购域名也可用平台子域名。Dashboard导航为客户端状态，不需要额外API或动态服务器。
- 审阅代码并批准推送后才能从GitHub构建当前版本。授权公开发布前不要点击Deploy或连接可能自动部署的新项目。已连Git项目可能在push时自动部署，也需事先核对。
- 公网验收：用另一设备/无token的无痕窗口，在你电脑关闭时完成Simulation；记录浏览器没有API请求。认证Live单独验收，不复用公开会话。

## 6分钟面试脚本

- 0:00–0:45：同一ProductionURL，展示SIMULATION横幅，说明所有访客无需账号/后端。Module2/3是Planned。
- 0:45–2:00：生成订单，输入描述，选择clear fixture，运行模拟。展示SIM-ID、五阶段与“memory readback ≠ SQLite”；照片只本地预览，不做识别。
- 2:00–3:00：重复订单演示幂等；切blurry/expired展示拒绝与人工队列；评估明确为模拟计数。
- 3:00–3:45：在未共享的私密操作步骤中连接tunnel+操作者token，不在录屏暴露秘密。切LIVE横幅，说明是同一React应用和独立数据集。
- 3:45–5:15：仅在真实验收与执行审批完成后，上传真实图，检查真实run ID、提取、业务状态、trace和独立SQLite只读核验。未配置时不演示虚构成功。
- 5:15–6:00：展示安全边界与失败。断开tunnel后明确LIVE DISCONNECTED；手动切回Simulation作离线演示，直言是模拟回退，不是Live。

## 已验证与未验证

99项Python、8项Chromium、tsc/Vite构建、部署静态检查、pip check及本地Docker构建/卷/鉴权检查通过。Chromium覆盖静态服务器无backend依赖、断网后模拟、0浏览器API请求、模拟不改变真实库、实际本机跨域CORS/操作者认证、Live断线无自动回退及原有Live业务路径；一项health响应为UI契约替身。

当前只在Linux/Chromium验证；Windows PowerShell命令、实际公网HTTPS/tunnel、Vercel/Cloudflare发布、Dify Cloud与DeepSeek真实图片执行尚未验证。本轮未推送，之前verify #4仅证明a9d07a1，不证明当前改动的远端CI。无需这些外部条件即可使用本地独立静态Simulation，不能据此标记真实Live完成。

首次加载公共静态网站需要网络；已加载页面可在断网后继续Simulation。没有新增Service Worker/持久缓存，断网刷新或首次访问不保证可用。

断开网页连接只清除当前浏览器的连接与显示，不撤销后端已经接受的任务。停止演示前检查运行中案件；必要时先把执行开关改回0并重启，再独立核查业务状态，不能把浏览器断开解释为业务动作已回滚。

## 本轮精确文件清单（相对a9d07a1）

- `.env.example`
- `AGENTS.md`
- `API_SPEC.md`
- `ARCHITECTURE.md`
- `PLANS.md`
- `PRD.md`
- `README.md`
- `backend/app.py`
- `docs/unified-demo-guide.md`
- `progress/build-log.md`
- `progress/test-report.md`
- `scripts/check_deployment.py`
- `scripts/ui_server.py`
- `tests/test_predeployment.py`
- `web/e2e/dashboard.spec.ts`
- `web/playwright.config.ts`
- `web/src/data.ts`
- `web/src/main.tsx`
- `web/src/simulation.ts`
- `web/src/style.css`
- `web/src/types.ts`
