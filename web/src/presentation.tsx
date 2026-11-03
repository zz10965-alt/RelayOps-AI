import React from 'react';

export function Icon({name,size=20}:{name:string;size?:number}){
 const paths:Record<string,React.ReactNode>={
  box:<><path d="m3 7 9-5 9 5v10l-9 5-9-5Z"/><path d="m3 7 9 5 9-5M12 12v10M7 4.8l9 5"/></>,
  home:<><path d="m3 10 9-7 9 7v11h-6v-7H9v7H3Z"/></>,
  truck:<><path d="M2 5h12v12H2zM14 10h4l4 4v3h-8"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="18" r="2"/></>,
  warehouse:<><path d="m2 10 10-7 10 7v11H2Z"/><path d="M7 21V11h10v10M7 15h10M7 18h10"/></>,
  chart:<><path d="M4 3v18h17M8 16v-4M13 16V8M18 16V5"/></>,
  user:<><circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/></>,
  check:<path d="m5 12 4 4L19 6"/>,
  arrow:<path d="M4 12h16m-6-6 6 6-6 6"/>,
  eye:<><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></>,
  search:<><circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/></>,
  decide:<><circle cx="12" cy="12" r="4"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2"/></>,
  tool:<><path d="M15 3a5 5 0 0 0-6 6L3 15a3 3 0 0 0 4 4l6-6a5 5 0 0 0 6-6l-4 4-3-3Z"/></>,
  shield:<><path d="m12 2 9 4v6c0 6-9 10-9 10S3 18 3 12V6Z"/><path d="m8 12 3 3 5-6"/></>,
  monitor:<><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 22h8m-4-5v5"/></>,
  refresh:<><path d="M20 8a9 9 0 1 0 0 9M20 2v6h-6"/></>,
  info:<><circle cx="12" cy="12" r="10"/><path d="M12 10v7m0-11v1"/></>,
  clock:<><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 3"/></>,
  list:<><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></>,
  upload:<><path d="M12 17V3m-5 5 5-5 5 5M3 15v6h18v-6"/></>,
  close:<path d="m6 6 12 12M6 18 18 6"/>,
 };
 return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]??paths.info}</svg>;
}
export const statusLabels:Record<string,string>={queued:'等待处理',running:'执行中',needs_information:'待补充资料',handoff:'需人工处理',application_created:'申请已创建',created:'已创建',approved:'已批准',completed:'已完成',shipping:'运输中',delivered:'已签收'};
export const stages=[{name:'Understand',label:'理解',description:'分析问题与证据',icon:'eye'},{name:'Retrieve',label:'查询',description:'获取订单与规则',icon:'search'},{name:'Decide',label:'决策',description:'核对业务条件',icon:'decide'},{name:'Act',label:'执行',description:'创建允许的申请',icon:'tool'},{name:'Verify',label:'验证',description:'检查实际处理结果',icon:'shield'}];
export const stageLabels:Record<string,string>={not_observed:'未观测到',succeeded:'已有成功证据',simulated:'模拟记录',recorded:'已有决策记录',failed:'失败',handoff:'转人工',partial:'部分记录'};
export const time=(value:number)=>new Date(value*1000).toLocaleString('zh-CN',{hour12:false});
export const percent=(value:number|null)=>value===null?'暂无样本':`${(value*100).toFixed(1)}%`;
const reasons:Record<string,string>={
 'Please supply a damage description. No simulated action executed.':'请补充问题描述。尚未执行模拟处理。',
 'Insufficient evidence. Request a suitable photo or human review.':'证据不足，请补充合适照片或交由人工核查。',
 'Order not found.':'未找到订单，请核对订单号。',
 'Order not delivered. No return request permitted.':'订单尚未签收，不允许创建退货申请。',
 'Outside the 30-day return policy. No return request permitted.':'订单超出30天售后期限，不允许创建退货申请。',
 'Request created and memory readback checked; not approved or completed.':'已创建模拟申请并完成内存回读；尚未批准，也未完成退货或退款。',
 'Synthetic evidence and deterministic policy checks permit request creation.':'合成证据与确定性政策检查允许创建模拟申请。',
 'Created a browser-memory request, not a real business action.':'已在浏览器内存中创建模拟申请，不是真实业务操作。',
 'Reused the existing simulated request (idempotent).':'已复用同订单的模拟申请，没有重复创建。',
 'Re-read the simulated memory store. This is NOT SQLite verification.':'已回读模拟内存记录；这不是SQLite数据库验证。',
 'Synthetic order found.':'已找到合成订单。',
 'Synthetic order not found.':'未找到合成订单。',
 'Simulated form submission; no HTTP request or database write.':'模拟表单已提交，没有HTTP请求或数据库写入。',
 'Workflow requested human review; no backend action verified':'工作流请求人工核查，尚未确认后端业务执行成功。',
 'Please supply a clear product photo; workflow requested human review':'请补充清晰商品照片，工作流已请求人工核查。',
 'White ceramic cup':'白色陶瓷杯',
 'Image maximum is 5 MiB':'图片最大为5 MiB，请重新选择。',
 'Check the order ID and description lengths':'请检查订单号与问题描述的长度。',
};
export function humanReason(value:string|null|undefined){
 if(!value)return '暂无可确认的处理结论，请以执行证据为准。';
 const clean=value.replace(/^Error: /,'');
 const raw=clean.replace(/^SIMULATION: /,'');
 if(reasons[raw])return (clean.startsWith('SIMULATION: ')?'模拟：':'')+reasons[raw];
 if(value.startsWith('SIMULATION fixture:'))return '使用所选的确定性合成证据场景，没有分析图片或调用模型。';
 return value;
}
export function connectionMessage(value:string){
 if(value.includes('unprotected backend'))return '连接被拒绝：后端未开启受保护模式。';
 if(value.includes('HTTPS backend origin'))return '请输入不带路径、查询参数或凭据的HTTPS后端地址。';
 if(value.includes('Invalid URL'))return '后端地址格式无效，请核对完整HTTPS地址。';
 if(value.includes('valid private operator token'))return '请输入至少32个ASCII字符的私有操作者口令。';
 const code=value.match(/HTTP (\d+)/)?.[1];
 if(code)return `真实请求被拒绝（HTTP ${code}），请检查口令、执行授权或请求限制。`;
 return '真实后端已断开或无法访问。请检查隧道和CORS；未替换为模拟结果。';
}
