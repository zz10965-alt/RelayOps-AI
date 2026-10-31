# Dify Cloud 设置：DeepSeek 修订版

当前包已切换为官方DeepSeek/deepseek-flash，旧OpenAI原生Structured Output设置不再适用。详细模型证据、节点图、失败处理、验证和限制见[DIFY_PACKAGE_CHANGES.md](DIFY_PACKAGE_CHANGES.md)。本次没有修改前端/业务API或对外发布。

## 导入与模型

用户已确认DeepSeek已安装并配置，模型列表存在支持VISION的deepseek-flash；不需要重复安装OpenAI。Codex从官方插件源码核实provider标识为langgenius/deepseek/deepseek，模型为deepseek-flash。源码支持vision与json_object，未声明structured-output，所以包关闭原生Structured，采用严格JSON Code校验。

1. Studio → Create → Import App导入本地新版workflows/relayops.ifpkg到专用测试Workflow；若更新已有应用先导出备份，避免覆盖其他工作。
2. 记录实际Cloud导入/迁移提示；本包DSL标签保持0.3.0，不伪称Cloud版本。应用包manifest格式已本地核验，不代表账号已导入成功。
3. 视觉节点选择你已配置的官方DeepSeek/deepseek-flash。确认Vision开启、图片变量Start.image，JSON模式json_object、thinking=false，原生Structured关闭。
4. Start.image为必填单文件，上传及image功能启用，仅local_file PNG/JPEG/WebP。不要将图片仅附在描述文字而忽略image字段。

## 变量与HTTPS

| 名称 | 所在位置 | 用途 |
|---|---|---|
| BUSINESS_API_URL | Dify Workflow环境变量，导入后为空 | 你控制的Cloud可达HTTPS origin，不含尾部/api |
| BUSINESS_API_TOKEN | Dify Workflow Secret，导入后为空 | 同后端实际DIFY_TOOL_TOKEN |
| DIFY_BASE_URL | 后端安全环境 | https://api.dify.ai/v1 |
| DIFY_API_KEY | 后端安全环境 | 本Workflow App API Key，非DeepSeek Key |
| DIFY_TOOL_TOKEN | 后端安全环境 | 实际高熵秘密，用于恒时比较工具鉴权 |
| DeepSeek provider Key | 你已配置的Dify Provider安全设置 | 只供Dify调用模型，不填入包或聊天 |

BUSINESS_API_URL不由现有后端适配器消费；后端同名值只是可选预检镜像。空地址会走人工分支，不访问.invalid或localhost。现有出站网络还需允许api.dify.ai；这与Dify反向调用API是两个方向。

API仅loopback监听，不能被Cloud访问。你需要另行授权并配置自己的HTTPS测试主机/持久磁盘/有效公共证书/受限网关；不得裸露整个开发服务。deploy/dify-callback.nginx.conf.example只是未部署、未运行nginx -t的模板。只公开带鉴权的订单/政策GET与resolve POST，不公开UI、docs、cases、metrics或数据库。不假定Cloud固定出口IP。

## 节点测试与首次E2E

先单测只读订单/政策HTTP，再测试真实损坏照片、模糊照片和商品不匹配照片。仅eligible证据路径进入resolve；模糊分支请求补图并交接，错误/低分转人工。Studio整图测试不能随便填写case_id/execution_token，它们必须由后端生成。

检查节点后，由你在测试应用点击Publish，并从该应用API Access / Service API → API Key获取App Key，安全注入后端。此次Codex没有替你发布。凭据和HTTPS可达后，在实际API主机、现有仓库根目录执行：

```bash
.venv/bin/python scripts/dify_preflight.py
.venv/bin/python scripts/dify_preflight.py --check-api
# 仅在没有现有实例时启动；配置变化应通过既有进程管理重启：
.venv/bin/uvicorn backend.app:app --host 127.0.0.1 --port 8000
# 另一个终端，使用真实清晰损坏白色陶瓷杯照片：
.venv/bin/python scripts/live_e2e.py --image /absolute/path/to/photo.jpg
.venv/bin/python scripts/verify_case_db.py --db .data/relayops.sqlite3 --case ACTUAL_CASE_ID
```

预检默认不联网、不打印秘密，--check-api仅只读检查App与字段，不调用模型。完整成功必须有真实run_id、后端return_verify、created申请以及独立SQLite匹配；创建不等于批准或退款。

注意既有适配器不消费早期非执行分支的详细输出：无resolve回调时会安全进入后端通用handoff，具体拒绝/补图原因见Dify执行记录。本次未改该行为。正常请求仍依赖后端政策、幂等与独立数据库回读。Cloud导入/视觉/E2E未实测，不将本地73项测试当成远端成功。

用户后续已明确授权将新版包及相关修改上传原GitHub仓库。下载时使用main分支当前版本；历史提交仍包含OpenAI旧包。此授权不包含Dify部署或发布。
