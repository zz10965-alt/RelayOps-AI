import {createSimulation} from './simulation';
import type {Health} from './types';
export type DataClient={mode:'simulation'|'live';request:<T>(path:string,options?:RequestInit)=>Promise<T>;dispose:()=>void};
export function simulationClient():DataClient{
 const request=createSimulation();
 return {mode:'simulation',request:async<T>(path:string,options?:RequestInit)=>await request(path,options) as T,dispose:()=>{}};
}
export function liveClient(rawOrigin:string,rawToken:string):DataClient{
 const url=new URL(rawOrigin);
 const local=['127.0.0.1','localhost','[::1]'].includes(url.hostname);
 if(url.username||url.password||url.search||url.hash||!['','/'].includes(url.pathname)||!(url.protocol==='https:'||(url.protocol==='http:'&&local&&location.protocol==='http:')))throw new Error('Use an HTTPS backend origin without path, query or credentials.');
 let token=rawToken.trim();
 if(token.length<32||!/^[\x21-\x7e]+$/.test(token))throw new Error('Enter a valid private operator token of at least 32 ASCII characters.');
 const controllers=new Set<AbortController>();
 let disposed=false;
 const request=async<T>(path:string,options?:RequestInit):Promise<T>=>{
  if(disposed)throw new Error('Live connection closed. No simulation fallback.');
  const controller=new AbortController();controllers.add(controller);
  const timer=setTimeout(()=>controller.abort(),12000);
  try{
   const headers=new Headers(options?.headers);headers.set('Authorization','Bearer '+token);
   const response=await fetch(url.origin+'/api'+path,{...options,headers,signal:controller.signal,redirect:'error',credentials:'omit',cache:'no-store',referrerPolicy:'no-referrer'});
   if(!response.ok)throw new Error(`Live request rejected (HTTP ${response.status}). Check authorization, execution approval or request limits.`);
   return await response.json() as T;
  }catch(error){
   if(error instanceof Error&&error.message.startsWith('Live request'))throw error;
   throw new Error('Live backend offline or unreachable. Check the tunnel and CORS. No simulated results were substituted.');
  }finally{clearTimeout(timer);controllers.delete(controller);}
 };
 return {mode:'live',request,dispose:()=>{disposed=true;token='';controllers.forEach(c=>c.abort());controllers.clear();}};
}
export async function connectLive(origin:string,token:string):Promise<DataClient>{
 const client=liveClient(origin,token);
 try{
  const health=await client.request<Health&{public_demo:boolean}>('/health');
  if(!health.public_demo)throw new Error('Refusing an unprotected backend. Enable the existing authenticated operator mode.');
  await client.request('/cases'); // Health is anonymous; this request actually verifies operator access.
  return client;
 }catch(error){client.dispose();throw error;}
}
