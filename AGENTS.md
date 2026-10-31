# RelayOps AI 开发规范
以 docs/project-instructions.md（用户提供的总指令）为主要产品要求。
每阶段开始阅读本文件、PLANS.md、progress/build-log.md；阶段结束运行测试、记录真实结果并继续未受阻工作。
使用现有隔离 checkout，不创建 worktree。不覆盖用户工作，不擅自发布或推送。
采用 FastAPI、SQLite、React/TypeScript 和真实 Dify Workflow；测试替身只能出现在测试中。
禁止把模型建议当执行成功：退货申请 created、approved、completed 必须区分；创建后重新查询验证。
密钥仅服务端环境变量，禁止提交。边界输入校验、超时、有限重试、幂等、人工交接和日志脱敏必须保留。
外部服务未验证时明确报告，禁止编造准确率、成本和测试结果。
