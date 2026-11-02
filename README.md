# RelayOps AI

多模态电商运营异常处理 Agent：商品损坏售后 MVP。FastAPI + SQLite 模拟业务系统，Dify Workflow 负责视觉提取与 HTTP 工具编排，React/TypeScript 提供运营 Dashboard。

**当前状态：本地业务 API、Dify 协议契约与 Web Demo 已测试；真实 Dify 导入、视觉模型和远端端到端运行尚未验证。项目未达到全部完成标准。** 所有订单/商品/政策均为合成数据，不连接支付或真实商家。

## 本地启动

需要 Python 3.12+、Node 24（Cloud 已提供）。在仓库根目录：

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
npm --prefix web ci
npm --prefix web run build
.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

生产构建由同一 FastAPI 服务提供。开发热更新：后端如上运行，另一个终端 `npm --prefix web run dev`，Vite 会代理 `/api`。Cloud onboarding 不提供本地预览链接。不要把默认无用户认证的 Demo 暴露到公网。

默认数据库 `.data/relayops.sqlite3` 自动初始化，`RELAYOPS_DB` 可覆盖。首次初始化种子订单：DEMO-1001 已交付3天、DEMO-1002 已交付45天、DEMO-1003 运输中。种子日期不会随启动刷新。重启时中断任务转人工，不自动重放业务动作。

Dify 未配置也能运行 UI 与业务查询；提交完整案件将明确转人工，**不会生成假识别或假申请**。缺描述/照片标记待补充。白色测试 PNG 仅用于协议测试，不是损坏证据。

## 连接真实 Dify Cloud（需要用户操作）

详细页面入口、导入/模型/凭据、HTTPS安全边界与首轮验收见 **[DIFY_SETUP_GUIDE.md](DIFY_SETUP_GUIDE.md)**。

- 当前Cloud文档使用`.ifpkg`应用包：优先导入`workflows/relayops.ifpkg`；裸`relayops.yml`保留用于接受DSL的页面。包结构/哈希只通过本地验证，目标Cloud导入尚未执行。
- 当前本地包已改为官方DeepSeek `langgenius/deepseek/deepseek` / `deepseek-flash`：源码确认Vision与json_object，原生Structured关闭，使用严格JSON校验及证据门槛。用户确认已配置Provider，Codex尚未真实运行。详见[DIFY_PACKAGE_CHANGES.md](DIFY_PACKAGE_CHANGES.md)。
- 后端需要安全注入`DIFY_BASE_URL=https://api.dify.ai/v1`、该应用`DIFY_API_KEY`与实际秘密`DIFY_TOOL_TOKEN`。Dify Workflow需要`BUSINESS_API_URL`（Cloud可达HTTPS地址）和同值Secret `BUSINESS_API_TOKEN`。当前运行环境三项DIFY_*均未设置，当前出站allowlist也需追加api.dify.ai。
- 本地loopback或host.docker.internal不是Cloud回调地址。本次只准备受限HTTPS网关模板，未部署/未开隧道。不要公开无用户认证的Dashboard或全部API。
- 只读预检：`.venv/bin/python scripts/dify_preflight.py`；可选`--check-api`只读取Dify应用信息与参数，不调用模型。
- 首次真实验收：`.venv/bin/python scripts/live_e2e.py --image /path/to/real-damaged-cup.jpg`；再用`.venv/bin/python scripts/verify_case_db.py --db .data/relayops.sqlite3 --case ACTUAL_CASE_ID`独立只读核验。当前没有执行真实模型/E2E。

Dify工具执行后创建并回读申请；`application_created`只是申请真实存在，不能等同`approved`或`completed`。密钥不得发送到聊天、前端或Git。Cloud目标账号、模型、发布、回调和凭据都需要用户安全配置。

## 验证

```bash
.venv/bin/python -m pytest -q
npm --prefix web run build
npm --prefix web run test:e2e
```

浏览器测试使用系统 `/usr/bin/chromium`、临时真实 SQLite 与 FastAPI；隔离环境会移除 Dify 凭据，不影响真实业务 DB。其他机器可在 `web/playwright.config.ts` 配置浏览器路径。Cloud 命令沙箱内 ASGI TestClient 可能挂起，需要获准的非沙箱执行；不是测试通过。测试报告见 [progress/test-report.md](progress/test-report.md)。

## 界面与数据

Overview、New Case、Case Detail、Execution Trace、Resolution Result、Human Handoff、Evaluation 均调用实际 `/api`。统计来自 SQLite，空分母为 null；费用只读取 Dify 明确提供的 metadata，缺失显示未知，无 ROI 或虚构准确率。最新列表最多200条，统计全库。

OpenAPI：服务的 `/docs`。设计文档：[PRD](PRD.md)、[架构](ARCHITECTURE.md)、[API](API_SPEC.md)、[Workflow](workflow_design.md)、[评估](evaluation_plan.md)。界面截图见 [本地真实 Dashboard](docs/dashboard.png)，演示步骤见 [docs/demo-guide.md](docs/demo-guide.md)。完整阶段计划与未验证项见 [PLANS.md](PLANS.md)，用户原始指令保存于 [docs/project-instructions.md](docs/project-instructions.md)。

## 范围与限制

单进程内部 Demo，没有用户身份、租户隔离、外部部署、持久后台队列、人工批准或退款接口。敏感数据不得上传。工具 Bearer token 与案件执行 token 双重校验；图片校验内容与5MiB上限；业务API幂等，不接受模型自行宣称完成。Dify HTTP 有界重试（最多两次），异常留证并转人工。调用耗时与内容 trace 仅作调试，本地操作员可见；生产部署前必须加权限与保留周期。

源码已按用户明确授权提交并推送到 GitHub；未发布环境、未创建外网服务。物流/库存场景按要求延后。

用户后续已明确授权上传DeepSeek应用包及相关修改；当前版本应以本次GitHub提交为准，旧OpenAI包保留在历史提交中。真实Dify导入与E2E仍未验证。

## Module 1 面试演示与部署候选

最新开发、测试证据、Railway/Vercel配置、授权边界及6分钟演示脚本见 [Module 1验收报告](docs/module1-review.md)。支持生成新鲜合成订单、英文优先UI和真实事件五阶段时间线；Module 2/3仅标记Planned。公网候选Docker默认启用鉴权且禁用案件执行，尚未部署或验证真实Dify/DeepSeek闭环。旧种子不刷新，重复演示请生成新订单。

最终提交前复核见 [预部署报告](docs/predeployment-review.md)：基线73→上一轮79→本轮最终97项Python测试、4项Chromium通过；GitHub交付候选可审阅，真实部署与模型验收仍未完成。
