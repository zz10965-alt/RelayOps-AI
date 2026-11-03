import type {Detail, Metrics} from './types';

// Explicit browser-only fixtures. These timestamps and outputs are synthetic, not model observations.
export function createSimulation(){
 let sequence=0, tick=0;
 const now=()=>Date.UTC(2026,0,15)/1000+tick++;
 const orders=new Map<string,Record<string,unknown>>();
 const records=new Map<string,Detail>();
 const applications=new Map<string,{id:string;order_id:string;status:string}>();
 const policy={text:'SIMULATION: Delivered within 30 days, clear matching damage evidence, confidence ≥ 0.8. Creating a request does not approve it or issue a refund.'};
 const newOrder=(scenario:string)=>{
  if(!['eligible','expired','shipping'].includes(scenario))throw new Error('Unknown synthetic order scenario');
  const id=`SIM-ORDER-${String(++sequence).padStart(4,'0')}`;
  const result={id,product:'White ceramic cup',status:scenario==='shipping'?'shipping':'delivered',delivered_age_days:scenario==='expired'?45:3,synthetic:true};
  orders.set(id,result);return result;
 };
 newOrder('eligible');
 return async function request(path:string,options?:RequestInit):Promise<unknown>{
  if(path==='/health')return {dify_configured:false,execution_enabled:true,public_demo:true,simulation:true};
  if(path==='/demo/orders')return newOrder(JSON.parse(String(options?.body??'{}')).scenario??'eligible');
  if(path==='/cases'&&options?.method==='POST'){
   const form=options.body;
   if(!(form instanceof FormData))throw new Error('Expected a case form');
   const orderId=String(form.get('order_id')??'').trim();
   const description=String(form.get('description')??'').trim();
   if(!orderId||orderId.length>80||description.length>4000)throw new Error('Check the order ID and description lengths');
   const image=form.get('image');
   if(image instanceof File&&image.size>5*1024*1024)throw new Error('Image maximum is 5 MiB');
   const fixture=String(form.get('evidence_fixture')??'clear');
   if(!['clear','blurry','unrelated','low_confidence'].includes(fixture))throw new Error('Unknown simulated evidence fixture');
   const id=`SIM-CASE-${String(++sequence).padStart(4,'0')}`;
   const record:Detail={id,order_id:orderId,description,status:'running',reason:null,created:now(),finished:null,order:orders.get(orderId)??null,analysis:null,application:null,policy,run_id:null,trace:[],stages:[]};
   const add=(step:string,detail:Record<string,unknown>,success=true)=>record.trace.push({id:record.trace.length+1,step,success,detail:{simulation:true,...detail},created:now(),duration_ms:0});
   add('submission',{summary:'Simulated form submission; no HTTP request or database write.'});
   const handoff=(reason:string)=>{record.status='handoff';record.reason='SIMULATION: '+reason;add('resolve',{decision:'handoff',reason});};
   if(!description){record.status='needs_information';record.reason='SIMULATION: Please supply a damage description. No simulated action executed.';}
   else{
    record.analysis={simulation:true,order_id:orderId,damaged:fixture!=='unrelated',product_match:fixture!=='unrelated',image_quality:fixture==='low_confidence'?'clear':fixture,confidence:fixture==='low_confidence'?0.4:0.95,summary:`SIMULATION fixture: ${fixture}. No image analysis or model call took place.`};
    add('analysis',record.analysis);
    add('order_lookup',{summary:record.order?'Synthetic order found.':'Synthetic order not found.'},!!record.order);
    if(!record.order)handoff('Order not found.');
    else{
     add('policy_lookup',{summary:policy.text});
     if(fixture!=='clear')handoff('Insufficient evidence. Request a suitable photo or human review.');
     else if(record.order.status!=='delivered')handoff('Order not delivered. No return request permitted.');
     else if(Number(record.order.delivered_age_days)>30)handoff('Outside the 30-day return policy. No return request permitted.');
     else{
      const existing=applications.get(orderId);
      const application=existing??{id:`SIM-RETURN-${String(++sequence).padStart(4,'0')}`,order_id:orderId,status:'created'};
      applications.set(orderId,application);
      add('resolve',{summary:'Synthetic evidence and deterministic policy checks permit request creation.'});
      add('return_create',{...application,reused:!!existing,summary:existing?'Reused the existing simulated request (idempotent).':'Created a browser-memory request, not a real business action.'});
      record.application={...applications.get(orderId)!};
      add('return_verify',{...record.application,summary:'Re-read the simulated memory store. This is NOT SQLite verification.'});
      record.status='application_created';record.reason='SIMULATION: Request created and memory readback checked; not approved or completed.';
     }
    }
   }
   record.finished=now();
   const groups:[string,string[]][]=[['Understand',['analysis']],['Retrieve',['order_lookup','policy_lookup']],['Decide',['resolve']],['Act',['return_create']],['Verify',['return_verify']]];
   record.stages=groups.map(([name,steps])=>{
    const events=record.trace.filter(e=>steps.includes(e.step));
    const status=!events.length?'not_observed':events.some(e=>!e.success)?'failed':name==='Decide'&&record.status==='handoff'?'handoff':'simulated';
    return {name,status,summary:events.map(e=>String((e.detail as Record<string,unknown>).summary??(e.detail as Record<string,unknown>).reason??e.step)).join(' · '),events};
   });
   records.set(id,record);return {id,status:record.status};
  }
  if(path==='/cases')return [...records.values()].reverse();
  if(path.startsWith('/cases/')){const item=records.get(path.slice(7));if(!item)throw new Error('Simulated case not found');return structuredClone(item);}
  if(path==='/metrics'){
   const rows=[...records.values()],total=rows.length,created=rows.filter(r=>r.status==='application_created').length;
   const ratio=(n:number,d:number)=>d?n/d:null;
   const tools=rows.flatMap(r=>r.trace).filter(e=>e.step==='resolve');
   const result:Metrics={total_cases:total,terminal_cases:total,created_applications:applications.size,completion_rate:ratio(created,total),automation_rate:ratio(created,total),tool_calls:tools.length,tool_success_rate:ratio(tools.filter(e=>e.success).length,tools.length),parameter_accuracy:tools.length?1:null,average_duration_seconds:null,handoff_rate:ratio(rows.filter(r=>r.status==='handoff').length,total),retried_cases:0,recovered_cases:0,recovery_rate:null,average_api_cost:null,priced_cases:0,currency:null,cost_note:'SIMULATION ONLY: Browser-memory fixture counts, not model accuracy, API cost, real timing or verified operational outcomes.'};
   return result;
  }
  throw new Error('Unsupported simulated operation');
 };
}
