import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import fs from 'node:fs';
import path from 'node:path';
import Step6TransportePublico from '@/components/survey/sections/Step6TransportePublico.vue';
import SurveyWizard from '@/components/survey/SurveyWizard.vue';
import AdminResponseDetailGrid from '@/components/admin/AdminResponseDetailGrid.vue';
import {
  RUTAS_TRANSPORTE_COLECTIVO,
  RUTAS_TRANSPORTE_OPTIONS,
  RUTAS_TRANSPORTE_LABELS
} from '@/utils/surveyOptions';
import { calculateStepProgress, getStepValidationErrors } from '@/utils/surveyStepValidation';
import { formatRutasTpUtilizadas } from '@/utils/responseFormatters';
import { validateFormioSchema } from '@/utils/schemaValidator';

describe('R1 — Catálogo de Rutas de Transporte Colectivo y Sección VI', () => {
  describe('1. Integridad del catálogo compartido (@shared/catalogs/rutas_transporte_maturin.json)', () => {
    it('contiene exactamente 103 rutas colectivas únicas con códigos snake_case válidos y sin líneas exclusivas de TAXI', () => {
      expect(RUTAS_TRANSPORTE_COLECTIVO).toHaveLength(103);
      expect(RUTAS_TRANSPORTE_OPTIONS).toHaveLength(104); // 103 + 'otra'
      expect(RUTAS_TRANSPORTE_LABELS.otra).toBe('Otra');

      const seenCodes = new Set<string>();
      for (const ruta of RUTAS_TRANSPORTE_COLECTIVO) {
        expect(ruta.codigo).toMatch(/^[a-z0-9_]+$/);
        expect(ruta.value).toBe(ruta.codigo);
        expect(ruta.codigo).not.toBe('otra');
        expect(seenCodes.has(ruta.codigo)).toBe(false);
        seenCodes.add(ruta.codigo);

        // Ninguna ruta debe tener TAXI como modalidad
        expect(ruta.modalidades).not.toContain('TAXI');
        expect(ruta.modalidades.length).toBeGreaterThan(0);
        expect(RUTAS_TRANSPORTE_LABELS[ruta.codigo]).toBe(ruta.nombre);
      }

      // Incluye RUTA 07 (POR PUESTO) y normaliza URBSNO -> URBANO en RUTA 86
      const ruta07 = RUTAS_TRANSPORTE_COLECTIVO.find((r) => r.codigo === 'ruta_07_a_civil_union_paraiso');
      expect(ruta07).toBeDefined();
      expect(ruta07?.modalidades).toContain('POR PUESTO');

      const ruta86 = RUTAS_TRANSPORTE_COLECTIVO.find(
        (r) => r.codigo === 'ruta_86_a_coop_mancomunidad_bolivariana_rl'
      );
      expect(ruta86).toBeDefined();
      expect(ruta86?.modalidades).toContain('URBANO');
      expect(ruta86?.modalidades).not.toContain('URBSNO');

      // Excluye líneas exclusivas de TAXI
      const names = RUTAS_TRANSPORTE_COLECTIVO.map((r) => r.nombre);
      expect(names).not.toContain('ASOCIACIÓN CIVIL TAXIS DEL ESTE');
      expect(names).not.toContain('A. CIVIL TAXIS EJECUTIVO THE POWER LINE MONAGAS');
    });

    it('ordena naturalmente las líneas RUTA XX primero (01 a 110) seguidas de las demás en orden alfabético', () => {
      const idxRuta01 = RUTAS_TRANSPORTE_COLECTIVO.findIndex((r) => r.nombre.startsWith('RUTA 01'));
      const idxRuta11 = RUTAS_TRANSPORTE_COLECTIVO.findIndex((r) => r.nombre.startsWith('RUTA 11 '));
      const idxRuta100 = RUTAS_TRANSPORTE_COLECTIVO.findIndex((r) => r.nombre.startsWith('RUTA 100'));
      const idxRuta110 = RUTAS_TRANSPORTE_COLECTIVO.findIndex((r) => r.nombre.startsWith('RUTA 110'));
      const idxNonRuta = RUTAS_TRANSPORTE_COLECTIVO.findIndex((r) => !r.nombre.startsWith('RUTA'));

      expect(idxRuta01).toBe(0);
      expect(idxRuta11).toBeGreaterThan(idxRuta01);
      expect(idxRuta100).toBeGreaterThan(idxRuta11);
      expect(idxRuta110).toBeGreaterThan(idxRuta100);
      expect(idxNonRuta).toBeGreaterThan(idxRuta110);
    });
  });

  describe('2. Componente Step6TransportePublico.vue y flujo en SurveyWizard.vue', () => {
    it('renderiza #rutas_tp_dia y el selector #rutas_tp_utilizadas en estado inicial en blanco', () => {
      const wrapper = mount(Step6TransportePublico, {
        props: {
          modelValue: {
            rutas_tp_dia: '',
            rutas_tp_utilizadas: [],
            rutas_tp_utilizadas_otra: ''
          }
        }
      });

      expect(wrapper.find('#rutas_tp_dia').exists()).toBe(true);
      expect(wrapper.find('#rutas_tp_utilizadas').exists()).toBe(true);
      expect(wrapper.find('#rutas_tp_utilizadas_search').exists()).toBe(true);
      expect(wrapper.findAll('input[name="rutas_tp_utilizadas"]')).toHaveLength(104); // 103 + otra
      expect(wrapper.find('#rutas_tp_utilizadas_otra').exists()).toBe(false);
    });

    it('filtra rutas sin distinguir tildes ni mayúsculas y mantiene siempre visible la opción «Otra»', async () => {
      const wrapper = mount(Step6TransportePublico, {
        props: {
          modelValue: {
            rutas_tp_dia: 2,
            rutas_tp_utilizadas: []
          }
        }
      });

      const searchInput = wrapper.find('#rutas_tp_utilizadas_search');
      await searchInput.setValue('paraiso');

      const checkboxes = wrapper.findAll('input[name="rutas_tp_utilizadas"]');
      const values = checkboxes.map((cb) => cb.attributes('value'));
      expect(values).toContain('ruta_07_a_civil_union_paraiso');
      expect(values).toContain('otra');

      // Búsqueda sin coincidencias en catálogo sigue mostrando «otra»
      await searchInput.setValue('ruta_inexistente_xyz_999');
      const noMatchCheckboxes = wrapper.findAll('input[name="rutas_tp_utilizadas"]');
      expect(noMatchCheckboxes).toHaveLength(1);
      expect(noMatchCheckboxes[0].attributes('value')).toBe('otra');
      expect(wrapper.find('.routes-empty-msg').exists()).toBe(true);
    });

    it('emite toggle-multi, muestra chips removibles y revela/limpia el campo «Otra»', async () => {
      const wrapper = mount(Step6TransportePublico, {
        props: {
          modelValue: {
            rutas_tp_dia: 2,
            rutas_tp_utilizadas: ['ruta_01_y_05_union_de_conductores_lucas_perez', 'otra'],
            rutas_tp_utilizadas_otra: 'Línea Comunal Centro'
          }
        }
      });

      // Chips visibles
      const chips = wrapper.findAll('.route-chip');
      expect(chips).toHaveLength(2);
      expect(wrapper.text()).toContain('RUTA 01 Y 05 UNION DE CONDUCTORES "LUCAS PEREZ"');
      expect(wrapper.text()).toContain('Otra: Línea Comunal Centro');

      // Input de texto libre visible
      const otraInput = wrapper.find('#rutas_tp_utilizadas_otra');
      expect(otraInput.exists()).toBe(true);
      await otraInput.setValue('Ruta Nueva 2026');
      expect(wrapper.emitted('update-field')).toContainEqual([
        'rutas_tp_utilizadas_otra',
        'Ruta Nueva 2026'
      ]);

      // Al desmarcar 'otra', emite toggle-multi y limpia rutas_tp_utilizadas_otra
      const otraCheckbox = wrapper.find('input[name="rutas_tp_utilizadas"][value="otra"]');
      await otraCheckbox.trigger('change');
      expect(wrapper.emitted('toggle-multi')).toContainEqual(['rutas_tp_utilizadas', 'otra']);
      expect(wrapper.emitted('update-field')).toContainEqual(['rutas_tp_utilizadas_otra', '']);
    });

    it('oculta el selector de rutas y limpia selección y campo «Otra» cuando rutas_tp_dia se cambia a 0', async () => {
      const wrapper = mount(Step6TransportePublico, {
        props: {
          modelValue: {
            rutas_tp_dia: 2,
            rutas_tp_utilizadas: ['ruta_02_a_civil_linea_conductores_la_pica', 'otra'],
            rutas_tp_utilizadas_otra: 'Mi ruta'
          }
        }
      });

      await wrapper.find('#rutas_tp_dia').setValue('0');
      expect(wrapper.emitted('update-field')).toContainEqual(['rutas_tp_dia', 0]);
      expect(wrapper.emitted('update-field')).toContainEqual(['rutas_tp_utilizadas', []]);
      expect(wrapper.emitted('update-field')).toContainEqual(['rutas_tp_utilizadas_otra', '']);

      // Con rutas_tp_dia === 0, el selector no se renderiza
      await wrapper.setProps({
        modelValue: {
          rutas_tp_dia: 0,
          rutas_tp_utilizadas: [],
          rutas_tp_utilizadas_otra: ''
        }
      });
      expect(wrapper.find('#rutas_tp_utilizadas').exists()).toBe(false);

      // Cadena solo de espacios no se trata como 0
      await wrapper.setProps({
        modelValue: {
          rutas_tp_dia: '   ',
          rutas_tp_utilizadas: [],
          rutas_tp_utilizadas_otra: ''
        }
      });
      expect(wrapper.find('#rutas_tp_utilizadas').exists()).toBe(true);
    });

    it('integra toggleMultiSelect y limpieza batching dentro de SurveyWizard en el paso 6', async () => {
      let state: Record<string, any> = {
        rutas_tp_dia: 1,
        rutas_tp_utilizadas: [],
        rutas_tp_utilizadas_otra: ''
      };

      const wrapper = mount(SurveyWizard, {
        props: {
          modelValue: state,
          step: 5,
          'onUpdate:modelValue': async (nextVal: Record<string, any>) => {
            state = nextVal;
            await wrapper.setProps({ modelValue: state });
          }
        }
      });

      const cbOtra = wrapper.find('input[name="rutas_tp_utilizadas"][value="otra"]');
      await cbOtra.trigger('change');
      await nextTick();
      expect(state.rutas_tp_utilizadas).toEqual(['otra']);

      await wrapper.find('#rutas_tp_utilizadas_otra').setValue('Ruta Las Cocuizas');
      await nextTick();
      expect(state.rutas_tp_utilizadas_otra).toBe('Ruta Las Cocuizas');

      // Desmarcar 'otra' debe removerla y limpiar rutas_tp_utilizadas_otra
      await wrapper.find('input[name="rutas_tp_utilizadas"][value="otra"]').trigger('change');
      await nextTick();
      expect(state.rutas_tp_utilizadas).toEqual([]);
      expect(state.rutas_tp_utilizadas_otra).toBe('');
    });
  });

  describe('3. Validación y progreso en surveyStepValidation.ts', () => {
    const baseValidStep6 = {
      tiempo_espera_paradas_min: 15,
      km_residencia_parada: 0.5,
      dificultades_acceso_tp: 'no',
      calificacion_servicio_tp: 'bueno',
      gasto_semanal_transporte_bs: 100,
      acuerdo_rutas_directas: 'de_acuerdo',
      comentarios_transporte_maturin: 'Sin comentarios'
    };

    it('acepta rutas_tp_dia = 0 sin requerir rutas seleccionadas y calcula progreso 1', () => {
      const data = { ...baseValidStep6, rutas_tp_dia: 0, rutas_tp_utilizadas: [] };
      expect(getStepValidationErrors(5, data)).toEqual([]);
      expect(calculateStepProgress(5, data)).toBe(1);
    });

    it('exige al menos una ruta cuando rutas_tp_dia > 0 y texto libre cuando se marca «Otra»', () => {
      const missingRoutes = getStepValidationErrors(5, {
        ...baseValidStep6,
        rutas_tp_dia: 2,
        rutas_tp_utilizadas: []
      });
      expect(missingRoutes.some((e) => e.field === 'rutas_tp_utilizadas')).toBe(true);

      const missingOtraText = getStepValidationErrors(5, {
        ...baseValidStep6,
        rutas_tp_dia: 1,
        rutas_tp_utilizadas: ['otra'],
        rutas_tp_utilizadas_otra: '   '
      });
      expect(missingOtraText.some((e) => e.field === 'rutas_tp_utilizadas_otra')).toBe(true);

      const validWithRoutes = {
        ...baseValidStep6,
        rutas_tp_dia: 2,
        rutas_tp_utilizadas: ['ruta_01_y_05_union_de_conductores_lucas_perez', 'otra'],
        rutas_tp_utilizadas_otra: 'Ruta Comunal'
      };
      expect(getStepValidationErrors(5, validWithRoutes)).toEqual([]);
      expect(calculateStepProgress(5, validWithRoutes)).toBe(1);
    });

    it('soporta diccionario legado de Form.io en rutas_tp_utilizadas', () => {
      const errors = getStepValidationErrors(5, {
        ...baseValidStep6,
        rutas_tp_dia: 1,
        rutas_tp_utilizadas: { ruta_02_a_civil_linea_conductores_la_pica: true }
      });
      expect(errors).toEqual([]);
    });
  });

  describe('4. Formateo y visualización en AdminResponseDetailGrid.vue', () => {
    it('formatea códigos de catálogo, opción «Otra» y objeto legado con formatRutasTpUtilizadas', () => {
      expect(
        formatRutasTpUtilizadas(
          ['ruta_01_y_05_union_de_conductores_lucas_perez', 'otra'],
          'Ruta Express'
        )
      ).toEqual([
        'RUTA 01 Y 05 UNION DE CONDUCTORES "LUCAS PEREZ"',
        'Otra: Ruta Express'
      ]);

      expect(
        formatRutasTpUtilizadas({ ruta_07_a_civil_union_paraiso: true, otra: false })
      ).toEqual(['RUTA 07 / A. CIVIL UNION PARAISO']);

      expect(formatRutasTpUtilizadas([], '')).toEqual([]);
    });

    it('muestra las rutas formateadas en AdminResponseDetailGrid.vue', () => {
      const wrapper = mount(AdminResponseDetailGrid, {
        props: {
          maskPii: true,
          displayData: {
            rutas_tp_dia: 2,
            rutas_tp_utilizadas: ['ruta_06_a_civil_union_de_conductores_juanico', 'otra'],
            rutas_tp_utilizadas_otra: 'Línea Las Cayenas'
          }
        }
      });

      const cell = wrapper.get('[data-testid="admin-detail-rutas-tp"]');
      expect(cell.text()).toContain('RUTA 06 / A. CIVIL UNION DE CONDUCTORES JUANICO');
      expect(cell.text()).toContain('Otra: Línea Las Cayenas');
    });
  });

  describe('5. Validación del esquema Form.io (shared/schemas/pdul_origen_destino.json)', () => {
    it('contiene rutas_tp_utilizadas (104 valores) y rutas_tp_utilizadas_otra válidos en panel_seccion_vi', () => {
      const schemaPath = path.resolve(__dirname, '../../../shared/schemas/pdul_origen_destino.json');
      const schema = JSON.parse(fs.readFileSync(schemaPath, 'utf-8'));

      const validation = validateFormioSchema(schema, { requireSubmit: true, requireParroquia: true });
      expect(validation.valid).toBe(true);
      expect(validation.errors).toEqual([]);

      const panelVi = schema.components.find((c: any) => c.key === 'panel_seccion_vi');
      const rutasSelect = panelVi.components.find((c: any) => c.key === 'rutas_tp_utilizadas');
      const rutasOtra = panelVi.components.find((c: any) => c.key === 'rutas_tp_utilizadas_otra');

      expect(rutasSelect).toBeDefined();
      expect(rutasSelect.multiple).toBe(true);
      expect(rutasSelect.data.values).toHaveLength(104);
      expect(rutasOtra).toBeDefined();
      expect(rutasOtra.conditional).toEqual({
        show: true,
        when: 'rutas_tp_utilizadas',
        eq: 'otra'
      });
    });
  });
});
