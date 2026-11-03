import {existsSync} from 'node:fs';
import {defineConfig} from '@playwright/test';
export default defineConfig({
 testDir:'./e2e-pages',workers:1,reporter:'list',
 use:{baseURL:'http://127.0.0.1:8004/RelayOps-AI/',headless:true,
  launchOptions:{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||(existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),args:['--no-sandbox']}},
 webServer:{command:'python ../scripts/pages_preview.py',url:'http://127.0.0.1:8004/RelayOps-AI/',reuseExistingServer:false,timeout:30000}
});
