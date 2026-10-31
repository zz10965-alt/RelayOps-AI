import {test,expect} from '@playwright/test';

test('real backend dashboard, missing evidence, handoff, trace and metrics',async({page,request})=>{
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'让每个异常都有处理闭环'})).toBeVisible();
 await expect(page.getByText('Dify 尚未配置',{exact:true})).toBeVisible();
 await page.screenshot({path:'/tmp/relayops-overview.png',fullPage:true});
 await page.getByRole('button',{name:'＋ 新建案件',exact:true}).click();
 await page.getByLabel('订单号').fill('DEMO-1001');
 await page.getByRole('button',{name:'提交并开始处理 →'}).click();
 await expect(page.getByText('请补充：问题描述、商品照片',{exact:true})).toBeVisible();
 await expect(page.getByText('没有经过核验的申请',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'＋ 新建案件',exact:true}).click();
 await page.getByLabel('订单号').fill('DEMO-1001');
 await page.getByLabel('问题描述').fill('白色陶瓷杯损坏，需要售后');
 // Real valid PNG bytes, synthetic test evidence, no fake model response.
 await page.getByLabel('商品照片').setInputFiles('../tests/fixtures/evidence.png');
 await page.getByRole('button',{name:'提交并开始处理 →'}).click();
 await expect(page.getByText('Dify 未配置，未执行视觉分析',{exact:true})).toBeVisible();
 await page.getByText('configuration',{exact:true}).click();
 await expect(page.getByText(/Dify 未配置；未运行模型/)).toBeVisible();
 await page.getByRole('button',{name:/Evaluation/}).click();
 await expect(page.getByRole('heading',{name:'真实日志指标'})).toBeVisible();
 const metrics=await (await request.get('/api/metrics')).json();
 expect(metrics.total_cases).toBe(2);expect(metrics.created_applications).toBe(0);
 expect(metrics.average_api_cost).toBeNull();
 await page.getByRole('button',{name:/Human Handoff/}).click();
 await expect(page.getByRole('heading',{name:'等待人工处理'})).toBeVisible();
 await expect(page.locator('tbody tr')).toHaveCount(2);
});

test('mobile navigation and readable layout',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.goto('/');
 await page.getByRole('button',{name:/New Case/}).click();
 await expect(page.getByLabel('订单号')).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
});
