# 实际测试报告 — 2026-10-30

最新Phase 4准备回归：**45 passed / 1依赖warning（1.30s）**，既有Chromium **2 passed（3.8s）**。下方保留此前阶段的历史证据；真实Dify始终未执行。

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
