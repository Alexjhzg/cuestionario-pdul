import type { Page, Request, Response } from '@playwright/test';

export interface AuditFinding {
  type: 'BUG' | 'WARNING' | 'IMPROVEMENT';
  category: 'CONSOLE' | 'NETWORK' | 'LAYOUT' | 'USABILITY' | 'ACCESSIBILITY';
  description: string;
  url: string;
  metadata?: any;
}

export class AuditTracker {
  private findings: AuditFinding[] = [];
  private page: Page;

  constructor(page: Page) {
    this.page = page;
    this.setupListeners();
  }

  private setupListeners() {
    this.page.on('console', (msg) => {
      const type = msg.type();
      const text = msg.text();
      // Filtrar advertencias benignas conocidas de bibliotecas de terceros
      if (text.includes('[Vue warn]: injection') || text.includes('Vite') || text.includes('Download the Vue Devtools')) {
        return;
      }
      if (type === 'error') {
        this.findings.push({
          type: 'BUG',
          category: 'CONSOLE',
          description: `Error en consola de JavaScript: ${text}`,
          url: this.page.url()
        });
      } else if (type === 'warning' && !text.includes('deprecated')) {
        this.findings.push({
          type: 'WARNING',
          category: 'CONSOLE',
          description: `Advertencia en consola: ${text}`,
          url: this.page.url()
        });
      }
    });

    this.page.on('pageerror', (err) => {
      this.findings.push({
        type: 'BUG',
        category: 'CONSOLE',
        description: `Excepción no capturada en la página: ${err.message}`,
        url: this.page.url(),
        metadata: { stack: err.stack }
      });
    });

    this.page.on('response', (response: Response) => {
      const status = response.status();
      const url = response.url();
      // Omitir peticiones esperadas con error (si aplica)
      if (status >= 400 && !url.includes('favicon.ico')) {
        this.findings.push({
          type: status >= 500 ? 'BUG' : 'WARNING',
          category: 'NETWORK',
          description: `Fallo HTTP ${status} en llamada de red: ${url}`,
          url: this.page.url(),
          metadata: { status, requestUrl: url }
        });
      }
    });
  }

  async checkHorizontalOverflow(screenName: string): Promise<void> {
    const overflow = await this.page.evaluate(() => {
      const doc = document.documentElement;
      const body = document.body;
      const scrollWidth = Math.max(doc.scrollWidth, body.scrollWidth);
      const clientWidth = Math.max(doc.clientWidth, body.clientWidth);
      return {
        hasOverflow: scrollWidth > clientWidth,
        scrollWidth,
        clientWidth,
        diff: scrollWidth - clientWidth
      };
    });

    if (overflow.hasOverflow) {
      this.findings.push({
        type: 'BUG',
        category: 'LAYOUT',
        description: `Desbordamiento horizontal detectado en pantalla '${screenName}': scrollWidth (${overflow.scrollWidth}px) > clientWidth (${overflow.clientWidth}px) [diferencia: ${overflow.diff}px]`,
        url: this.page.url(),
        metadata: overflow
      });
    }
  }

  addManualFinding(finding: AuditFinding) {
    this.findings.push(finding);
  }

  getFindings(): AuditFinding[] {
    return [...this.findings];
  }

  clear() {
    this.findings = [];
  }
}

