import {test,expect} from '@playwright/test';

test('strict Pages subpath loads all assets, reloads, and runs a complete offline simulation without backend requests',async({page,context,request})=>{
 const redirect=await request.get('http://127.0.0.1:8004/RelayOps-AI',{maxRedirects:0});
 expect(redirect.status()).toBe(301);expect(redirect.headers().location).toBe('/RelayOps-AI/');
 const failures:string[]=[],apiRequests:string[]=[],assets:string[]=[];
 page.on('pageerror',e=>failures.push(e.message));
 page.on('requestfailed',r=>failures.push(r.url()));
 page.on('request',r=>{
  if(['fetch','xhr'].includes(r.resourceType()))apiRequests.push(r.url());
  if(['script','stylesheet'].includes(r.resourceType()))assets.push(r.url());
 });
 page.on('response',r=>{if(r.status()>=400)failures.push(`${r.status()} ${r.url()}`)});
 await page.goto('./');
 await expect(page.getByText('SIMULATION · BROWSER ONLY',{exact:true})).toBeVisible();
 await page.reload();
 await expect(page.getByText('SIMULATION · BROWSER ONLY',{exact:true})).toBeVisible();
 expect(assets.length).toBeGreaterThan(0);
 expect(assets.every(url=>new URL(url).pathname.startsWith('/RelayOps-AI/assets/'))).toBeTruthy();
 // Missing root assets must fail, so a forgiving SPA server cannot mask bad base URLs.
 expect((await request.get('/assets/not-a-pages-asset.js')).status()).toBe(404);
 await context.setOffline(true);
 await page.getByRole('button',{name:'＋ New Case',exact:true}).click();
 await page.getByRole('button',{name:'Generate fresh synthetic order'}).click();
 await page.getByLabel('Damage description').fill('Pages simulation: cracked ceramic cup');
 await page.getByLabel('Optional local image preview').setInputFiles('../tests/fixtures/evidence.png');
 await expect(page.getByAltText('Selected image preview')).toBeVisible();
 await page.getByRole('button',{name:'Run simulation →'}).click();
 await expect(page.locator('.resolution')).toContainText('SIMULATION: Request created');
 await expect(page.locator('summary').filter({hasText:'simulated'})).toHaveCount(5);
 await page.getByRole('button',{name:/Evaluation/}).click();
 await expect(page.getByRole('heading',{name:'Simulated session metrics'})).toBeVisible();
 for(const scenario of ['blurry','expired']){
  await page.getByRole('button',{name:'＋ New Case',exact:true}).click();
  if(scenario==='expired')await page.getByLabel('Interview scenario').selectOption('expired');
  await page.getByRole('button',{name:'Generate fresh synthetic order'}).click();
  await page.getByLabel('Damage description').fill('Pages policy/evidence case');
  if(scenario==='blurry')await page.getByLabel('Simulated evidence fixture').selectOption('blurry');
  await page.getByRole('button',{name:'Run simulation →'}).click();
  await expect(page.locator('.resolution')).toContainText(scenario==='blurry'?'Insufficient evidence':'30-day return policy');
  await expect(page.getByText('No simulated application',{exact:true})).toBeVisible();
 }
 await page.getByRole('button',{name:/Human Handoff/}).click();
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
 await page.getByRole('button',{name:'Operator Live connection'}).click();
 await page.getByLabel('Live backend origin').fill('https://operator.fixture.invalid');
 await page.getByLabel('Private operator token').fill(token);
 await page.getByRole('button',{name:'Connect Live',exact:true}).click();
 await expect(page.getByText('LIVE · OPERATOR',{exact:true})).toBeVisible();
 expect(calls).toContain('/api/health');expect(calls).toContain('/api/cases');
 expect(calls.every(path=>path.startsWith('/api/')&&!path.includes('RelayOps-AI'))).toBeTruthy();
 expect(page.url()).not.toContain(token);
 expect(await page.evaluate(()=>({local:{...localStorage},session:{...sessionStorage}}))).toEqual({local:{},session:{}});
 await page.getByRole('button',{name:'Disconnect and return to Simulation'}).click();
 await expect(page.getByText('SIMULATION · BROWSER ONLY',{exact:true})).toBeVisible();
});
