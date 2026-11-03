import {expect} from '@playwright/test';
import type {Page} from '@playwright/test';
export const TOKEN='operator-test-fixture-32-characters-only';
export async function connect(page:Page,origin='http://127.0.0.1:8001'){
 await page.getByRole('button',{name:'连接真实后端',exact:true}).click();
 await page.getByLabel('真实后端地址').fill(origin);
 await page.getByLabel('私有操作者口令').fill(TOKEN);
 await page.getByRole('button',{name:'验证并连接',exact:true}).click();
 await expect(page.locator('.mode-pill')).toHaveText('真实连接 · 操作者');
}
export async function startCase(page:Page,scenario='valid'){
 await page.getByRole('button',{name:'商品损坏售后',exact:true}).click();
 if(scenario!=='valid')await page.getByRole('radio').nth({evidence:1,expired:2,shipping:3}[scenario]!).check();
 await page.getByRole('button',{name:'下一步：补充信息',exact:true}).click();
 await expect(page.getByLabel('订单号')).toBeVisible();
}
export async function runCase(page:Page,live=false){
 await page.getByRole('button',{name:'下一步：确认运行',exact:true}).click();
 await page.getByRole('button',{name:live?'提交真实案件':'运行模拟处理',exact:true}).click();
 await expect(page.getByRole('heading',{name:'五阶段执行时间线',exact:true})).toBeVisible();
}
export async function showResult(page:Page){
 await page.getByRole('button',{name:'查看处理结果',exact:true}).click();
 await expect(page.getByRole('heading',{name:/^(模拟处理结果|案件处理结果)$/})).toBeVisible();
}
