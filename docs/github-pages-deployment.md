# GitHub Pages：Module 1免费静态站部署准备

## 当前结论

本轮基于 `d876ee5d202539e19ec2047580407ac8c4dc90b4` 本地实现，未commit/push、未开启Pages、未发布网页。**本地准备Go，等待用户审阅；推送与发布分别需要明确授权。** 真实公网Pages、Windows HTTPS隧道和Dify/DeepSeek尚未验收。

预计公开地址（尚未发布，不把它当可用Demo）：

```text
https://zz10965-alt.github.io/RelayOps-AI/
```

保留英文React Dashboard、纯浏览器Public Simulation和认证Private Live；不开始Module2/3。没有付费服务、秘密变更、数据迁移或模型调用。

## $0适用条件

已读取GitHub官方文档源码：Pages支持GitHub Free的公开仓库，私有仓库可用性取决于付费计划。使用现有公开仓库和标准`ubuntu-latest` Actions runner；不购买Pro、付费runner、域名、数据库或后端。

- [Pages说明](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [免费可用性官方源码](https://github.com/github/docs/blob/main/data/reusables/gated-features/pages.md)
- [Pages使用限制](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)

用户仍须在控制台确认账户资格/仓库可见性和当前限制。如果界面要求升级或付费，停止，不自动付费，也不擅自改变仓库可见性。Pages用于个人作品演示，不作为电商支付、真实客户业务或敏感数据网站。静态站无后端托管成本；Dify/DeepSeek真实调用费用与本方案分开，默认不发生。

## 构建与发布设计

| 用途 | 命令 | base | 产物 |
|---|---|---|---|
| 现有本地/Vercel/其他根路径静态站 | `npm --prefix web run build` | `/` | `web/dist` |
| GitHub Pages项目站 | `npm --prefix web run build:pages` | `/RelayOps-AI/` | `web/dist-pages` |

Vite仅在`github-pages`模式应用项目base。两个产物互不覆盖，Pages目录忽略于Git，不提交编译输出。根目录方案、Railway、Docker、Dify文件保留。

`.github/workflows/pages.yml`：

- 只有`workflow_dispatch`，没有push/PR自动发布。
- 只允许main构建；安装Node24、Python3.12（仅用于标准库静态测试服务器），从`web`执行`npm ci`、`build:pages`和`test:pages`。
- 不启动FastAPI、不安装后端依赖，不使用Dify/DeepSeek/token环境变量；仅上传`web/dist-pages`。
- build权限仅contents:read、pages:read；deploy仅pages:write、id-token:write，使用GitHub内置令牌/OIDC，无需新增PAT或仓库secret。
- deploy依赖build成功，绑定`github-pages` environment，使用官方configure-pages/upload-pages-artifact/deploy-pages Actions。
- 现有verify工作流仍只做检查，新增Pages构建/子路径测试/静态检查，但不发布。

当前导航使用React内存状态，不产生`/case/...`等深层URL。首页和导航都保持在`/RelayOps-AI/`；刷新重置内存模拟记录。没有添加404.html或SPA fallback去掩盖坏路径。新增内联favicon，避免浏览器默认去根路径请求favicon造成404。

## 本地验证（不公开端口）

在仓库根目录：

```bash
.venv/bin/python -m pytest -q
npm --prefix web run build
npm --prefix web run test:e2e
npm --prefix web run build:pages
npm --prefix web run test:pages
.venv/bin/python scripts/check_deployment.py --pages
.venv/bin/python -m pip check
.venv/bin/python scripts/check_docs.py
git diff --check
```

Windows虚拟环境解释器改为`.venv\Scripts\python.exe`；Pages浏览器测试使用PATH中的`python`启动标准库服务器。测试用本机8004端口，不开放公网。

- Python：**99 passed**，1项既有Starlette/httpx弃用warning。
- 原Chromium：**8 passed**，原始测试未删除，保留实际本机跨域CORS/认证、Live离线无自动回退以及双模式隔离检查。
- Pages Chromium：**2 passed**。严格静态服务器仅服务`/RelayOps-AI/`，没有后端或fallback；JS/CSS均在项目assets路径并实际存在；无尾斜杠301跳转；首页刷新成功；离线完成模拟订单/图片预览/申请/五阶段/证据不足与超期拒绝/人工队列/评估，浏览器fetch/XHR为0。
- 第二项Pages测试仅用HTTPS协议fixture检查Live请求指向独立后端`/api/*`，不会错误附加`/RelayOps-AI/`；认证头、内存存储和退出模式检查通过。这不是实际隧道或模型运行。
- 部署检查验证资产引用、静态产物无服务端秘密标识/测试token、无数据库/缓存文件，以及手动main发布/最小权限契约。
- 根路径/Pages两种tsc+Vite构建、pip check、文档及diff检查通过。错误根路径资产测试有意返回404以证明服务器严格；实际应用资源不应出现404。

本轮只验证本地，既有GitHub verify成功仅对应d876ee5；当前改动未推送，不能声称新远端CI或Pages发布通过。

## 你需要执行的动作（按批准阶段分开）

### A. 当前只审阅

检查本轮diff与本文。此时不要点击Run workflow或更改Pages设置，不需要秘密，也不需要Railway、Vercel或Cloudflare项目。

### B. 明确授权推送后

1. 将本轮准备提交并非强制推送至现有main；不提交`dist`/`dist-pages`、数据库、`.env`、缓存。
2. 等待新verify全部通过，特别是原8项+Pages2项浏览器检查。本地通过不替代远端CI。
3. 这次push不会自动运行Pages发布工作流。

### C. 你另行明确批准公开发布后

1. 在GitHub仓库`Settings → Pages`确认资格，`Build and deployment → Source`选择 **GitHub Actions**，不要选Deploy from a branch，不建立gh-pages分支。
2. 不添加custom domain，不购买域名；无需添加Dify、DeepSeek、操作者或工具token，也不设置`VITE_API_BASE_URL`。
3. 如`Settings → Environments → github-pages`中已有保护规则，保留；若账户免费功能允许，可以配置required reviewer作为额外批准门槛。不要为了配置审核功能升级付费套餐。
4. 到`Actions → Deploy GitHub Pages → Run workflow`，选择main，确认此次确实获准公开发布后再点击。不要只运行旧的verify来期待网站上线。
5. build通过后deploy会上传静态站；如果environment要求审核，确认当前提交再执行Review deployments。没有审核时，手动Run workflow本身就会在构建成功后发布，不能把它当仅预览按钮。
6. 等待deploy job成功并查看该job提供的page_url。预计为`https://zz10965-alt.github.io/RelayOps-AI/`；首次发布/传播可能需要等待。没有实际成功记录前，不宣称网址已可用。
7. 用无痕窗口打开完整带尾斜杠的URL，确认默认SIMULATION；关闭本地后端与隧道，演示模拟新订单、照片预览、clear/blurry/expired、timeline、handoff和evaluation；开发者工具Network应无后端/模型API请求。
8. 检查刷新仍加载首页，JS/CSS在`/RelayOps-AI/assets/`，不要把裸站点根`https://zz10965-alt.github.io/`或未实现深链接当应用地址。

后续更新不会自动发布；每次需要在新verify通过、用户批准后再次手动运行Pages部署workflow。若仓库更名或改用根域名，需重新审阅base，不直接沿用本配置。

## Private Live与GitHub Pages的兼容设置

Public Simulation不需要任何后台设置。只有你私下演示Live时，按`docs/unified-demo-guide.md`启动受保护的Windows后端和经批准的HTTPS隧道。

| 配置 | 正确值/含义 |
|---|---|
| 网页地址 | `https://zz10965-alt.github.io/RelayOps-AI/` |
| 本地后端`RELAYOPS_CORS_ORIGINS` | **`https://zz10965-alt.github.io`**，不包含`/RelayOps-AI/`，不带末尾斜杠 |
| 网页私有Live backend origin | 当前实际tunnel的HTTPS origin，不带`/api`或项目路径 |
| Dify `BUSINESS_API_URL` | 同一个实际tunnel origin，绝不是github.io网址 |
| 操作者token | 只在私有连接表单输入，浏览器内存；不是Dify/DeepSeek key |
| 后端执行开关 | 保持`RELAYOPS_ALLOW_MODEL_EXECUTION=0`，除非你另行批准真实执行 |

CORS Origin只包含scheme+host(+port)，项目子路径只影响静态资源，不影响后端路由。Live请求继续发往`tunnel-origin/api/*`，token不进入GitHub URL、源码、构建、持久存储或第三方请求。真实HTTPS网页不会允许HTTP localhost混合内容，应使用HTTPS隧道；本地HTTP例外仅用于开发。

操作者认证、工具Bearer、案件execution_token、输入限制、幂等、SQLite独立读回与人工交接均未变。连接失败仍明确显示LIVE DISCONNECTED，不用Simulation冒充成功。网络、浏览器隐私政策或隧道拦截可能阻止实际连接，需用真实环境验收，不能关闭鉴权/CORS/TLS来解决。

## 剩余限制与停止点

- 未推送、未配置Pages、未触发发布，预计网址现在不能当成已发布链接。
- 未执行真实Windows/tunnel/Dify/DeepSeek，不能标记实际Agent闭环通过。
- 公共Simulation为浏览器会话数据；刷新清空，首次加载需互联网，不提供首次离线访问或持久业务数据库。
- 只有Module1可用，Module2/3仍Planned。
- 本轮停止等待用户审阅；后续提交、发布和模型执行均分开授权。

## 本轮精确变更清单

- `.github/workflows/pages.yml`
- `.github/workflows/test.yml`
- `.gitignore`
- `PLANS.md`
- `README.md`
- `docs/github-pages-deployment.md`
- `docs/unified-demo-guide.md`
- `progress/build-log.md`
- `progress/test-report.md`
- `scripts/check_deployment.py`
- `scripts/pages_preview.py`
- `web/e2e-pages/pages.spec.ts`
- `web/index.html`
- `web/package.json`
- `web/playwright.pages.config.ts`
- `web/vite.config.ts`
