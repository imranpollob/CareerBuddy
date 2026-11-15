import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, timeout: 60000,
  use: { baseURL: 'http://127.0.0.1:5173', channel: 'chrome', trace: 'retain-on-failure' },
  projects: [{name:'desktop',use:{viewport:{width:1440,height:1000}}}, {name:'mobile',use:{...devices['iPhone 13'], defaultBrowserType:'chromium'}}],
  webServer: [
    {command:'../.venv/bin/uvicorn backend.api:app --app-dir .. --host 127.0.0.1 --port 8000',url:'http://127.0.0.1:8000/api/health',env:{SKILLPILOT_SEED_ACCOUNTS:'true',SKILLPILOT_AI_MODE:'mock',SKILLPILOT_REPOSITORY:'memory',SKILLPILOT_ACTOR_CREDENTIALS_PATH:'../.local/test-actor-accounts.json'},reuseExistingServer:false},
    {command:'npm run dev',url:'http://127.0.0.1:5173',reuseExistingServer:false},
  ],
})
