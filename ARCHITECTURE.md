# 当前统一双模式架构

```mermaid
flowchart LR
 Public[同一静态React URL / 默认Simulation] --> Sim[纯浏览器确定性fixtures与内存Map]
 Operator[同一React / 私有Live连接] -->|运行时HTTPS origin与操作者Bearer| Tunnel[临时HTTPS隧道]
 Tunnel --> Local[Windows FastAPI + SQLite]
 Local -->|服务端App Key| Dify[Dify Cloud + DeepSeek Vision]
 Dify -->|工具Bearer + 案件token| Tunnel
 Local --> Verify[独立SQLite读回]
```

前端DataClient将Simulation与Live隔离。默认模式不调用后端；模拟记录SIM-ID和合成时钟不可解释成真实执行。Live配置和token仅内存，验证后端保护模式与操作者权限后才切换；失败明确断线，不自动替换成模拟。刷新清除连接，断开中止在途请求，React重建模式界面避免跨模式迟到响应。

本地后端通过RELAYOPS_LOCAL_LIVE=1允许绝对Windows数据库路径，但仍强制RELAYOPS_PUBLIC_DEMO=1、独立token、限流、执行门槛和既有幂等/读回。静态首页/编译资源可匿名访问，不开放业务记录。生产HTTPS网页仅能连接HTTPS后端；HTTP loopback仅用于本地开发。

Railway/Vercel原配置逐字节保留为可选架构，不属于当前$0持续托管主方案。详细边界和手动步骤见docs/unified-demo-guide.md。以下保留既有Live系统架构说明。

# 系统架构
```mermaid
flowchart LR
 UI[React Dashboard] --> API[FastAPI 案件服务]
 API -->|上传图片 / workflows/run| Dify[Dify Workflow + 视觉模型]
 Dify -->|鉴权 HTTP POST /api/tools/resolve| API
 API --> DB[(SQLite 模拟业务与执行日志)]
```
浏览器同源 /api；Vite 开发代理与生产静态服务均连接 FastAPI。密钥不进入前端。
单进程 Demo：SQLite WAL + unique(order_id) 实现幂等，后台任务执行 Dify，异常归档人工。后台任务不跨重启持久排队，启动时将中断任务转人工，避免虚假成功。
Dify 负责多模态提取和工具编排；后端负责确定性政策校验、原子写入和回读；模型不可直接写申请状态。
表：orders、products、returns、cases、events。cases 存提取与结果；events 存调用耗时、成功/参数校验和错误；不存密钥/原始图片到 trace，图片仅用于 Dify 上传。
信任边界：Dify 工具 Bearer token；case_id 与工作流运行绑定的一次性随机执行 token；用户图片和模型输出均校验，不接收客户端传入政策/订单事实。前端无公网认证，部署前必须加身份验证与权限控制。

## Module 1部署候选更新
保留同源本地开发；Vercel独立前端通过公开的VITE_API_BASE_URL连接Railway后端，显式HTTPS CORS，不把服务端秘密编入浏览器。Railway Docker读取PORT、单worker，SQLite卷/data。公网模式采用私有操作者Bearer与独立工具Bearer，并默认禁止案件执行。单进程限流不是分布式配额系统。未进行真实云部署；部署与人工步骤见docs/module1-review.md。
