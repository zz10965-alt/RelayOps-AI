import {test,expect} from '@playwright/test';

test('real backend dashboard, missing evidence, handoff, trace and metrics',async({page,request})=>{
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'Every exception, a verified outcome'})).toBeVisible();
 await expect(page.getByText('Dify not configured',{exact:true})).toBeVisible();
 await page.screenshot({path:'/tmp/relayops-overview.png',fullPage:true});
 await page.getByRole('button',{name:'＋ New Case',exact:true}).click();
 await page.getByLabel('Order ID').fill('DEMO-1001');
 await page.getByRole('button',{name:'Submit and run →'}).click();
 await expect(page.getByText('请补充：问题描述、商品照片',{exact:true})).toBeVisible();
 await expect(page.getByText('No verified application',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'＋ New Case',exact:true}).click();
 await page.getByLabel('Order ID').fill('DEMO-1001');
 await page.getByLabel('Damage description').fill('白色陶瓷杯损坏，需要售后');
 // Real valid PNG bytes, synthetic test evidence, no fake model response.
 await page.getByLabel('Product image').setInputFiles('../tests/fixtures/evidence.png');
 await page.getByRole('button',{name:'Submit and run →'}).click();
 await expect(page.getByText('Dify 未配置，未执行视觉分析',{exact:true})).toBeVisible();
 await page.getByText('configuration',{exact:true}).click();
 await expect(page.getByText(/Dify 未配置；未运行模型/)).toBeVisible();
 await page.getByRole('button',{name:/Evaluation/}).click();
 await expect(page.getByRole('heading',{name:'Observed metrics'})).toBeVisible();
 const metrics=await (await request.get('/api/metrics')).json();
 expect(metrics.total_cases).toBe(2);expect(metrics.created_applications).toBe(0);
 expect(metrics.average_api_cost).toBeNull();
 await page.getByRole('button',{name:/Human Handoff/}).click();
 await expect(page.getByRole('heading',{name:'Awaiting human review'})).toBeVisible();
 await expect(page.locator('tbody tr')).toHaveCount(2);
});

test('mobile navigation and readable layout',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.goto('/');
 await page.getByRole('button',{name:'New Case',exact:true}).click();
 await expect(page.getByLabel('Order ID')).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
});

test('fresh scenario order and honest timeline',async({page})=>{
 await page.goto('/');
 await expect(page.getByText('Delivery Exceptions — Planned · Inventory & Fulfillment — Planned')).toBeVisible();
 await page.getByRole('button',{name:'Damage & Returns — Open Module 1'}).click();
 await page.getByRole('button',{name:'Generate fresh synthetic order'}).click();
 await expect(page.getByLabel('Order ID')).toHaveValue(/^DEMO-/);
 const first=await page.getByLabel('Order ID').inputValue();
 await page.getByRole('button',{name:'Generate fresh synthetic order'}).click();
 await expect(page.getByLabel('Order ID')).not.toHaveValue(first);
 await page.getByRole('button',{name:'Submit and run →'}).click();
 await expect(page.getByRole('heading',{name:'Agent Execution Timeline'})).toBeVisible();
 await expect(page.locator('summary').filter({hasText:'not observed'})).toHaveCount(5);
});

test('owner-disabled execution stays visibly disabled (health response UI contract)',async({page})=>{
 await page.route('**/api/health',route=>route.fulfill({json:{status:'ok',synthetic:true,dify_configured:true,public_demo:true,execution_enabled:false}}));
 await page.goto('/');
 await page.getByRole('button',{name:'＋ New Case',exact:true}).click();
 await expect(page.getByText('Case execution is disabled by the owner.',{exact:false})).toBeVisible();
 await expect(page.getByRole('button',{name:'Submit and run →'})).toBeDisabled();
});
