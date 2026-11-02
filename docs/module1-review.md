> 最新结果与完整交付清单以 [最终预部署复核](predeployment-review.md) 为准。本文保留上一轮79项测试及演示脚本作为历史记录。

# Module 1 验收与面试演示交付

## 当前结论（2026-11-02）

本地开发与演示改进已完成，可供代码审阅和本地演示；**公网发布 No-Go，真实 Dify/DeepSeek 全链路未验收，Module 1 不标记全部完成**。未开始 Module 2/3，未推送、未开公网端口、未创建付费服务、未改生产秘密。

开始时 HEAD 为 `65aa556cbc3bb87af037fcc20a3ba320fa2f00c4`，`git status --short` 与 `git diff 65aa556 --stat` 均为空。附件所说约27项未提交部署改动在这个工作区不存在。已有源码、数据、DeepSeek包与 Nginx 模板均保留，没有 reset 或迁移数据库。如那批改动位于另一工作区，请提供其非秘密 diff/文件后另行合并，不能声称已审阅不存在的文件。

## 本次实现

- 延续现有 React Dashboard，导航、表单、结果与指标以英文为主；业务原始原因/模型证据保留原文。
- Overview 展示三模块边界：仅 Damage & Returns 可用；其余标 Planned。
- `POST /api/demo/orders`：eligible / expired / shipping，使用随机新订单号和当前日期，不刷新旧种子、不清除旧申请。A/B 均使用 eligible，区别由用户实际上传图片决定。
- Understand / Retrieve / Decide / Act / Verify 来自后端真实事件。未观测到的阶段不标成功；Retrieve 缺少任一查询事件为 partial；Decide 的记录不冒充模型节点成功。时间戳为后端事件时间，不是云端节点开始时间；未测量耗时明确标注，不伪造节点耗时。
- 保留原始 Execution Trace、模型证据、业务事实、申请与 run ID。Workflow 补清晰照片终止分支可传达明确人工交接提示；Workflow 输出永远不能授权创建申请。
- 保留原有确定性业务规则、案件执行 token、工具 Bearer、每订单唯一申请、写入后独立连接读回。`created` 不等于 `approved` 或 `completed`。
- 公网候选模式需私有操作者 token（浏览器只在内存保存，刷新后重新输入）；工具事实查询/resolve 使用单独 DIFY_TOOL_TOKEN。
- 公网案件执行默认禁用，需另行授权后显式设 `RELAYOPS_ALLOW_MODEL_EXECUTION=1`。CORS 显式 HTTPS origins；请求流及 Content-Length 上限；10次/分钟全局写请求限流，最多2个 queued/running 案件（SQLite事务检查）；Uvicorn单 worker、20连接并发限制。

这是单实例、单操作者合成业务 Demo，不是生产多租户身份系统。限流为进程内状态，重启会清零；不能横向扩容后仍假设全局限流生效。图片5MiB/2000万像素限制保留。密钥不进入Vite变量或Git。

## 测试证据

| 类别 | 命令/结果 | 边界 |
|---|---|---|
| Python本地单元/集成及HTTP替身契约 | `timeout 90 .venv/bin/python -m pytest -q`：79 passed，1项既有Starlette/httpx弃用warning | 含新订单重复演示、政策拒绝、时间线、默认禁用执行、鉴权、大小、限流、结构校验、幂等/读回；替身不是模型实跑 |
| TypeScript与构建 | `npm --prefix web run build` 通过 | 不是Vercel部署 |
| Chromium | `npm --prefix web run test:e2e`：3 passed | 真实FastAPI/临时SQLite；未配置Dify路径、移动布局、新订单与未执行阶段 |
| 包一致性 | `.venv/bin/pip check`：通过 | 无依赖冲突 |
| 部署静态检查 | `.venv/bin/python scripts/check_deployment.py`：通过 | 检查配置及构建产物中服务端秘密标识/测试token；不声称覆盖未知生产秘密 |
| Docker构建 | `docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt -t relayops-module1:local .`：通过 | 使用代理CA且保留TLS验证，未部署Railway |
| 本地容器功能 | `.venv/bin/python scripts/container_smoke.py`：通过 | PORT=8123、health、401、默认执行403、新订单与/data重启持久化；临时卷/容器已清理，无对外端口 |
| GitHub CI | 未运行远端CI | 仅增加静态检查步骤，未推送 |
| 真实云部署 | 未执行 | HTTPS证书、真实域名CORS、Railway卷挂载及计费均未验收 |
| 真实Dify/DeepSeek | 未执行 | 无安全注入凭据、未配置可达HTTPS回调、无用户真实损坏图 |

最初浏览器回归有2项失败，诊断为英文按钮选择器歧义和异步生成订单未等待；修正选择器和等待条件后3项通过。容器启动/重启短暂连接拒绝由就绪轮询处理，最终功能断言通过。

## 部署准备与用户操作（依次执行）

1. **先审阅代码及部署方案**。如需要找回所述27项改动，请先从原工作区获取；本轮未覆盖任何已有未提交改动。
2. **批准推送之前不上传GitHub**。你确认后才能另行 commit/push 并核查真实CI。本次仅保留工作区修改。
3. **计费确认点**：你选择/确认 Railway 与 Vercel 账户、额度、区域和费用；没有批准之前不创建/激活服务。保持 Railway 单副本/单worker，不启用横向扩容。
4. Railway使用仓库根目录Dockerfile，挂持久卷到 `/data`，`RELAYOPS_DB=/data/relayops.sqlite3`；`PORT`由平台注入。Docker默认 `RELAYOPS_PUBLIC_DEMO=1`。安全平台配置中设置高熵且至少32字符的 `RELAYOPS_DEMO_TOKEN`，设置 `RELAYOPS_CORS_ORIGINS=https://你的前端域名`（多个用逗号分隔，不用通配符）；**保持案件执行禁用**。
5. Vercel Root Directory选 `web`，`npm ci`、`npm run build`、输出 `dist`；设置唯一公开连接变量 `VITE_API_BASE_URL=https://你的后端域名`，必须为HTTPS origin。不要设置任何 `VITE_*KEY`、token。操作者在UI密码框输入自己的访问token，点击Connect；不要硬编码或在URL中传token。
6. **公网发布批准点**：你明确批准发布后，才可部署前后端；检查HTTPS证书、健康检查、未授权401、未允许来源的CORS、默认执行403和卷重启持久化。这些都尚未实测。
7. Dify按 `DIFY_SETUP_GUIDE.md` 导入现有DeepSeek `.ifpkg`，核对实际Cloud兼容性、deepseek-flash视觉能力、应用输入和发布状态。在Railway保护配置设置 `DIFY_BASE_URL=https://api.dify.ai/v1`、应用 `DIFY_API_KEY`、实际 `DIFY_TOOL_TOKEN`；Dify端设置 `BUSINESS_API_URL=https://你的后端域名`、同值 `BUSINESS_API_TOKEN`。应用key和工具token用途不同；不在聊天发送秘密。确认环境出站允许 `api.dify.ai`，本Cloud当前未配置该自定义域。
8. 先运行只读预检 `scripts/dify_preflight.py --check-api`（确认保护变量已注入）。Cloud开发环境和Railway变量是不同位置，不能假设自动同步。
9. **模型费用与执行批准点**：确认模型预算后，由你明确批准受控执行，再设置 `RELAYOPS_ALLOW_MODEL_EXECUTION=1`，只允许私有操作者访问；不开放匿名、不启用无限执行。
10. 提供无个人敏感数据的真实损坏白色陶瓷杯图、模糊/无关图。A生成新eligible订单→描述/真实图片→提交；B新eligible订单→不适用图→人工/补图；C新expired/shipping订单→实际证据→政策拒绝。模型若错误分类不能记为通过，应保存实际run并诊断。
11. A逐项检查run ID、分析、return_create、return_verify与实际申请，再在后端同一卷运行 `scripts/verify_case_db.py --db /data/relayops.sqlite3 --case 实际ID`。B/C独立只读查returns中对应order_id计数必须为0。失败时不能把未调用Act算创建成功，也不能把application_created称退款完成。
12. 记录真实部署URL/版本、三场景run ID、截图、成本元数据（若无则未知）和独立DB核验。完成后再作Module 1最终验收；Module 2/3继续等待你明确批准。

## 6分钟面试共享屏幕脚本

- **0:00–0:45 Overview**：说明合成电商数据、只有Module 1可用；展示Planned模块。强调模型提取与后端执行分工。
- **0:45–1:30 New Case**：生成fresh eligible订单，解释日期新鲜且不会撞旧申请；上传自己准备的真实破损杯图，填写描述。未配Dify时明确说只演示本地路径，不展示虚假成功。
- **1:30–2:45 A路径**（只有真实环境验收后）：提交，查看run ID、真实模型字段和五阶段时间线；展开原始trace。说明not observed不是成功，耗时只展示真实记录。
- **2:45–3:30 Verify**：展示created申请ID以及独立SQLite只读核验。强调尚未批准、退款或完成退货，重试受唯一约束保护。
- **3:30–4:30 B路径**：新订单上传模糊/无关图片，展示实际补图/人工原因与未执行阶段。若模型实际未拒绝，坦诚记录失败，不口头替换结果。
- **4:30–5:15 C路径**：生成expired或shipping订单，提交真实图，展示可信后端拒绝与无申请的DB证据。没有模型配置时只展示已通过本地政策回归的证据，不能称云端成功。
- **5:15–6:00 Evaluation/架构**：指标来自DB，不是模型准确率；费用缺失显示Unknown。解释单实例限制、鉴权、限流、默认禁用执行与生产化边界，最后说明后续模块须逐一验收。

## 文件与后续

核心修改：backend/app.py、web/src/main.tsx、web/src/style.css、web/vite.config.ts；测试：tests/test_module1.py、tests/test_integration.py、web/e2e/dashboard.spec.ts；部署：Dockerfile、.dockerignore、railway.json、web/vercel.json、scripts/container_smoke.py、scripts/check_deployment.py、.github/workflows/test.yml；文档：本文件及README/API_SPEC/ARCHITECTURE/PLANS/progress。

推荐：**本地面试开发演示 Go；现在公开上线与宣称真实Agent闭环 No-Go**。下一步是你审阅Module 1、确认平台/计费及秘密配置和发布权限。本轮到此停止，不推进Module 2/3。

最终补验：HTTPS VITE_API_BASE_URL构建及产物引用通过，HTTP地址被构建配置拒绝；同源本地构建已恢复。容器HTTPS来源CORS预检通过。Dify只读离线预检exit 2，实际三项DIFY变量缺失，未执行远端请求。
