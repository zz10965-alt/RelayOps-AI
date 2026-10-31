# RelayOps AI 分阶段计划

## 环境与范围
2026-10-30：GitHub origin 可读但无 refs；本地 work 分支 unborn、无文件。Python 3.12.14、Node 24.19.0、npm 11.9.0。Cloud 无 Dify 绑定。仅实现商品损坏售后 MVP，所有订单和政策是合成模拟数据。

## 阶段、依赖与验收
1. **Phase 1 需求与架构**：PRD、架构、工作流、API 和评估方案齐全；定义状态机、政策、失败场景、信任边界。验收：文档一致性检查。状态：文档完成，检查通过。
2. **Phase 2 Dify 最小流程**：生成版本标记的 DSL，图片输入→视觉 LLM→结构化 JSON→HTTP 工具→结果。解析和图连通检查；导入、真实节点测试需 Dify 版本/部署/模型。状态：DSL 生成/本地检查通过；导入和远端节点测试阻塞。
3. **Phase 3 模拟 API**：FastAPI + SQLite；订单/政策查询、幂等创建、状态查询、持久化任务与 trace；API 测试覆盖无效输入、规则拒绝、重复请求。状态：本地 API/商品/规则/持久化验证通过；最新全套35项通过。
4. **Phase 4 集成**：服务端上传 Dify 图片并运行 Workflow，工具回调做确定性校验、创建及回读，核对返回任务状态；有界重试、失败转人工。契约测试与真实远端测试分开。依赖 Phase 2/3。状态：适配器与HTTP契约测试通过；真实Dify端到端阻塞。
5. **Phase 5 Web Demo**：Overview、New Case、Case Detail、Execution Trace、Resolution、Human Handoff、Evaluation；React/TS 调用实际 API，图片上传、加载和错误状态；类型检查、生产构建及浏览器测试。状态：本地实现完成，构建及2项浏览器测试通过；真实Dify成功路径待配置。
6. **Phase 6 自动化与交付**：场景测试、HTTP 冒烟、文档、指标口径、操作指南。端到端真实 Dify 必须独立验证；未配置则不能标记项目完成。状态：本地自动化/说明/CI配置完成，真实Dify验收及GitHub远端CI未运行。

## 必需与可选检查
必需：pytest、DSL 结构检查、前端 tsc/build、实际 HTTP 持久化请求；真实 Dify 运行和 Web 全链路为产品完成门槛。可选：物流/库存扩展、外部部署、商业指标，当前不实施。

## 外部前提
需用户选择 Dify 部署/版本/视觉模型，在服务端安全配置 DIFY_BASE_URL、DIFY_API_KEY、DIFY_TOOL_TOKEN；Dify 必须可访问本 API 的 HTTPS 工具地址。未获授权不发布外网、不推送 GitHub。

## 当前验收证据
- Python：35 passed，1项Starlette/httpx弃用警告；不是功能失败。
- Web：tsc + Vite生产构建通过；Chromium 2 passed（真实FastAPI/SQLite，未配置Dify分支）。
- HTTP冒烟：health、静态UI、订单、政策、持久化缺资料案件、metrics通过。
- 复现：scripts/install.sh 完整执行通过（锁文件pip、npm ci、build、pip check）。
- npm全依赖audit：0项已知公告；不代表所有依赖绝对安全。
- 已保存Cloud install_script/start_skill草稿，尚未发布或验证新任务恢复。

## 继续条件（产品仍未全部完成）
1. 提供Dify部署URL、实际版本、视觉模型名称（非秘密信息）。
2. 在Dify导入候选DSL，配置模型与工具端点/秘密；在后端安全配置app key和实际工具token。勿在聊天发送Key。
3. 确保Dify可达本API的HTTPS或同网络受控地址；当前服务仅本机监听，未对外部署。
4. 运行scripts/live_e2e.py并记录真实run_id、视觉结果、业务创建和独立回读；补测真实模糊/无关照片路径。
5. 用户在环境设置中审阅并保存配置，再发布环境。GitHub源代码尚未推送，远端CI未运行。

## Phase 4 续作 — Dify Cloud 集成准备（2026-10-30）
本轮仅推进Phase 4；Phase 1–3不重做，web所有源文件冻结。完成官方文档/源码核查、Cloud应用包候选、原生结构化输出、HTTPS/超时/鉴权配置检查、只读预检、真实验收等待修正和独立SQLite核验。操作入口与官方来源见DIFY_SETUP_GUIDE.md。
- 已验证：45项Python测试通过（原有35项基础上扩充10项），保留1项依赖弃用警告；Cloud包manifest字节数/SHA256及Schema/序列化检查通过。
- 已配置候选：官方OpenAI provider `langgenius/openai/openai`，源码确认的视觉/structured-output模型 `gpt-4.1-mini`；并非账号内已配置。
- 待配置：实际进程DIFY_BASE_URL、DIFY_API_KEY、DIFY_TOOL_TOKEN均缺失；BUSINESS_API_URL需要在Dify Workflow设置，后端同名值仅为可选预检镜像。当前执行机还需允许出站api.dify.ai。
- 待手动操作：Owner/Admin安装/配置OpenAI；Editor导入relayops.ifpkg（旧UI可选YAML）、节点检查、发布测试Workflow、生成AppKey；另行授权并提供受控HTTPS网关。
- 未完成：目标Cloud导入兼容验证、真实视觉图片、Cloud回调、真实E2E；没有公开服务、开启隧道、推送或发布。
- 本机监听不代表公网可达；deploy/dify-callback.nginx.conf.example只是待审阅模板，未部署/未运行nginx -t。
- 暂停条件：上述所有无需外部凭据的准备完成后，等待用户配置；不将HTTP替身/结构检查列为真实Cloud运行成功。

## GitHub交付状态更新
已获用户明确授权，将现有49个项目文件提交并推送至zz10965-alt/RelayOps-AI的main分支，包含原样ifpkg。此前“未推送”的条目是当时的历史状态；真实Dify与部署状态未改变，远端CI结果尚未核实。

## 本次DeepSeek包修订（仅现有Workflow）
按用户新要求替换官方DeepSeek/deepseek-flash；源码确认VISION与JSON模式，无native structured-output声明。启用文件/图片上传，严格JSON解析与条件分支，失败/低质量不进入resolve；完整结果需后端回读证据。BUSINESS_API_URL改为空的待配置变量，token保持Secret空值。
本地全套73 passed/1既有依赖warning；业务API与React逐字节不变。Cloud导入、模型及E2E仍未验证。现有适配器对不调用resolve的早期分支仅记录通用handoff，具体原因见Dify日志；此次不更改。没有部署/发布/推送，新包在工作区，GitHub仍旧版。详见DIFY_PACKAGE_CHANGES.md。

交付授权更新：用户后续明确同意上传DeepSeek新版与相关修改至GitHub；此前禁止推送/仅本地的状态已被此授权替代，Dify部署/发布仍不执行。
