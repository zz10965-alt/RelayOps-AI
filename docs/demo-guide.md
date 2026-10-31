# 演示脚本与真实验收

1. 安装并构建，启动 FastAPI，打开 Dashboard（在支持的本地浏览器环境）。初始统计为0/暂无样本，不是预置成功。
2. New Case 输入 DEMO-1001，不传照片和描述，查看 needs_information 与缺失项。
3. 未配置 Dify 时，传完整资料会进入 handoff，trace 明确显示 configuration 错误。这验证错误路径，不是 Agent 成功演示。
4. 按 README 配置并验证 Dify。使用清晰破损白色陶瓷杯照片提交 DEMO-1001，等待 application_created；检查 Dify run ID、模型提取、order_lookup、policy_lookup、return_create、return_verify；GET申请状态应为created。重复提交同订单不得增加申请记录。
5. 使用模糊或无关照片，或者 DEMO-1002/1003，检查人工交接原因。真实图像判断受模型表现影响，必须记录实际结果。
6. Evaluation 只展示本数据库日志；本地自动化测试DB独立，不能把测试用例通过率当线上模型准确率。单次费用没有Dify明确报价时显示未知。

未通过第4步前不能将项目描述为“已完成真实Dify端到端”。当前未进行远端发布、GitHub推送或目标实例导入。截图（如有）只代表本地UI，不证明模型能力。
