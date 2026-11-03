import { defineConfig, loadEnv } from 'vite';
export default defineConfig(({mode})=>{
 const base=loadEnv(mode,'.','VITE_').VITE_API_BASE_URL;
 if(base && (!base.startsWith('https://') || new URL(base).pathname!=='/' || new URL(base).username || new URL(base).password || new URL(base).search || new URL(base).hash)) throw new Error('VITE_API_BASE_URL must be an HTTPS origin');
 return {base:mode==='github-pages'?'/RelayOps-AI/':'/',server:{proxy:{'/api':'http://127.0.0.1:8000'}}};
});
