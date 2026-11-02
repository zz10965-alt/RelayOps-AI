# Module 1 最终交付前复核（2026-11-02）

## 结论

**GitHub源代码提交候选：Go，等待用户审阅和另行授权推送。** 本地实现、依赖安装、类型/生产构建、Python/浏览器回归及Docker部署候选已验证。

**Railway/Vercel：代码与受保护的部署配置已准备好；实际部署验收尚未发生。** 只有用户确认账户、计费、环境变量、持久卷及发布权限后，才能进行部署。**真实模型闭环及公开面试运行：No-Go**，Dify凭据、Cloud工作流兼容性、HTTPS回调和真实图片三场景尚未验证。不能把准备就绪称为已部署或Module 1全部完成。

本轮无commit/push、无公开端口、无付费服务、无生产秘密改动、无真实模型执行、无Module 2/3开发。原有开发数据库未删除或迁移。所有本轮容器验证均使用专属临时卷，结束后清理。

## 73 / 79 / 92 / 97 和27项改动的调查

- GitHub `git ls-remote origin refs/heads/main` 只读核对为 `65aa556cbc3bb87af037fcc20a3ba320fa2f00c4`，与本地基线一致。
- 将该提交源码归档到 `/tmp/relayops-review-baseline`，独立运行完整Python套件：**73 passed**。没有建立Git worktree或修改原checkout。
- 本轮开始工作区：**79项Python测试、21个变更文件**。73个基线测试全部存在；上一轮增加5个Module 1测试及1个Workflow补图契约测试，故为79。
- 本轮先补13项部署/异常回归，一度实际得到92；之后发现真实验收脚本不支持受保护部署，再补5项来源/凭据测试，**最终97 passed**。这次得到92的中间结果，不证明它等同先前未知报告中的92。
- 对比最终收集的完整测试node ID：基线73项，当前97项，**删除0项，新增24项**；其中上一轮6项、本轮18项。完整node ID和受保护文件哈希见 `predeployment-evidence.json`。
- 本地可见历史仅3个提交；reflog及`git fsck --no-reflogs --unreachable`未提供另一份92测试/27文件版本。不能据此断言历史文件被删除，也不能声称恢复了另一工作区。本轮开始时的21项改动完整保留并继续修复，未reset、stash覆盖或删除文件。
- 最终相对基线是**29个文件：18个修改、11个新增**，准确列表在下方。这是当前真实状态，不应为了匹配27而删除或补造文件。如有另一工作区的部署diff，需要后续提供其非秘密文件后合并审阅。

## 保留与修复

保留：原有订单/商品/政策查询、图片校验、Dify上传/运行协议、DeepSeek视觉JSON工作流、严格证据分流、确定性业务规则、幂等申请、独立SQLite读回、人工交接、指标与响应式Dashboard。原始73个测试无丢失，独立基线与最终套件均通过。

11个工作流/依赖/已有部署模板文件逐字节与基线一致，包括整个 `workflows/`、生成器、Python锁文件/声明、前端package/lock及Nginx模板。DeepSeek包SHA256仍是 `1b186b3e9966672f61c1e2f081f4a9d439dec65875010b5d9d9c64e771aa1bff`。

本轮修复：

1. **跨域错误不可读**：CORS改为包裹鉴权、执行开关、请求大小和限流中间件。容器实际验证允许来源的401响应具有正确CORS头，预检也通过。
2. **流式请求限制不可靠**：移除对私有Request接收函数的替换；ASGI中间件在JSON/multipart解析前限制声明长度与实际累计字节。超限413、负Content-Length 400，流式超限有回归。
3. **配置校验漏洞**：持久库路径按resolve后的真实路径验证，拒绝`/data/../tmp`逃逸；CORS限定无userinfo/query/fragment/path/通配符的HTTPS origin，并检查有效端口。公网工具token必须至少32字符且与操作者token不同；`.env.*`默认忽略，保留可提交的`.env.example`。
4. **非ASCII案件凭据导致500**：常量时间比较改为字节比较，无效Unicode凭据返回401。
5. **并发回调状态竞争**：公网resolve路由在现有单进程事件循环中同步执行短事务、不在规则判断与写回之间await，避免两个线程用同一旧running状态分别决策。保留原有唯一约束、重试语义与后端独立回读。此设计仅用于单worker Demo，不宣称分布式并发保证。
6. **异常Dify run ID可让后台任务卡在running**：在SQLite写入前校验类型/长度；列表/字典等异常响应安全handoff并清除execution token。
7. **真实验收脚本无法用于公网鉴权**：`live_e2e.py`改为可导入的main，从保护环境读取两个不同用途的token；案件用操作者凭据、申请读取用工具凭据；远程只允许HTTPS origin并保留代理/TLS；执行开关未允许时，在提交前阻止验收。只运行了帮助和本地契约测试，未实跑模型。
8. **UI未说明执行关闭**：health提供开关状态；前端明确提示并禁用提交，不改变后端默认403。新增浏览器UI契约回归。
9. **CI与文档**：增加Docker构建/本地容器验证步骤、只读GitHub权限和15分钟超时；修正DeepSeek文档中的历史OpenAI/适配器状态歧义。远端CI尚未执行。

## 实际检查与边界

所有工作目录默认 `/workspace/RelayOps-AI`；源码候选使用 `/tmp/relayops-submission-candidate`。

| 检查 | 命令 | 结果/边界 |
|---|---|---|
| 基线Python | 在基线归档目录用 `/workspace/RelayOps-AI/.venv/bin/python -m pytest -q` | 73 passed，1既有warning |
| 最终Python | `.venv/bin/python -m pytest -q` | **97 passed，1既有Starlette/httpx弃用warning**；含本地业务/协议替身测试，不是模型实跑 |
| 独立候选Python | 在源码候选目录用同一已装依赖解释器运行pytest | 97 passed；无原checkout源文件路径依赖 |
| TypeScript/Vite | `npm --prefix web run build` | 通过 |
| 独立前端安装/构建 | `npm --prefix /tmp/relayops-submission-candidate/web ci --no-fund`；其下`run build` | 锁文件安装、生产构建通过；Python依赖复现另由Docker锁文件安装验证 |
| API来源构建 | `VITE_API_BASE_URL=https://backend.example.com npm --prefix web run build -- --outDir /tmp/relayops-https-build` | HTTPS接受；相同命令用HTTP地址被拒绝；本地web/dist仍为同源构建 |
| Chromium | `npm --prefix web run test:e2e` | **4 passed**：3项真实本地FastAPI/临时SQLite流程；1项health响应替身UI契约，测试关闭执行时按钮禁用；无模型替身成功页面 |
| Docker | `docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt -t relayops-module1:local .` | 最终镜像构建通过，TLS验证保持开启 |
| 容器 | `.venv/bin/python scripts/container_smoke.py` | PORT8123、health、CORS预检及401错误CORS、匿名401、默认执行403、新订单、`/data`卷重启持久化通过；不发布端口 |
| 静态部署/包检查 | `.venv/bin/python scripts/check_deployment.py`；`.venv/bin/pip check` | 通过；浏览器bundle未发现服务端秘密标识/测试token；不是所有未知秘密格式的完整扫描 |
| npm公告 | `npm --prefix web audit --json` | 0条已知公告，不代表依赖绝对安全 |
| 文档/差异 | `.venv/bin/python scripts/check_docs.py`；`git diff --check` | 通过 |
| Dify离线预检 | `.venv/bin/python scripts/dify_preflight.py` | exit2/BLOCKED，三个DIFY变量缺失，无远端请求；不能称连通性通过 |
| GitHub CI | 未推送，未执行本轮远端CI | 仅本地候选验证 |
| Railway/Vercel部署 | 未执行 | DNS/TLS、平台实际挂卷、生产域名CORS仍待验收 |
| 实际Dify/DeepSeek | 未执行 | 未验证Cloud导入、模型图像理解、真实回调或真实费用 |

常见私钥/GitHub-token模式扫描未在变更交付文件中发现匹配；不输出任何匹配值，不替代平台秘密管理。没有运行新的Python漏洞数据库扫描，pip check仅证明依赖无冲突。

## 需要用户按顺序执行的事项

1. 审阅本报告、29文件diff及原有6分钟面试脚本 `docs/module1-review.md`。如另有27文件版本，先提供其非秘密diff核对；当前仓库没有可恢复证据。
2. **GitHub批准点**：明确授权提交/推送后再交付；本轮未建立commit、未push。推送后检查新的完整CI，包括Docker步骤；本地通过不等于远端CI绿色。
3. **服务与计费批准点**：确认Railway/Vercel账户、额度和费用后才可创建服务。Railway用根Dockerfile、单副本单worker、持久卷`/data`；不要为了启动而关闭`RELAYOPS_PUBLIC_DEMO`保护。
4. **保护配置**：Railway配置`RELAYOPS_DB=/data/relayops.sqlite3`、高熵且至少32字符的`RELAYOPS_DEMO_TOKEN`、精确HTTPS `RELAYOPS_CORS_ORIGINS`。保留`RELAYOPS_ALLOW_MODEL_EXECUTION=0`或不设置。Vercel根目录`web`，公开变量仅`VITE_API_BASE_URL=https://后端域名`，不放任何key/token。
5. **公开部署批准点**：得到明确批准后才部署。验证真实HTTPS、CORS允许/拒绝来源、401/403和卷重启；本机Docker验证不是云平台验收。
6. 按 `DIFY_SETUP_GUIDE.md` 在专用测试Workflow核实现有DeepSeek包/Provider/vision，配置`BUSINESS_API_URL`为实际后端HTTPS、`BUSINESS_API_TOKEN`为工具token。后端安全设置`DIFY_BASE_URL=https://api.dify.ai/v1`、该Workflow的`DIFY_API_KEY`和不同于操作者token且至少32字符的`DIFY_TOOL_TOKEN`。不要在聊天中发送秘密。若在当前Cloud发起调用，还需要放行`api.dify.ai`；Railway网络另行验证。
7. 用保护环境运行`.venv/bin/python scripts/dify_preflight.py --check-api`只读验证应用协议；未运行的检查不能算通过。
8. **模型执行与预算批准点**：你确认费用并明确批准受控运行后，才设置`RELAYOPS_ALLOW_MODEL_EXECUTION=1`。只允许私有操作者，不匿名开放、不取消限流。
9. 准备真实破损白色陶瓷杯照片和模糊/无关照片；分别生成新eligible、eligible、expired/shipping订单，真实运行A/B/C。确认A真实created并读回，B人工/补图，C后端拒绝且无申请。保留实际run ID、trace、截图与费用元数据，不能用HTTP契约测试替代。
10. 若使用脚本，在运行端安全注入`RELAYOPS_DEMO_TOKEN`和`DIFY_TOOL_TOKEN`，再运行 `scripts/live_e2e.py --api https://后端域名 --order 新订单号 --image /path/to/real-image.jpg`。不要把token作为CLI参数。后端同一卷使用 `scripts/verify_case_db.py --db /data/relayops.sqlite3 --case 实际ID` 独立核验；B/C独立查询returns确认没有对应申请。
11. 保存真实部署和模型验收结果后再决定Module 1最终通过。单操作者共享token、进程内限流、无持久队列/多租户/退款接口仍是已知边界；重启中断任务转人工。Module 2/3继续等待单独批准。

## 相对65aa556的精确文件清单

以下29个路径全部保留在工作区，未推送；18个已跟踪修改、11个新增。各自M/A状态见机器可读的 `predeployment-evidence.json`。

- `.dockerignore`
- `.env.example`
- `.github/workflows/test.yml`
- `.gitignore`
- `API_SPEC.md`
- `ARCHITECTURE.md`
- `DIFY_PACKAGE_CHANGES.md`
- `Dockerfile`
- `PLANS.md`
- `README.md`
- `backend/app.py`
- `docs/module1-review.md`
- `docs/predeployment-evidence.json`
- `docs/predeployment-review.md`
- `progress/build-log.md`
- `progress/test-report.md`
- `railway.json`
- `scripts/check_deployment.py`
- `scripts/container_smoke.py`
- `scripts/live_e2e.py`
- `tests/test_integration.py`
- `tests/test_module1.py`
- `tests/test_predeployment.py`
- `web/e2e/dashboard.spec.ts`
- `web/src/main.tsx`
- `web/src/style.css`
- `web/vercel.json`
- `web/vite.config.ts`
- `workflow_design.md`
