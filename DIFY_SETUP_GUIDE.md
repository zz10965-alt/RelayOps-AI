# Dify Cloud 真实集成操作指南

核查日期：2026-10-30。当前只完成**导入与集成准备**；未登录你的 Dify Cloud、未安装账号内插件、未导入/发布应用、未调用真实模型、未公开部署 API。现有 Phase 1–3 与前端均保留。

## 1. 已准备的文件与兼容性边界

- `workflows/relayops.ifpkg`：Dify Cloud 当前文档所述应用包候选，ZIP 内含 `manifest.yaml` 与 `app.yaml`。manifest 使用 `dify.app` / format_version=1，并包含实际字节长度和 SHA-256；本地完整性测试已通过。
- `workflows/relayops.yml`：同一应用的裸 DSL，保留 0.3.0 版本标签以兼容现有节点；不是声称 Cloud 当前版本为 0.3.0。
- `workflows/analysis.schema.json`：与后端 Analysis 字段对应的严格 JSON Schema；视觉节点已启用原生 Structured Output，Code 节点从 `vision.structured_output` 取值，并序列化整个 HTTP body。
- 官方源码本次 CURRENT_APP_DSL_VERSION 为 0.7.0；Cloud 的实际部署/灰度版本不能由 GitHub main 推断。旧 DSL 可能出现版本确认/迁移，**实际导入仍待你验证**。不要为了消除警告直接修改版本号。
- 最新 Cloud 文档使用 **Create → Import App** 和 `.ifpkg`；旧 UI 可能显示 **Import DSL** 并接受 `.yml`。优先应用包；只有页面明确接受 YAML 时才用裸 DSL。文件被选中不等于导入完成。
- `dependencies: []` 是有意的：没有编造 Marketplace 插件版本或哈希。官方 OpenAI 插件需要先在你的 workspace 手动安装，再在视觉节点重新选定。

修改后可重建文件：在仓库根目录运行 `.venv/bin/python scripts/build_workflow.py`。这只生成本地候选，不能替代 Dify 导入验收。

## 2. 登录与安装官方 OpenAI Model Provider

1. 打开 [Dify Cloud](https://cloud.dify.ai/) 并登录，确认在目标 workspace。需要 workspace Owner/Admin 管理模型提供商；导入应用需要 Editor 或以上权限。以实际 Cloud 登录重定向和页面为准。
2. 当前官方文档入口为 **Integrations → Model Provider → Install model providers**，或从 [Marketplace](https://marketplace.dify.ai/) 搜索 **OpenAI**。部分旧 UI 位于 workspace **Settings → Model Provider**。
3. 核对提供者为 **langgenius**，插件名 **openai**，节点 provider ID 为 `langgenius/openai/openai`，不要误选 OpenAI-compatible 第三方插件。
4. 点击 Install。若已装，记录实际安装版本，不必盲目升级。本次官方仓库 manifest 为 **1.1.0**，这不是你的 Cloud 已安装版本。
5. 在提供商卡片 **Setup / Configure** 填入 OpenAI 提供商 Key，或确认该模型可通过 workspace AI credits 使用。OpenAI Key 只填在 Dify 的安全配置里，**不是**本项目的 `DIFY_API_KEY`；ChatGPT 订阅也不能代替 API 权限和计费。
6. 保存后检查凭据校验、额度/模型权限。若使用多组凭据，确认视觉节点选中的实际凭据与 Usage Priority，避免调用到意外账户。

### 本次实际核实的视觉模型

| 官方模型 ID | 官方预定义文件中的能力 | 本项目选择 |
|---|---|---|
| `gpt-4.1-mini` | `vision`、`structured-output`、chat | 导入候选默认值 |
| `gpt-4.1` | `vision`、`structured-output`、chat | 有相应权限时可手动选择 |

以上均由官方插件源码核实，不是猜测 ID。原候选 `gpt-4o` 的无日期预定义 YAML 在该源码快照中未找到；不能据此断言 OpenAI 全面停用它，但也不能继续假定它在当前 Cloud 列表可选。**源码支持 ≠ 你的插件版本支持 ≠ 账号有权限 ≠ 真实调用通过**。若 Cloud 列表没有上述模型，不要输入随机 ID；先检查实际插件版本/凭据，记录页面错误。

## 3. 导入与核对节点

1. 在 **Studio → Create → Import App** 上传 `workflows/relayops.ifpkg`，创建专用测试 Workflow。不要导入到其他已有业务应用上覆盖其 draft。若该项目已有 Dify 应用，先导出备份，再只更新该项目测试应用；更新会替换 draft，部分 WebApp 设置可能立即影响现有页面。
2. 如有 DSL 版本/迁移提示，审阅并确认，记录提示、Cloud 日期与安装插件版本。若失败，保留错误文本（删除秘密），不要宣称导入成功。
3. 从视觉节点的模型选择器重新选择 **OpenAI / gpt-4.1-mini**。确认 Vision 开启、High detail、文件变量为 **Start.image**，不是未提供的 `sys.files`。Start 是单文件 `file`，接受 local_file 图片；不需要开放额外聊天附件功能，应用 features.file_upload.enabled=false 不会取消显式 Start.image 输入。
4. 确认 Structured 开启、Schema 与 `workflows/analysis.schema.json` 相同，字段为 order_id / damaged / product_match / image_quality / confidence / summary，禁止多余字段。如显示 **Model not supported**，暂停该模型测试，不将提示词 JSON 当原生结构化成功。
5. 核对完整链路：
   **Start → GET订单商品 → GET政策 → Vision → Code JSON序列化 → POST resolve → End**。
   订单/政策先读是为了让视觉节点有商品参照；视觉后 resolve 会重新查询事实、执行规则、创建并独立连接回读。没有改写既有业务模块。
6. 三个 HTTP 节点都应使用 HTTPS、SSL verify=true、`Authorization: Bearer {{#env.BUSINESS_API_TOKEN#}}`；超时字段 connect/read/write 已修正。resolve 不启用节点自动重试，既有后端 HTTP 适配器最多尝试两次，业务操作仍由数据库唯一约束实现幂等。
7. Code 输入来自 `vision.structured_output`，输出整个 JSON 请求字符串，HTTP body 是单独的 `{{#serialize.body#}}`。不要再给这个占位符外包一层引号，否则会变成 JSON 字符串而非对象。
8. End 返回 `resolve.body`，其中包含由服务端回读的 application/status/trace。该节点没有额外 GET 申请节点；独立回读已在服务端 `application()` 中使用新数据库连接完成。验收还会通过单独 SQLite 脚本再读一次。

## 4. 变量与秘密分别配置在哪里

| 名称 | 配置位置 | 内容与用途 | 当前证据 |
|---|---|---|---|
| `DIFY_BASE_URL` | FastAPI 服务进程环境 | Dify Cloud 为 `https://api.dify.ai/v1`；不能填 Studio 登录地址 | 当前进程未设置 |
| `DIFY_API_KEY` | FastAPI 安全服务端环境 | 该 Workflow 应用的 App API Key；用于上传和运行 | 未设置、未验证 |
| `DIFY_TOOL_TOKEN` | FastAPI 安全服务端环境 | 随机高熵实际秘密，后端用于恒时比较工具 Bearer | 未设置、未验证 |
| `BUSINESS_API_URL` | **Dify Workflow 的 Environment Variables** | 你控制的、Cloud 可达的 HTTPS API origin，不带尾部 `/api` | 未配置；DSL 为故意不可达的 `.invalid` 占位地址 |
| `BUSINESS_API_TOKEN` | **Dify Workflow 的 Secret 变量** | 必须与后端实际 `DIFY_TOOL_TOKEN` 相同；三个HTTP节点使用 | 包内为空 |
| OpenAI provider Key | Dify Integrations 的 OpenAI Setup | 模型服务商凭据，与 App API Key 不同 | 无账号可见证据 |
| `RELAYOPS_DB` | FastAPI 环境，可选 | 默认 `.data/relayops.sqlite3` | SQLite 已本地验证 |

`BUSINESS_API_URL` 不是现有适配器消费的后端变量，只在 Dify HTTP 节点使用。可在后端设置同名镜像供预检，但不会自动同步到 Dify。`.env.example` 仅示例，不会自动加载。

不要把工具 token 配成仅由**出站代理**替换的占位值：它需要在后端作为实际秘密与传入 Bearer 比较。若 Cloud 的秘密机制只支持出站替换，请在受控 API 主机的 secret manager 注入实际工具 token，而不是尝试读出代理秘密。秘密不进前端、不写 Git、不放聊天、不截图，不导出带 secret values 的包。

当前执行环境的网络 allowlist **不含 `api.dify.ai`**。在 Cloud 环境设置中保留已有条目，追加该域名；如使用代理注入 App Key，绑定目标也应是此精确主机。不要开放 `*`、禁用 TLS 或清除继承代理。这个出站设置只解决 **FastAPI → Dify Cloud**，不会建立反向回调。

## 5. 为 Dify Cloud 提供安全 HTTPS 回调

**现有 FastAPI 只监听 127.0.0.1，Cloud 无法访问它。** `localhost`、`host.docker.internal`、私网容器 IP 和执行环境出站代理都不是公共回调入口。

可选路径（均需你另行授权/配置，本次没有执行）：

- 推荐：使用你已有的受控测试主机或应用托管环境，运行这套 FastAPI 与 SQLite；同机反向代理终止 TLS，再转发到 loopback。使用你拥有的域名、公共 CA 证书和持久磁盘。随后从该 API 主机发起完整 E2E，让上传/运行/回调落到**同一个后端实例和数据库**。
- 临时调试：仅在你明确授权后使用可撤销、带服务身份鉴权和路径限制的 HTTPS 隧道。若访问网关要求额外 header，须同步配置所有 Dify HTTP 节点。不要直接把整个开发服务公开；免费裸隧道地址不等于安全部署。执行机是否支持入站/隧道目前未验证。

仓库提供 `deploy/dify-callback.nginx.conf.example` **审阅模板**，未安装、未执行 nginx -t、未部署。它只公开 GET订单、GET政策和 POST resolve；所有路径在网关验证 Bearer，resolve 再验证后端 Bearer 与案件执行 token，其余路径返回404。需要在 Nginx 所在主机安全创建 0600 的 secret map、配置实际证书和域名，在自己的配置上下文运行 nginx -t 后才能启用。`proxy_pass 127.0.0.1` 假定 Nginx 与 API 同机；容器部署需受控内部网络，不能照抄。

必须保留的边界：

- HTTPS 有效证书和 SSL 校验；禁止公开 `/docs`、`/openapi.json`、UI、`/api/cases`、metrics 和数据库文件。
- 没有授权 header 时订单/政策应401，错误工具token应401，正确网关token但无有效案件执行token也不得创建。
- 请求限流/连接限制在你现有网关按测试流量配置；不要在日志中保存 Authorization、请求 body 或执行token。保护 Dify workflow run 输入日志的访问权限。
- 不假设 Dify Cloud 有某个固定出站 IP；如需 IP allowlist，只能使用 Dify 正式提供且适用于你 workspace 的当前出口信息。
- 从 **Dify HTTP节点单步测试**证明 Cloud 可达，不能用本机curl成功替代。401/403排查网关身份，404排查路径，TLS错误排查证书链，超时排查路由/网关/Dify策略；不要关闭安全检查“修通”。

## 6. 无副作用节点测试、发布和 App API Key

1. 配置 Workflow Environment Variables 的 HTTPS 地址和 Secret；先只运行订单与政策 GET 节点，用 DEMO-1001 验证实际返回订单/商品/30天政策。页面缺少单节点测试能力时，可先在专用测试草稿中临时断开写节点，测试后恢复并核对DSL；不要覆盖其他项目。
2. 单独测试视觉节点：上传真实、清晰、无个人信息的损坏白色陶瓷杯照片，使用订单实际返回作为商品参照，查看 `structured_output`。再用模糊/无关图片看实际输出，记录模型/插件版本，不用白色单像素夹具当损坏证据。
3. 不要为 Studio 整图测试随便填写 case_id/execution_token；这两个输入由后端生成并关联 running 案件，假值会被resolve拒绝，这是预期防护。完整业务验收应从现有Web Demo或后端API发起。
4. 检查节点与错误后，在该专用 Workflow 点击 **Publish / 发布**，使 Service API 使用最新图。没有授权前 Codex 不代你发布。
5. 在此应用内部打开 **API Access / 访问 API / Service API**（具体文案以界面为准），点击 **API Key / 创建密钥**，生成该应用自己的 Key。仅安全保存到后端 `DIFY_API_KEY`。不要误用 OpenAI Key、知识库Key或其他应用Key。
6. 在 API 页面确认 base URL 与此 workspace 的说明一致，再安全注入后端三个 DIFY_* 变量，重启后端。GET `/api/health` 的 dify_configured=true 只证明变量存在，不能证明模型、回调或E2E通过。

## 7. 第一次真实 E2E 与独立数据库核验

在**实际运行 API 的主机**、现有 checkout 根目录执行（凭据由安全环境预先注入，不在命令中写明）：

```bash
.venv/bin/python scripts/dify_preflight.py
.venv/bin/python scripts/dify_preflight.py --check-api
.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

不要启动重复服务；已运行时只需按既有进程管理方式重启。若API运行在另一主机，在那台主机操作，并让反向代理指向它。默认只监听loopback是有意的安全边界。

预检默认不联网，只报变量存在/缺失，不打印值。`--check-api` 才只读调用 `/info` 和 `/parameters` 检查应用Key及发布输入字段，**不调用模型、不证明HTTPS回调**。当前缺配置时exit2/BLOCKED是正确结果，不是测试通过。

另开终端运行：

```bash
.venv/bin/python scripts/live_e2e.py --image /absolute/path/to/real-damaged-cup.jpg
# 将上一条实际输出的case_id填入，DB路径必须属于同一个API进程：
.venv/bin/python scripts/verify_case_db.py --db .data/relayops.sqlite3 --case ACTUAL_CASE_ID
```

首次正常场景使用 DEMO-1001，描述与商品照片一致。种子交付日来自首次初始化，若已过30天，不要篡改业务结果；先查看当前订单政策，使用独立测试DB准备合规合成订单再验收，保留原库。

实际链路：后端接收照片 → `/v1/files/upload`（user与run一致）→ `/v1/workflows/run`（Start.image引用local_file上传ID）→ 订单/政策GET → 真实视觉与结构化输出 → resolve重新查询事实并应用规则 → SQLite幂等创建 → 独立连接读取申请 → Dify End → 后端记录run_id/workflow结束 → 验收脚本GET申请 → 只读SQLite脚本再次检查。

live_e2e已修正等待逻辑：不能在回调刚创建申请、run_id尚未返回时提前宣告失败/成功。它等待workflow结束证据并核对订单、申请、trace。当前适配器仍使用既有blocking模式和90秒读超时；Cloud边缘代理可能限制长请求，超时必须记录为未完成或失败，不能据本地幂等测试假定远端恢复成功。若真实模型超时，再依据真实错误决定是否扩展streaming；本次不重写适配器。

成功证据必须同时有：真实run_id、视觉字段、return_create、return_verify、workflow成功事件，以及SQLite相同order_id的申请状态 **created**。created不等于approved或completed。额外测试：重复提交同一订单不增加申请；模糊/无关图片或超期订单转人工。

如实际失败，保留安全的case_id/run_id/错误类型和节点状态；不要分享照片中的个人信息、请求体token或Key。补录到 `progress/build-log.md` 与测试报告，不能只凭Dify节点变绿宣称业务写入。

## 8. 已验证 / 待验证

已验证：本地DSL图、Schema/转义、包manifest大小与哈希、原有业务与HTTP契约、只读数据库核验的合成测试、冻结前端的回归测试。测试结果见 `progress/test-report.md`。

待配置：账号插件/模型、应用导入、Dify环境变量、AppKey、受控HTTPS回调与执行机出站域名。未完成：真实图片分析、Cloud到API回调、真实业务E2E及远端失败恢复。当前不能标记项目整体完成。

## 9. 官方来源与核查证据

本次通过官方GitHub仓库读取文档/源码，没有登录Cloud后台。源码commit和核实模型字段见 `docs/dify-source-evidence.json`。

- [官方Cloud应用导入文档](https://docs.dify.ai/en/cloud/use-dify/workspace/export-import-apps)：`.ifpkg`、导入权限、旧版本边界。
- [官方Cloud模型提供商文档](https://docs.dify.ai/en/cloud/use-dify/workspace/model-providers)：Integrations、Setup、权限与Key。
- [官方LLM节点文档](https://docs.dify.ai/en/cloud/use-dify/nodes/llm)：Vision、Structured及不支持模型提示。
- [官方HTTP节点文档](https://docs.dify.ai/en/cloud/use-dify/nodes/http-request)：超时、SSL和返回值。
- [官方API入门](https://docs.dify.ai/en/api-reference/guides/get-started)、[Workflow API](https://docs.dify.ai/en/api-reference/guides/workflow)：Cloud URL、应用Key、file上传与user一致性。
- [OpenAI官方插件模型源码](https://github.com/langgenius/dify-official-plugins/blob/b4df0da33f8e6f0f4cde7b9250f317c1d69e2bb5/models/openai/models/llm/gpt-4.1-mini.yaml)。
- [Dify应用包格式源码](https://github.com/langgenius/dify/blob/dca4024e5777f44a8cc4937f898483c11ecbd62d/api/services/app_package_service.py)、[DSL版本常量](https://github.com/langgenius/dify/blob/dca4024e5777f44a8cc4937f898483c11ecbd62d/api/constants/dsl_version.py)。

来源中的当前main/插件源码不代表你的Cloud已安装同版；最终以你账号实际导入和调用结果为准。
