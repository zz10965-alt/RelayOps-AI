# API 规范
所有业务数据为合成模拟数据；OpenAPI /docs 是字段级规范。
- GET /api/health：DB 可用与 Dify 是否配置（不返回密钥）。
- GET /api/orders/{id}（含商品信息）、GET /api/products/{id}、GET /api/policy：模拟事实。
- POST /api/cases multipart(order_id, description, image?)：202 入队；缺资料直接 needs_information；无 Dify 配置转 handoff，绝不伪造分析。
- GET /api/cases、GET /api/cases/{id}：任务、订单、提取、trace、申请实际状态。
- POST /api/tools/resolve：Bearer 工具鉴权，case_id+execution_token+analysis 字符串；running 案件校验后查询、创建、回读。重试同案返回幂等结果。
- GET /api/returns/{id}：数据库读回 created 状态。
- GET /api/metrics：真实日志统计、样本数、口径、unknown 成本。
400/422 无效字段，401 错误工具密钥，404 不存在，409 非法状态，413 图片过大；Dify 超时/错误保留安全错误并转人工。
数据库路径 RELAYOPS_DB（默认 .data/relayops.sqlite3），最大图片 5MiB。没有用于任意批准/退款的端点。

## Module 1扩充
- `POST /api/demo/orders` JSON `{ "scenario": "eligible" | "expired" | "shipping" }`：201新鲜合成白色陶瓷杯订单，随机ID，不修改旧订单。
- 案件详情新增 `stages`：Understand/Retrieve/Decide/Act/Verify，各自status/events，仅基于实际后端事件，not_observed不表示成功。
- 公网候选模式：health匿名；案件/指标/新订单需要操作者Bearer；订单/商品/政策/申请/resolve使用工具Bearer。resolve仍需案件execution_token。
- `RELAYOPS_PUBLIC_DEMO=1` 时验证私有token、HTTPS CORS与/data路径；`RELAYOPS_ALLOW_MODEL_EXECUTION`默认不启用，案件POST返回403。详细限制见docs/module1-review.md。
