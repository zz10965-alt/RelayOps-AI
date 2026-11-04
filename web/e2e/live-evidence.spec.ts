import {test,expect} from '@playwright/test';
import {connect,startCase,runCase,showResult} from './support';

// Browser HTTP contracts only: these fixtures are NOT actual Dify/model results.
for(const rejected of [false,true])test(`Live evidence rendering contract (mock HTTP): ${rejected?'human handoff':'five-stage verified return'}`,async({page})=>{
 const application={id:'test-contract-return',order_id:'TEST-CONTRACT-ORDER',status:'created'};
 const evidence={order_id:'TEST-CONTRACT-ORDER',damaged:true,product_match:true,image_quality:rejected?'blurry':'clear',confidence:rejected?0.3:0.95,summary:'测试替身证据：不代表真实模型输出'};
 const steps=['analysis','order_lookup','policy_lookup','resolve',...rejected?[]:['return_create','return_verify']];
 const trace=steps.map((step,id)=>({id,step,success:true,created:1,duration_ms:0,detail:step==='analysis'?evidence:step.startsWith('return_')?application:step==='resolve'?{decision:rejected?'handoff':'create',reason:rejected?'图片模糊，请补充清晰照片':'允许创建申请'}:{status:'delivered'}}));
 const names=['Understand','Retrieve','Decide','Act','Verify'];
 const groups=[['analysis'],['order_lookup','policy_lookup'],['resolve'],['return_create'],['return_verify']];
 const detail={id:'test-contract-case',order_id:'TEST-CONTRACT-ORDER',status:rejected?'handoff':'application_created',reason:rejected?'图片模糊，请补充清晰照片':'申请已创建并回读验证；尚未批准或完成退款/退货',created:1,finished:2,description:'测试替身',order:{product:'白色陶瓷杯',status:'delivered'},analysis:evidence,application:rejected?null:application,run_id:'mock-browser-run',policy:{text:'30天测试政策'},trace,stages:names.map((name,i)=>({name,status:rejected&&i>2?'not_observed':i===2?rejected?'handoff':'recorded':'succeeded',summary:'测试契约记录',events:trace.filter(e=>groups[i].includes(e.step))}))};
 await page.route('**/api/health',route=>route.fulfill({json:{status:'ok',public_demo:true,dify_configured:true,execution_enabled:true}}));
 await page.route('**/api/cases',route=>route.fulfill({status:route.request().method()==='POST'?202:200,json:route.request().method()==='POST'?{id:detail.id}:[detail]}));
 await page.route('**/api/cases/test-contract-case',route=>route.fulfill({json:detail}));
 await page.goto('/');await connect(page);await startCase(page);
 await page.getByLabel('订单号').fill(detail.order_id);await page.getByLabel('问题描述').fill('测试HTTP契约，不执行模型');
 await page.getByLabel('商品照片',{exact:true}).setInputFiles('../tests/fixtures/evidence.png');await runCase(page,true);
 await expect(page.getByText(evidence.summary,{exact:true})).toBeVisible();
 await expect(page.locator('.agent-timeline li')).toHaveCount(5);
 await expect(page.locator('.agent-timeline .not_observed')).toHaveCount(rejected?2:0);
 await showResult(page);
 await expect(page.getByRole('heading',{name:rejected?'需要人工核查':'已创建退货申请',exact:true})).toBeVisible();
 await expect(page.locator('.order-card')).toContainText('mock-browser-run');
 await expect(page.locator('.resolution')).toContainText(rejected?'图片模糊':'回读验证');
 if(!rejected){
  const tampered={...detail,trace:trace.map(e=>e.step==='return_verify'?{...e,detail:{...application,order_id:'WRONG-ORDER'}}:e)};
  await page.route('**/api/cases/test-contract-case',route=>route.fulfill({json:tampered}));
  await expect(page.getByRole('heading',{name:'结果尚待核验',exact:true})).toBeVisible();
  await expect(page.getByText('缺少匹配的成功核验事件，不宣称已完成。',{exact:true})).toBeVisible();
 }
});
