> 当前双模式本地结果：99 Python、8 Chromium通过；详见[统一指南](../docs/unified-demo-guide.md)。以下97/79等为既有阶段记录。

> 最新预部署复核：97 Python passed、4 Chromium passed；详情见 [最终报告](../docs/predeployment-review.md)。以下73/79等数字为各阶段历史结果。

# 实际测试报告 — 2026-10-30

最新DeepSeek包回归：**73 passed / 1既有依赖warning**。此前45项和Chromium结果为历史证据；本次业务API/React源码不变。真实Dify始终未执行。

## 本地已执行
| 检查 | 实际结果 | 能证明的范围 |
|---|---|---|
| `.venv/bin/python -X faulthandler -m pytest -q` | 35 passed，1 warning，1.04s | SQLite业务读写/商品/政策、幂等、鉴权、输入、失败与恢复、Dify HTTP契约、DSL图与转义 |
| `npm --prefix web run build` | tsc通过，Vite 6.4.5成功构建 | 类型与生产包；不证明模型运行 |
| `npm --prefix web run test:e2e` | 2 passed，2.4s | Chromium→真实FastAPI/SQLite；缺资料、无Dify转人工、trace、metrics、人工队列、移动布局 |
| `.venv/bin/python scripts/http_smoke.py` | PASS | 实际HTTP健康、生产页面、订单/政策、持久化缺资料任务、指标 |
| `bash scripts/install.sh` | exit 0 | 全锁依赖重装、npm ci、build、pip check的重复执行 |
| `scripts/check_docs.py` / compileall | PASS | 9份文档与原文长度、Python语法 |
| `npm audit --json` | 0 vulnerabilities | 当前npm数据库公告检查；不是安全保证 |

后端warning：Starlette建议未来迁移httpx2测试客户端；现有httpx协议测试通过，未隐藏warning。浏览器有NO_COLOR/FORCE_COLOR环境提示，不影响断言。

## 测试范围与合成数据
所有模型字段与Dify返回值仅在tests内使用替身，运行时没有假模型分支。正常创建场景在本地测试中由鉴权resolve执行真实SQLite写入、独立连接回读；模型对真实照片的判断尚未验证。浏览器测试会生成独立临时DB并清除其子进程Dify配置，不污染开发DB。白色PNG为合成夹具，不是商品损坏证据。

## 发现并修复
- 初次浏览器测试1 passed/1 failed：损坏PNG的CRC触发SyntaxError→500。补充422处理和回归测试，换有效夹具，重测通过。
- 全npm审计最初3项开发依赖高危条目：升级Vite6.4.5、Playwright1.64.1后复查0项。未关闭TLS、未使用受影响浏览器下载功能。
- 重复订单统计曾按完成任务数累计申请；改为returns表唯一记录数，并加断言。
- 异常Dify上传/运行/metadata类型均保留失败证据并转人工。

## 未执行 / 阻塞
- 真实Dify导入、具体版本兼容、模型图片输入、工具远端回调与真实E2E：未执行，缺部署地址/版本/模型/凭据/可达回调配置。
- 模糊/无关照片的真实识别效果与准确率：未测；单元测试仅验证字段到规则的分支。
- GitHub Actions：配置已写，远端未运行；未推送GitHub。
- Cloud草稿已保存install_script/start_skill；未发布、未验证新任务恢复。
- live_e2e.py仅执行过--help，未执行真实验收；不得把它当通过证据。

## 截图
[本地真实空数据库Dashboard](../docs/dashboard.png)：浏览器测试截图，无预置成功任务，仅展示UI与缺配置提示。

## Phase 4 Cloud准备回归 — 2026-10-30
`pytest -q`：42 passed，1 Starlette/httpx弃用warning，1.23s。保留既有业务与适配器测试，新增包manifest完整性、原生Schema/完整JSON序列化、配置预检不泄密、HTTPS占位地址拒绝与只读SQLite核验测试。预检实际运行exit2/BLOCKED，因为三个DIFY_*缺失；无外部请求发生。这不是Dify连通性通过。真实Cloud导入、模型、HTTPS回调及E2E仍未运行。

既有浏览器回归：2 passed，3.8s；冻结前端9个源/配置文件逐字节一致。Nginx模板未部署且未语法实测；不将模板当作HTTPS可达证据。

最终扩充私网/IPv6回环URL预检后，全套45 passed，1 warning，1.30s。无外部服务调用、导入或部署证据。

## DeepSeek应用包本次回归
73 passed / 1既有依赖warning（2.21s），包含原业务测试、严格JSON与证据分流、错误HTTP/数据库回读证据、包manifest/CRC/SHA256。业务API/React源码哈希一致。真实Cloud导入、图片模型调用与E2E未执行；本次没有推送，GitHub仍是旧包。

## Module 1 / Phase 7
本轮本地Python79 passed（1既有依赖warning）、Chromium3 passed、tsc/Vite build、pip check、部署静态检查通过。本地Docker镜像构建和PORT/鉴权/默认禁执行/临时卷重启读回通过。HTTP替身契约不能证明模型执行；远端CI、实际部署和Dify/DeepSeek均未验证。命令、失败修正及边界见 [Module 1报告](../docs/module1-review.md)。

最终补验：HTTPS VITE_API_BASE_URL构建及产物引用通过，HTTP地址被构建配置拒绝；同源本地构建已恢复。容器HTTPS来源CORS预检通过。Dify只读离线预检exit 2，实际三项DIFY变量缺失，未执行远端请求。

## 统一双模式当前本地验证（2026-11-03）
- `.venv/bin/python -m pytest -q`：99 passed，1既有Starlette/httpx弃用warning。
- `npm --prefix web run build`：TypeScript与Vite通过。
- `npm --prefix web run test:e2e`：8 passed，首轮1个旧默认模式假设失败已修正；包括独立静态页面/断网模拟/无浏览器API/未改真实DB、实际本机跨域认证和无自动回退；一项health响应为UI契约替身。
- `.venv/bin/python scripts/check_deployment.py`、`pip check`、`scripts/check_docs.py`和`git diff --check`通过。
- Docker构建（保留代理CA/TLS）和`container_smoke.py`通过，无对外端口，临时卷清理。
- 真实Windows、HTTPS隧道、公开静态平台、Dify/DeepSeek模型均未执行；verify #4是a9d07a1历史结果，不是当前未推送代码的CI。
- 安全/预算/手动步骤见 [双模式指南](../docs/unified-demo-guide.md)。
