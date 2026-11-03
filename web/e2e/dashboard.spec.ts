import {test,expect} from '@playwright/test';
const TOKEN='operator-test-fixture-32-characters-only';
async function connect(page:import('@playwright/test').Page,origin='http://127.0.0.1:8001'){
 await page.getByRole('button',{name:'Operator Live connection'}).click();
 await page.getByLabel('Live backend origin').fill(origin);
 await page.getByLabel('Private operator token').fill(TOKEN);
 await page.getByRole('button',{name:'Connect Live',exact:true}).click();
 await expect(page.getByText('LIVE · OPERATOR',{exact:true})).toBeVisible();
}

test('real backend dashboard, missing evidence, handoff, trace and metrics',async({page,request})=>{
 await page.goto('/');
 await connect(page);
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
 const metrics=await (await request.get('/api/metrics',{headers:{Authorization:'Bearer '+TOKEN}})).json();
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
 await connect(page);
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
 await connect(page);
 await page.getByRole('button',{name:'＋ New Case',exact:true}).click();
 await expect(page.getByText('Case execution is disabled by the owner.',{exact:false})).toBeVisible();
 await expect(page.getByRole('button',{name:'Submit and run →'})).toBeDisabled();
});

test('static public simulation works offline without ANY API requests; deterministic actions and idempotency',async({page,context,request})=>{
 const before=await (await request.get('/api/metrics',{headers:{Authorization:'Bearer '+TOKEN}})).json();
 const apiRequests:string[]=[];
 page.on('request',r=>{if(['fetch','xhr'].includes(r.resourceType()))apiRequests.push(r.url())});
 await page.goto('http://127.0.0.1:8003');
 await expect(page.getByText('SIMULATION · BROWSER ONLY',{exact:true})).toBeVisible();
 await page.screenshot({path:'/tmp/relayops-public-simulation.png',fullPage:true});
 await context.setOffline(true);
 await page.getByRole('button',{name:'＋ New Case',exact:true}).click();
 await page.getByRole('button',{name:'Generate fresh synthetic order'}).click();
 const order=await page.getByLabel('Order ID').inputValue();
 expect(order).toMatch(/^SIM-ORDER-/);
 await page.getByLabel('Damage description').fill('Synthetic cracked cup scenario');
 await page.getByLabel('Optional local image preview').setInputFiles('../tests/fixtures/evidence.png');
 await expect(page.getByAltText('Selected image preview')).toBeVisible();
 await page.getByRole('button',{name:'Run simulation →'}).click();
 await expect(page.locator('.resolution')).toContainText('SIMULATION: Request created');
 const application=await page.locator('dd').nth(1).innerText();
 expect(application).toMatch(/^SIM-RETURN-/);
 await expect(page.getByText('Not applicable — no model was called')).toBeVisible();
 await expect(page.locator('summary').filter({hasText:'simulated'})).toHaveCount(5);
 await page.screenshot({path:'/tmp/relayops-public-detail.png',fullPage:true});
 await page.getByRole('button',{name:'＋ New Case',exact:true}).click();
 await page.getByLabel('Order ID').fill(order);
 await page.getByLabel('Damage description').fill('Same synthetic order, repeated action');
 await page.getByRole('button',{name:'Run simulation →'}).click();
 await expect(page.locator('dd').nth(1)).toHaveText(application);
 await page.getByRole('button',{name:/Evaluation/}).click();
 await expect(page.getByRole('heading',{name:'Simulated session metrics'})).toBeVisible();
 expect(apiRequests).toEqual([]);
 const after=await (await request.get('/api/metrics',{headers:{Authorization:'Bearer '+TOKEN}})).json();
 expect(after.total_cases).toBe(before.total_cases);expect(after.created_applications).toBe(before.created_applications);
});

test('public simulation handles blurry evidence, expired policy, missing order and missing information',async({page})=>{
 await page.goto('http://127.0.0.1:8003');
 for(const scenario of ['blurry','expired','missing','description']){
  await page.getByRole('button',{name:'＋ New Case',exact:true}).click();
  if(scenario==='missing')await page.getByLabel('Order ID').fill('SIM-MISSING');
  else{
   if(scenario==='expired')await page.getByLabel('Interview scenario').selectOption('expired');
   await page.getByRole('button',{name:'Generate fresh synthetic order'}).click();
  }
  if(scenario!=='description')await page.getByLabel('Damage description').fill('Synthetic evidence case');
  if(scenario==='blurry')await page.getByLabel('Simulated evidence fixture').selectOption('blurry');
  await page.getByRole('button',{name:'Run simulation →'}).click();
  await expect(page.locator('.resolution')).toContainText({blurry:'Insufficient evidence',expired:'30-day return policy',missing:'Order not found',description:'Please supply a damage description'}[scenario]!);
  await expect(page.getByText('No simulated application',{exact:true})).toBeVisible();
 }
});

test('same static site connects cross-origin with real CORS/auth, clears records on disconnect and never silently falls back',async({page,context})=>{
 await page.goto('http://127.0.0.1:8003');
 await connect(page);
 await expect(page.getByText('Private operator token',{exact:true})).toHaveCount(0);
 expect(page.url()).not.toContain(TOKEN);
 expect(await page.evaluate(()=>({local:{...localStorage},session:{...sessionStorage}}))).toEqual({local:{},session:{}});
 await context.setOffline(true);
 await expect(page.getByText('LIVE · DISCONNECTED',{exact:true})).toBeVisible({timeout:16000});
 await expect(page.locator('tbody tr')).toHaveCount(0);
 await expect(page.getByRole('heading',{name:'Every exception, a verified outcome'})).toBeVisible();
 await expect(page.locator('.mode-banner')).toContainText('no simulation fallback');
 await page.getByRole('button',{name:'Disconnect and return to Simulation'}).click();
 await expect(page.getByText('SIMULATION · BROWSER ONLY',{exact:true})).toBeVisible();
 await expect(page.locator('tbody tr')).toHaveCount(0);
 await page.getByRole('button',{name:'Operator Live connection'}).click();
 await expect(page.getByLabel('Private operator token')).toHaveValue('');
});

test('private connection rejects wrong token, unsafe origin and unprotected backend without changing mode',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Operator Live connection'}).click();
 await page.getByLabel('Live backend origin').fill('http://remote.example');
 await page.getByLabel('Private operator token').fill('wrong-token-'+'x'.repeat(32));
 await page.getByRole('button',{name:'Connect Live',exact:true}).click();
 await expect(page.getByRole('alert')).toContainText('HTTPS backend origin');
 await page.getByLabel('Live backend origin').fill('http://127.0.0.1:8001');
 await page.getByRole('button',{name:'Connect Live',exact:true}).click();
 await expect(page.getByRole('alert')).toContainText('HTTP 401');
 await expect(page.getByText('SIMULATION · BROWSER ONLY',{exact:true})).toBeVisible();
 await page.route('**/api/health',r=>r.fulfill({json:{public_demo:false}}));
 await page.getByLabel('Private operator token').fill(TOKEN);
 await page.getByRole('button',{name:'Connect Live',exact:true}).click();
 await expect(page.getByRole('alert')).toContainText('Refusing an unprotected backend');
});
