import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import fs from 'node:fs';
import path from 'node:path';
import App from '@/App.vue';
import SurveyWizard from '@/components/survey/SurveyWizard.vue';

function hexToRelativeLuminance(hex: string): number {
  const clean = hex.trim().replace('#', '');
  const full = clean.length === 3 ? clean.split('').map((c) => c + c).join('') : clean;
  const r8 = parseInt(full.slice(0, 2), 16) / 255;
  const g8 = parseInt(full.slice(2, 4), 16) / 255;
  const b8 = parseInt(full.slice(4, 6), 16) / 255;

  const linearize = (v: number) => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4));
  return 0.2126 * linearize(r8) + 0.7152 * linearize(g8) + 0.0722 * linearize(b8);
}

function contrastRatio(fgHex: string, bgHex: string): number {
  const l1 = hexToRelativeLuminance(fgHex);
  const l2 = hexToRelativeLuminance(bgHex);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

function collectFiles(dir: string, extensions: Set<string>, out: string[] = []): string[] {
  if (!fs.existsSync(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === 'node_modules' || entry.name === '.venv' || entry.name === '__pycache__' || entry.name === 'dist') {
      continue;
    }
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      collectFiles(full, extensions, out);
    } else if (extensions.has(path.extname(entry.name))) {
      out.push(full);
    }
  }
  return out;
}

describe('Fase 5 - Auditoría de Soberanía Tecnológica, Contraste Cromático y Teclado WAI-ARIA', () => {
  const repoRoot = path.resolve(__dirname, '../../../');
  const frontendRoot = path.resolve(__dirname, '../..');

  it('Soberanía Tecnológica: cero llamadas a CDNs externos, Google Fonts, Google Maps o APIs propietarias', () => {
    const forbiddenExternalHosts = [
      'fonts.googleapis.com',
      'fonts.gstatic.com',
      'cdn.jsdelivr.net',
      'unpkg.com',
      'cdnjs.cloudflare.com',
      'cdn.form.io',
      'api.form.io',
      'maps.googleapis.com',
      'api.mapbox.com',
      'googletagmanager.com',
      'google-analytics.com'
    ];

    const filesToAudit = [
      path.join(frontendRoot, 'index.html'),
      ...collectFiles(path.join(frontendRoot, 'src'), new Set(['.ts', '.vue', '.css', '.html', '.json'])),
      ...collectFiles(path.join(repoRoot, 'backend/app'), new Set(['.py', '.json'])),
      ...collectFiles(path.join(repoRoot, 'shared'), new Set(['.ts', '.json', '.geojson']))
    ];

    expect(filesToAudit.length).toBeGreaterThan(30);

    for (const filePath of filesToAudit) {
      const content = fs.readFileSync(filePath, 'utf-8');
      for (const host of forbiddenExternalHosts) {
        expect(content, `Host externo prohibido '${host}' detectado en ${filePath}`).not.toContain(host);
      }
    }

    // Confirmar neutralización explícita de CDNs en FormioBuilder.vue
    const builderContent = fs.readFileSync(
      path.join(frontendRoot, 'src/components/admin/FormioBuilder.vue'),
      'utf-8'
    );
    expect(builderContent).toContain("setBaseUrl('')");
    expect(builderContent).toContain("setProjectUrl('')");
  });

  it('Contraste Cromático WCAG AA/AAA (>= 17.8:1 en tinta primaria) y blancos táctiles (>= 48px / 52px)', () => {
    const tokensCss = fs.readFileSync(path.join(frontendRoot, 'src/assets/styles/tokens.css'), 'utf-8');

    const getTokenHex = (varName: string): string => {
      const match = tokensCss.match(new RegExp(`${varName}:\\s*(#[0-9a-fA-F]{3,6})`));
      expect(match, `Token ${varName} debe existir en tokens.css`).not.toBeNull();
      return match![1];
    };

    const midnightInk = getTokenHex('--color-midnight-ink');
    const graphiteBody = getTokenHex('--color-graphite-body');
    const snowCanvas = getTokenHex('--color-snow-canvas');
    const lavenderWash = getTokenHex('--color-lavender-wash');
    const royalSignal = getTokenHex('--color-royal-signal');
    const slateCaption = getTokenHex('--color-slate-caption');

    // Tinta principal institucional >= 17.8:1 sobre fondo blanco, canvas y lavender wash
    expect(contrastRatio(midnightInk, '#ffffff')).toBeGreaterThanOrEqual(17.8);
    expect(contrastRatio(midnightInk, snowCanvas)).toBeGreaterThanOrEqual(17.8);
    expect(contrastRatio(midnightInk, lavenderWash)).toBeGreaterThanOrEqual(17.8);
    expect(contrastRatio(graphiteBody, '#ffffff')).toBeGreaterThanOrEqual(17.8);

    // Acento primario con texto blanco >= 4.5:1 (WCAG AA) y subtítulos >= 7:1
    expect(contrastRatio('#ffffff', royalSignal)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(slateCaption, '#ffffff')).toBeGreaterThanOrEqual(7.0);

    // Ergonomía táctil base y pointer coarse
    expect(tokensCss).toContain('--min-touch-target: 48px;');
    expect(tokensCss).toMatch(/@media\s*\(pointer:\s*coarse\)[\s\S]*--min-touch-target:\s*52px;/);
  });

  it('Accesibilidad de Teclado WAI-ARIA: navegación completa por flechas, Home, End y paneles semánticos', async () => {
    const wrapper = mount(App, {
      props: {
        adminMode: true
      },
      global: {
        stubs: {
          DashboardView: true,
          AdminSurveyListView: true,
          AdminResponsesView: true,
          FormBuilderView: true,
          SurveyFillView: true,
          Toast: true
        }
      }
    });

    const tablist = wrapper.find('[role="tablist"]');
    expect(tablist.exists()).toBe(true);

    const tabs = wrapper.findAll('[role="tab"]');
    expect(tabs.length).toBeGreaterThanOrEqual(4);
    expect(tabs[0].attributes('aria-selected')).toBe('true');

    // Navegación ArrowRight
    await tabs[0].trigger('keydown', { key: 'ArrowRight' });
    await nextTick();
    expect(tabs[1].attributes('aria-selected')).toBe('true');

    // Navegación End -> última pestaña visible (#tab-survey-fill)
    await tabs[1].trigger('keydown', { key: 'End' });
    await nextTick();
    const lastTab = wrapper.find('#tab-survey-fill');
    expect(lastTab.attributes('aria-selected')).toBe('true');

    // Navegación ArrowLeft -> salta el tab oculto #tab-form-builder y cae en #tab-admin-responses
    await lastTab.trigger('keydown', { key: 'ArrowLeft' });
    await nextTick();
    const responsesTab = wrapper.find('#tab-admin-responses');
    expect(responsesTab.attributes('aria-selected')).toBe('true');

    // Navegación Home -> primera pestaña visible
    await responsesTab.trigger('keydown', { key: 'Home' });
    await nextTick();
    expect(tabs[0].attributes('aria-selected')).toBe('true');
  });

  it('Wizard Ciudadano conserva landmarks WAI-ARIA, barra de progreso y botones tipados accesibles', () => {
    const wrapper = mount(SurveyWizard, {
      props: {
        modelValue: {
          parroquia: 'san_simon',
          residentes: [],
          viajes: [],
          acepta_declaracion: true
        },
        step: 0
      }
    });

    const progress = wrapper.find('[role="progressbar"]');
    expect(progress.exists()).toBe(true);
    expect(progress.attributes('aria-valuemin')).toBe('0');
    expect(progress.attributes('aria-valuemax')).toBe('100');

    const stepItems = wrapper.findAll('.step-indicator-item');
    const stepBtns = wrapper.findAll('.step-indicator-btn');
    expect(stepItems).toHaveLength(9);
    expect(stepBtns).toHaveLength(9);
    expect(stepItems[0].attributes('aria-current')).toBe('step');
    for (const btn of stepBtns) {
      expect(btn.attributes('type')).toBe('button');
    }
  });
});
