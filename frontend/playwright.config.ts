import { defineConfig, devices } from '@playwright/test';

/**
 * Configuración de Playwright para el Auditor Integral de Funcionalidad
 * Cuestionario Origen-Destino PDUL Maturín
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 60000,
  expect: {
    timeout: 10000
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1, // Ejecución secuencial para no generar carreras en la base de datos
  reporter: [
    ['list'],
    ['json', { outputFile: 'playwright-report/audit-results.json' }],
    ['html', { outputFolder: 'playwright-report', open: 'never' }]
  ],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // Vista desktop estándar
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true
  },
  projects: [
    {
      name: 'desktop-chromium',
      use: {
        ...devices['Desktop Chrome']
      }
    },
    {
      name: 'mobile-portrait',
      use: {
        viewport: { width: 360, height: 740 },
        isMobile: true,
        hasTouch: true
      }
    }
  ]
});

