import { defineConfig, devices } from '@playwright/test';

/* Backend (FastAPI) + static frontend. No new runtime dependencies. */
export default defineConfig({
  testDir: './frontend',
  testMatch: /.*\.spec\.ts/,
  timeout: 60_000,
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:8130',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      command: 'python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000',
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: true,
      timeout: 60_000,
      env: { PYTHONPATH: '.' },
    },
    {
      command: 'python -m http.server 8130 --directory frontend',
      url: 'http://127.0.0.1:8130/index.html',
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
