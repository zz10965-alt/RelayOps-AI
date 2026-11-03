# Module 1中文UI/UX审阅

本轮以用户提供的四页设计图为视觉/布局参考，在a5e244f基础上本地实现。未复制参考图中的订单号、商品、7天规则或成功结果。图片中的业务数据不作为实现要求；实际30天政策、合成白色杯订单和真实后端状态保持原样。

## 页面与截图

截图由Chromium实际操作静态Simulation生成，不是设计稿拼图或真实模型运行证明。截图中的SIM订单、申请、证据、时间与置信度均来自现有确定性模拟引擎；页面持续标注模拟。没有任何真实客户数据或操作者凭据。

| 页面 | 截图 | 已实现 |
|---|---|---|
| 首页 | [01-home.png](01-home.png) | 深紫导航、产品介绍、主CTA、三模块卡片；仅Module1可体验，其余Planned/规划中 |
| 选择场景 | [02-workflow.png](02-workflow.png) | 四场景单选、三个引导步骤、现有业务条件说明 |
| 信息输入 | [02b-information.png](02b-information.png) | 订单生成/输入、描述、模拟fixture与本地图片预览；Live使用真实上传 |
| Agent执行过程 | [03-execution.png](03-execution.png) | 五阶段可选视觉时间线、真实记录状态、证据/判断双面板、可展开JSON和trace |
| 处理结果 | [04-result.png](04-result.png) | 从匹配创建/回读事件判定结果，展示依据、订单、申请和下一步 |
| 非自动处理 | [05-handoff.png](05-handoff.png) | 超期场景不创建申请；解释实际原因，不展示绿色成功结果 |
| 移动端结果 | [06-mobile-result.png](06-mobile-result.png) | 390px窄屏结果布局 |
| 移动端过程 | [07-mobile-execution.png](07-mobile-execution.png) | 小屏导航与五阶段时间线 |

## 交互与数据边界

- 首页→选择场景→补充信息→确认运行→执行过程→处理结果。没有假“2分钟视频”入口，次CTA是页面内的实际流程说明。
- 场景只选择输入条件；Live最终状态仍由真实模型与后端决定，不根据设计图或所选卡片预判成功。
- Simulation即时返回时直接显示已记录状态，不用假延时、假进度条或假“正在思考”。Live仅queued/running显示处理中。
- 时间线沿用Understand/Retrieve/Decide/Act/Verify的原有事件映射：模拟、成功记录、handoff、失败、未观测到分别呈现。点击节点仅改变查看阶段，不改变业务状态。
- 成功结果必须有application_created、created申请及匹配申请ID的成功return_verify事件；模拟仅称内存回读，不称SQLite验证。创建≠批准≠退货/退款完成。
- 无证据、缺资料、超期与外部失败保留人工/待补充说明，不以静态成功卡覆盖。
- 中文格式化仅是展示层；原始后端/模拟字段、JSON、ID、run ID、时间和拒绝原因可展开检查。未引入AI翻译或改写原始业务数据。
- 操作者连接窗口使用原DataClient认证，native dialog支持键盘、Esc和焦点恢复；口令仍仅内存。没有新增凭据、存储、依赖或接口。
- 深紫导航、浅色背景、卡片留白、统一线性SVG图标、本地中文字体栈，无外部字体/图片服务。首页插画只是流程示意，不是证据图片或成功记录。

## 测试与修正

| 检查 | 命令/结果 |
|---|---|
| 后端原有回归 | `.venv/bin/python -m pytest -q`：99 passed，1既有Starlette/httpx弃用warning |
| 根路径类型/构建 | `npm --prefix web run build`：通过 |
| 原有8项＋新增审阅测试 | `npm --prefix web run test:e2e`：9 passed |
| Pages构建 | `npm --prefix web run build:pages`：通过，base仍为/RelayOps-AI/ |
| Pages子路径回归 | `npm --prefix web run test:pages`：2 passed |
| 部署/包检查 | `scripts/check_deployment.py --pages`、pip check通过 |

保留原8项浏览器场景及2项Pages场景的业务、安全断言，更新中文选择器并按三步引导进入运行。覆盖真实本地后端缺资料/未配置Dify、fresh订单、鉴权/执行门槛、错误origin/token、跨域CORS、0API离线模拟、幂等、模拟不改真实库、断线无自动回退与秘密不入持久存储。新增测试验证参考四页、单选键盘操作、390px结果/过程无横向溢出，自动生成截图。连接Esc退出恢复焦点也有断言。

首轮一个标题选择器因中文可访问名称空格失败，已用语义匹配修正。移动端确有10px溢出，检查实际元素边界定位到导航按钮，改五列布局后通过，没有用overflow隐藏问题。

部署工作流、普通与Pages Vite base、DataClient、Simulation逻辑、后端/SQLite/DeepSeek、Railway/Vercel/Docker和锁文件保持不变。GitHub Actions与公开Pages尚未验证本轮修改；既有verify #6属于旧提交，不算当前代码CI。真实Windows、隧道和模型仍未验收。

本轮没有commit/push、没有发布/重新部署、没有执行真实模型，也没有开始Module2/3。请先审阅截图与交互，后续提交和部署仍分别等待授权。

## 首页插画质感补充

按用户对纸箱视觉的反馈，将首页线稿替换为原创生成的纸箱、封箱胶带、白紫机器人装饰插画。插画随Vite本地打包，不使用外部图床；约1.4MB。它没有与上传图片、损坏判断、业务证据或成功状态绑定。原有线性SVG继续用于导航和流程图标。

9项界面测试与2项Pages测试再次通过，新增检查PNG实际解码及/RelayOps-AI/assets下的正确加载；两种构建和部署检查通过。部署检查只为此静态PNG扩展允许类型，并校验PNG签名，原有秘密隔离检查保留。没有调用Dify/DeepSeek业务模型，没有推送或部署。01-home.png与截图包已更新。

## 本轮精确文件清单

- `PLANS.md`
- `README.md`
- `docs/ui-redesign/01-home.png`
- `docs/ui-redesign/02-workflow.png`
- `docs/ui-redesign/02b-information.png`
- `docs/ui-redesign/03-execution.png`
- `docs/ui-redesign/04-result.png`
- `docs/ui-redesign/05-handoff.png`
- `docs/ui-redesign/06-mobile-result.png`
- `docs/ui-redesign/07-mobile-execution.png`
- `docs/ui-redesign/README.md`
- `progress/build-log.md`
- `progress/test-report.md`
- `scripts/check_deployment.py`
- `web/e2e-pages/pages.spec.ts`
- `web/e2e/dashboard.spec.ts`
- `web/e2e/redesign.spec.ts`
- `web/e2e/support.ts`
- `web/index.html`
- `web/src/assets/README.md`
- `web/src/assets/hero-parcel-robot.png`
- `web/src/main.tsx`
- `web/src/presentation.tsx`
- `web/src/style.css`
- `web/src/vite-env.d.ts`
