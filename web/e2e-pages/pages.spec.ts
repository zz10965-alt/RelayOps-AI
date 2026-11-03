import {test,expect} from '@playwright/test';
import {startCase,runCase,showResult} from '../e2e/support';

test('strict Pages subpath loads all assets, reloads, and runs a complete offline simulation without backend requests',async({page,context,request})=>{
 const redirect=await request.get('http://127.0.0.1:8004/RelayOps-AI',{maxRedirects:0});
 expect(redirect.status()).toBe(301);expect(redirect.headers().location).toBe('/RelayOps-AI/');
 const failures:string[]=[],apiRequests:string[]=[],assets:string[]=[];
 page.on('pageerror',e=>failures.push(e.message));
 page.on('requestfailed',r=>failures.push(r.url()));
 page.on('request',r=>{
  if(['fetch','xhr'].includes(r.resourceType()))apiRequests.push(r.url());
  if(['script','stylesheet','image'].includes(r.resourceType())&&r.url().startsWith('http'))assets.push(r.url());
 });
 page.on('response',r=>{if(r.status()>=400)failures.push(`${r.status()} ${r.url()}`)});
 await page.goto('./');
 await expect(page.locator('.mode-pill')).toHaveText('模拟体验模式');
 await page.reload();
 await expect(page.locator('.mode-pill')).toHaveText('模拟体验模式');
 await expect(page.getByAltText('纸箱与紫色机器人装饰插画，非损坏证据')).toBeVisible();
 expect(await page.getByAltText('纸箱与紫色机器人装饰插画，非损坏证据').evaluate((img:HTMLImageElement)=>img.complete&&img.naturalWidth>0)).toBeTruthy();
 expect(assets.some(url=>url.endsWith('.png'))).toBeTruthy();
 expect(assets.length).toBeGreaterThan(0);
 expect(assets.every(url=>new URL(url).pathname.startsWith('/RelayOps-AI/assets/'))).toBeTruthy();
 // Missing root assets must fail, so a forgiving SPA server cannot mask bad base URLs.
 expect((await request.get('/assets/not-a-pages-asset.js')).status()).toBe(404);
 await context.setOffline(true);
 await startCase(page);
 await page.getByRole('button',{name:'生成演示订单',exact:true}).click();
 await page.getByLabel('问题描述').fill('Pages simulation: cracked ceramic cup');
 await page.getByLabel('图片预览（可选）').setInputFiles('../tests/fixtures/evidence.png');
 await expect(page.getByAltText('待提交图片预览')).toBeVisible();
 await runCase(page);
 await expect(page.locator('.stage-status').filter({hasText:'模拟记录'})).toHaveCount(5);
 await showResult(page);
 await expect(page.locator('.resolution')).toContainText('已创建模拟申请');
 await page.getByRole('button',{name:'效果评估',exact:true}).click();
 await expect(page.getByRole('heading',{name:'模拟效果评估'})).toBeVisible();
 for(const scenario of ['blurry','expired']){
  await startCase(page,scenario==='expired'?'expired':'evidence');
  await page.getByRole('button',{name:'生成演示订单',exact:true}).click();
  await page.getByLabel('问题描述').fill('Pages policy/evidence case');
  await runCase(page);await showResult(page);
  await expect(page.locator('.resolution')).toContainText(scenario==='blurry'?'证据不足':'30天售后期限');
  await expect(page.getByText('没有模拟申请',{exact:true})).toBeVisible();
 }
 await page.getByRole('button',{name:'人工处理',exact:true}).click();
 await expect(page.locator('tbody tr')).toHaveCount(2);
 expect(new URL(page.url()).pathname).toBe('/RelayOps-AI/');
 expect(apiRequests).toEqual([]);expect(failures).toEqual([]);
});

test('Pages runtime Live connection uses the independent HTTPS API origin (protocol fixture, no model)',async({page})=>{
 const token='pages-operator-fixture-'+'x'.repeat(32),calls:string[]=[];
 const metrics={total_cases:0,terminal_cases:0,created_applications:0,completion_rate:null,automation_rate:null,tool_calls:0,tool_success_rate:null,parameter_accuracy:null,average_duration_seconds:null,handoff_rate:null,retried_cases:0,recovered_cases:0,recovery_rate:null,average_api_cost:null,priced_cases:0,currency:null,cost_note:'Protocol test only'};
 await page.route('https://operator.fixture.invalid/api/**',async route=>{
  const r=route.request();expect(r.headers().authorization).toBe('Bearer '+token);
  const path=new URL(r.url()).pathname;calls.push(path);
  const data=path==='/api/health'?{public_demo:true,dify_configured:false,execution_enabled:false}:path==='/api/cases'?[]:metrics;
  await route.fulfill({json:data});
 });
 await page.goto('./');
 await page.getByRole('button',{name:'连接真实后端',exact:true}).click();
 await page.getByLabel('真实后端地址').fill('https://operator.fixture.invalid');
 await page.getByLabel('私有操作者口令').fill(token);
 await page.getByRole('button',{name:'验证并连接',exact:true}).click();
 await expect(page.locator('.mode-pill')).toHaveText('真实连接 · 操作者');
 expect(calls).toContain('/api/health');expect(calls).toContain('/api/cases');
 expect(calls.every(path=>path.startsWith('/api/')&&!path.includes('RelayOps-AI'))).toBeTruthy();
 expect(page.url()).not.toContain(token);
 expect(await page.evaluate(()=>({local:{...localStorage},session:{...sessionStorage}}))).toEqual({local:{},session:{}});
 await page.getByRole('button',{name:'断开并返回模拟'}).click();
 await expect(page.locator('.mode-pill')).toHaveText('模拟体验模式');
});
