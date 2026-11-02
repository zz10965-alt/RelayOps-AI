# Dify Workflow 设计
## 节点
Start(case_id, execution_token, order_id, description, image file) → Vision LLM(仅提取 damaged/product_match/image_quality/confidence/summary/order_id) → HTTP resolve → End(result)。HTTP resolve 先查订单/政策，再校验模型结构与业务规则，创建后回读。节点失败由调用方捕获并转人工。
模型输出 JSON，不依赖模型宣称任务成功。structured extraction 失败转人工。工具 body 使用 llm.text 字符串，避免未转义 JSON 插值；HTTP 变量放在字符串字段中由 Dify 渲染。
## 兼容与验证状态
DSL 目标 Dify 1.x Workflow 格式，具体 provider/model 导入后配置。YAML 生成与结构校验不等于导入成功；部署版本未知，必须在目标实例导入并运行视觉节点后才能声称兼容。
## 配置
Dify 应用环境变量 BUSINESS_API_URL（可从 Dify 网络访问的后端 base URL）、BUSINESS_API_TOKEN（服务端 DIFY_TOOL_TOKEN 相同）。API 服务 DIFY_BASE_URL 指向 /v1、DIFY_API_KEY 为 Workflow app key。工具仅接受运行中案件的 execution_token。
Dify file upload 返回文件 id 后以 local_file 输入，模型 vision enabled；禁止使用前端或静态结果替代真实模型。
## 外部验收
导入→选择视觉模型→配置工具 URL/secret→发布 Workflow→服务端安全注入 app key→上传真实照片→检查 Dify run_id、trace、returns 回读；每一项分别记录证据。

## Phase 4 Cloud准备修订
Cloud导入优先workflows/relayops.ifpkg；裸DSL维持0.3.0候选。官方源码版本0.7.0不是Cloud部署版本证据。实际图为Start→订单商品GET→政策GET→视觉原生Structured Output→完整JSON序列化→resolve→End。视觉模型候选gpt-4.1-mini已有官方插件源码证据。所有HTTP带Bearer，ssl_verify=true，timeout使用connect/read/write；HTTPS地址默认.invalid，不能误连本机。导入/配置步骤与限制以DIFY_SETUP_GUIDE.md为准，历史文本中的纯提示词输出已升级为原生Schema，但后端继续独立校验。

## 当前部署候选说明（2026-11-02）
前述OpenAI/native Structured段落为历史方案。当前包保持65aa556的官方DeepSeek/deepseek-flash、Vision、json_object与严格JSON解析，未启用原生Structured Output；实际节点/失败分支详见DIFY_PACKAGE_CHANGES.md。后端现已支持早期补清晰照片handoff提示，但不从workflow文本创建申请。真实Cloud兼容性与模型执行仍待验收。
