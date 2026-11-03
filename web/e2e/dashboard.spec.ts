import {test,expect} from '@playwright/test';
import {TOKEN,connect,startCase,runCase,showResult} from './support';

test('real backend dashboard, missing evidence, handoff, trace and metrics',async({page,request})=>{
 await page.goto('/');await connect(page);
 await expect(page.getByRole('heading',{name:/多模态电商运营智能体/})).toBeVisible();
 await expect(page.getByText('Dify尚未配置，未执行视觉分析。',{exact:false})).toBeVisible();
 await startCase(page);await page.getByLabel('订单号').fill('DEMO-1001');await runCase(page,true);await showResult(page);
 await expect(page.locator('.resolution')).toContainText('请补充：问题描述、商品照片');
 await expect(page.getByText('没有经过核验的申请',{exact:true})).toBeVisible();
 await startCase(page);await page.getByLabel('订单号').fill('DEMO-1001');
 await page.getByLabel('问题描述').fill('白色陶瓷杯损坏，需要售后');
 await page.getByLabel('商品照片',{exact:true}).setInputFiles('../tests/fixtures/evidence.png');
 await runCase(page,true);await showResult(page);
 await expect(page.locator('.resolution')).toContainText('Dify 未配置，未执行视觉分析');
 await page.getByRole('button',{name:'查看完整执行过程',exact:true}).click();
 await page.getByText('查看执行日志',{exact:true}).click();
 await page.getByText('configuration',{exact:true}).click();
 await expect(page.getByText(/Dify 未配置；未运行模型/)).toBeVisible();
 await page.getByRole('button',{name:'效果评估',exact:true}).click();
 await expect(page.getByRole('heading',{name:'真实运行评估'})).toBeVisible();
 const metrics=await (await request.get('/api/metrics',{headers:{Authorization:'Bearer '+TOKEN}})).json();
 expect(metrics.total_cases).toBe(2);expect(metrics.created_applications).toBe(0);expect(metrics.average_api_cost).toBeNull();
 await page.getByRole('button',{name:'人工处理',exact:true}).click();
 await expect(page.getByRole('heading',{name:'人工交接队列'})).toBeVisible();await expect(page.locator('tbody tr')).toHaveCount(2);
});

test('mobile navigation and readable layout',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await startCase(page);await expect(page.getByLabel('订单号')).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});

test('fresh scenario order and honest timeline',async({page})=>{
 await page.goto('/');await connect(page);
 await expect(page.getByText('规划中',{exact:true})).toHaveCount(2);
 await startCase(page);await page.getByRole('button',{name:'生成演示订单',exact:true}).click();
 await expect(page.getByLabel('订单号')).toHaveValue(/^DEMO-/);const first=await page.getByLabel('订单号').inputValue();
 await page.getByRole('button',{name:'生成演示订单',exact:true}).click();await expect(page.getByLabel('订单号')).not.toHaveValue(first);
 await runCase(page,true);await expect(page.locator('.stage-status').filter({hasText:'未观测到'})).toHaveCount(5);
});

test('owner-disabled execution stays visibly disabled (health response UI contract)',async({page})=>{
 await page.route('**/api/health',route=>route.fulfill({json:{status:'ok',synthetic:true,dify_configured:true,public_demo:true,execution_enabled:false}}));
 await page.goto('/');await connect(page);await expect(page.getByText('操作者已关闭案件执行；仍可查看记录与生成合成订单。')).toBeVisible();
 await startCase(page);await page.getByLabel('订单号').fill('DEMO-1001');await page.getByRole('button',{name:'下一步：确认运行',exact:true}).click();
 await expect(page.getByRole('button',{name:'提交真实案件',exact:true})).toBeDisabled();
});

test('static public simulation works offline without ANY API requests; deterministic actions and idempotency',async({page,context,request})=>{
 const before=await (await request.get('/api/metrics',{headers:{Authorization:'Bearer '+TOKEN}})).json();const apiRequests:string[]=[];
 page.on('request',r=>{if(['fetch','xhr'].includes(r.resourceType()))apiRequests.push(r.url())});
 await page.goto('http://127.0.0.1:8003');await expect(page.locator('.mode-pill')).toHaveText('模拟体验模式');await context.setOffline(true);
 await startCase(page);await page.getByRole('button',{name:'生成演示订单',exact:true}).click();const order=await page.getByLabel('订单号').inputValue();expect(order).toMatch(/^SIM-ORDER-/);
 await page.getByLabel('问题描述').fill('合成测试：白色杯体裂纹');await page.getByLabel('图片预览（可选）').setInputFiles('../tests/fixtures/evidence.png');
 await expect(page.getByAltText('待提交图片预览')).toBeVisible();await runCase(page);
 await expect(page.locator('.stage-status').filter({hasText:'模拟记录'})).toHaveCount(5);await showResult(page);
 await expect(page.locator('.resolution')).toContainText('已创建模拟申请');const application=await page.locator('.order-card').getByText(/^SIM-RETURN-/).innerText();
 await expect(page.getByText('不适用：未调用模型')).toBeVisible();
 await startCase(page);await page.getByLabel('订单号').fill(order);await page.getByLabel('问题描述').fill('同订单重复申请，检查幂等');await runCase(page);await showResult(page);
 await expect(page.locator('.order-card').getByText(application,{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'效果评估',exact:true}).click();await expect(page.getByRole('heading',{name:'模拟效果评估'})).toBeVisible();
 expect(apiRequests).toEqual([]);const after=await (await request.get('/api/metrics',{headers:{Authorization:'Bearer '+TOKEN}})).json();expect(after.total_cases).toBe(before.total_cases);expect(after.created_applications).toBe(before.created_applications);
});

test('public simulation handles blurry evidence, expired policy, missing order and missing information',async({page})=>{
 await page.goto('http://127.0.0.1:8003');
 for(const scenario of ['blurry','expired','missing','description']){
  await startCase(page,scenario==='expired'?'expired':scenario==='blurry'?'evidence':'valid');
  if(scenario==='missing')await page.getByLabel('订单号').fill('SIM-MISSING');else await page.getByRole('button',{name:'生成演示订单',exact:true}).click();
  if(scenario!=='description')await page.getByLabel('问题描述').fill('模拟证据核查');await runCase(page);await showResult(page);
  await expect(page.locator('.resolution')).toContainText({blurry:'证据不足',expired:'30天售后期限',missing:'未找到订单',description:'请补充问题描述'}[scenario]!);
  await expect(page.getByText('没有模拟申请',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'查看完整执行过程',exact:true}).click();await expect(page.locator('.agent-timeline li.not_observed')).toHaveCount(scenario==='description'?5:2);
 }
});

test('same static site connects cross-origin with real CORS/auth, clears records on disconnect and never silently falls back',async({page,context})=>{
 await page.goto('http://127.0.0.1:8003');await connect(page);
 await expect(page.getByLabel('私有操作者口令')).toHaveCount(0);expect(page.url()).not.toContain(TOKEN);
 expect(await page.evaluate(()=>({local:{...localStorage},session:{...sessionStorage}}))).toEqual({local:{},session:{}});
 await page.getByRole('button',{name:'运营数据',exact:true}).click();await expect(page.locator('tbody tr').first()).toBeVisible();
 await context.setOffline(true);await expect(page.locator('.mode-pill')).toHaveText('真实连接 · 已断开',{timeout:16000});await expect(page.locator('tbody tr')).toHaveCount(0);
 await expect(page.locator('.mode-notice')).toContainText('断线不会自动替换为模拟数据');await page.getByRole('button',{name:'断开并返回模拟',exact:true}).click();
 await expect(page.locator('.mode-pill')).toHaveText('模拟体验模式');await page.getByRole('button',{name:'连接真实后端',exact:true}).click();await expect(page.getByLabel('私有操作者口令')).toHaveValue('');
});

test('private connection rejects wrong token, unsafe origin and unprotected backend without changing mode',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'连接真实后端',exact:true}).click();await page.getByLabel('真实后端地址').fill('http://remote.example');await page.getByLabel('私有操作者口令').fill('wrong-token-'+'x'.repeat(32));
 await page.getByRole('button',{name:'验证并连接',exact:true}).click();await expect(page.getByRole('alert')).toContainText('HTTPS后端地址');
 await page.getByLabel('真实后端地址').fill('http://127.0.0.1:8001');await page.getByRole('button',{name:'验证并连接',exact:true}).click();await expect(page.getByRole('alert')).toContainText('HTTP 401');await expect(page.locator('.mode-pill')).toHaveText('模拟体验模式');
 await page.route('**/api/health',r=>r.fulfill({json:{public_demo:false}}));await page.getByLabel('私有操作者口令').fill(TOKEN);await page.getByRole('button',{name:'验证并连接',exact:true}).click();await expect(page.getByRole('alert')).toContainText('后端未开启受保护模式');
 await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);await expect(page.getByRole('button',{name:'连接真实后端',exact:true})).toBeFocused();
});
