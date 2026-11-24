import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import SurveyWizard from '@/components/survey/SurveyWizard.vue';

// Mock scrollTo para evitar errores en entorno de prueba DOM
window.scrollTo = vi.fn() as any;

describe('Componente SurveyWizard.vue (Asistente de 9 Pasos)', () => {
  it('renderiza el paso activo y calcula el porcentaje de avance correcto (11.1% en paso 1)', () => {
    const wrapper = mount(SurveyWizard, {
      props: {
        modelValue: {
          cedula: '12345678',
          parroquia: 'san_simon'
        },
        step: 0
      }
    });

    expect(wrapper.text()).toContain('Paso 1 de 9:');
    expect(wrapper.text()).toContain('Ubicación y Caracterización del Hogar');
    expect(wrapper.text()).toContain('11.1% completado');

    const progressbar = wrapper.find('[role="progressbar"]');
    expect(progressbar.attributes('aria-valuenow')).toBe('11.1');
  });

  it('calcula correctamente el porcentaje en pasos intermedios (ej. 44.4% en paso 4 con residentes)', () => {
    const wrapper = mount(SurveyWizard, {
      props: {
        modelValue: {
          cedula: '12345678',
          parroquia: 'san_simon',
          residentes: [{ nombre_apellido: 'Familiar', edad: 25 }]
        },
        step: 3 // Cuarto paso (índice 3): Composición del Hogar
      }
    });

    expect(wrapper.text()).toContain('Paso 4 de 9:');
    expect(wrapper.text()).toContain('44.4% completado');
  });

  it('incrementa el porcentaje de progreso en tiempo real al responder preguntas dentro de un paso', async () => {
    const wrapper = mount(SurveyWizard, {
      props: {
        modelValue: {
          cedula: '',
          parroquia: ''
        },
        step: 0
      }
    });

    // Inicialmente 0% completado en Paso 1 sin respuestas
    expect(wrapper.find('.progress-percentage').text()).toBe('0% completado');

    // Al seleccionar la parroquia incrementa hasta completar el paso
    await wrapper.setProps({
      modelValue: {
        parroquia: 'san_simon'
      }
    });
    expect(wrapper.find('.progress-percentage').text()).toBe('11.1% completado');
  });

  it('previene el avance si faltan campos obligatorios en el paso actual', async () => {
    const wrapper = mount(SurveyWizard, {
      props: {
        modelValue: {
          parroquia: '' // Parroquia vacía requerida
        },
        step: 0
      }
    });

    // Buscar botón "Siguiente"
    const nextBtn = wrapper.findAll('button').find(b => b.text().includes('Siguiente'));
    expect(nextBtn).toBeDefined();

    await nextBtn!.trigger('click');

    // No debe haber emitido update:step
    expect(wrapper.emitted('update:step')).toBeFalsy();
  });

  it('permite avanzar cuando todas las preguntas del paso están completas', async () => {
    const wrapper = mount(SurveyWizard, {
      props: {
        modelValue: {
          cedula: '12345678',
          parroquia: 'boqueron',
          comunidad_sector: 'Sector Centro',
          zona_residencia_od: 'Boquerón',
          avenida_calle: 'Calle Principal',
          casa_apartamento: 'Casa N° 10'
        },
        step: 0
      }
    });

    const nextBtn = wrapper.findAll('button').find(b => b.text().includes('Siguiente'));
    await nextBtn!.trigger('click');

    // Debe emitir 'update:step' con el paso 1
    const emittedStep = wrapper.emitted('update:step');
    expect(emittedStep).toBeTruthy();
    expect(emittedStep![0]).toEqual([1]);
  });

  it('permite navegar hacia atrás mediante el botón Anterior', async () => {
    const wrapper = mount(SurveyWizard, {
      props: {
        modelValue: {
          cedula: '12345678',
          parroquia: 'boqueron',
          tipo_vivienda: '3'
        },
        step: 1
      }
    });

    const prevBtn = wrapper.findAll('button').find(b => b.text().includes('Anterior'));
    expect(prevBtn).toBeDefined();
    expect(prevBtn!.attributes('disabled')).toBeUndefined();

    await prevBtn!.trigger('click');

    const emittedStep = wrapper.emitted('update:step');
    expect(emittedStep).toBeTruthy();
    expect(emittedStep![0]).toEqual([0]);
  });

  it('la parroquia es una lista desplegable con las 11 parroquias de Maturín con nombres limpios (R4)', () => {
    const wrapper = mount(SurveyWizard, { props: { modelValue: {}, step: 0 } });
    const select = wrapper.find<HTMLSelectElement>('#parroquia');
    expect(select.element.tagName).toBe('SELECT');

    const options = select.findAll('option');
    expect(options[0].element.disabled).toBe(true);
    expect(options).toHaveLength(12);

    const texts = options.map(o => o.text());
    expect(texts).toContain('Alto de Los Godos');
    expect(texts).toContain('San Simón');
    expect(texts).toContain('Las Cocuizas');
    expect(texts.some(t => t.includes('_'))).toBe(false);

    const values = options.map(o => o.element.value);
    expect(values).toContain('san_simon');
    expect(values).toContain('las_cocuizas');
  });

  it('verifica que los campos de los pasos 2, 3 y 6 inicien vacíos con placeholders explicativos (R5)', async () => {
    const wrapper = mount(SurveyWizard, {
      props: {
        modelValue: {},
        step: 1 // Paso 2
      }
    });

    const radios = wrapper.findAll<HTMLInputElement>('input[name="tipo_vivienda"]');
    expect(radios).toHaveLength(7);
    expect(radios.every(r => !r.element.checked)).toBe(true);

    const labels = wrapper.findAll('.survey-radio-option').map(l => l.text());
    expect(labels).toEqual([
      'a.- Quinta o Casa quinta',
      'b.- Casa',
      'c.- Apartamento en edificio',
      'd.- Apartamento en quinta, casa-quinta o casa',
      'e.- Casa de vecindad',
      'f.- Vivienda rústica (rancho)',
      'g.- Otro tipo'
    ]);

    const cuartos = wrapper.find<HTMLInputElement>('#total_cuartos_vivienda');
    expect(cuartos.element.value).toBe('');
    expect(cuartos.attributes('placeholder')).toBeTruthy();

    // "g.- Otro tipo" solo muestra su campo de texto al elegirse
    expect(wrapper.find('#tipo_vivienda_otro').exists()).toBe(false);
    await radios[6].setValue(true);
    const emitted = wrapper.emitted('update:modelValue')!;
    expect((emitted[emitted.length - 1][0] as any).tipo_vivienda).toBe('otro');

    const conOtro = mount(SurveyWizard, { props: { modelValue: { tipo_vivienda: 'otro' }, step: 1 } });
    expect(conOtro.find('#tipo_vivienda_otro').exists()).toBe(true);

    // Verificación Paso 3 (Sección III: Datos del Hogar)
    const wrapperPaso3 = mount(SurveyWizard, {
      props: {
        modelValue: {},
        step: 2 // Paso 3
      }
    });

    const grupos = wrapperPaso3.find<HTMLInputElement>('#grupos_gastos_separados');
    expect(grupos.element.value).toBe('');
    expect(grupos.attributes('placeholder')).toBeTruthy();

    const hogarNum = wrapperPaso3.find<HTMLInputElement>('#hogar_numero');
    expect(hogarNum.element.value).toBe('');
    expect(hogarNum.attributes('placeholder')).toBeTruthy();

    const cuartosDormir = wrapperPaso3.find<HTMLInputElement>('#cuartos_dormir_hogar');
    expect(cuartosDormir.element.value).toBe('');
    expect(cuartosDormir.attributes('placeholder')).toBeTruthy();

    const personasHogar = wrapperPaso3.find<HTMLInputElement>('#numero_personas_hogar');
    expect(personasHogar.element.value).toBe('');
    expect(personasHogar.attributes('placeholder')).toBeTruthy();

    const radiosTenencia = wrapperPaso3.findAll<HTMLInputElement>('input[name="tenencia_vivienda"]');
    expect(radiosTenencia).toHaveLength(8);
    expect(radiosTenencia.every(r => !r.element.checked)).toBe(true);

    const labelsTenencia = wrapperPaso3.findAll('input[name="tenencia_vivienda"] + span').map(s => s.text());
    expect(labelsTenencia).toEqual([
      'a.- Propia pagada totalmente',
      'b.- Propia pagándose',
      'c.- Alquilada',
      'd.- Alquilada parte de la Vivienda',
      'e.- Cedida por razones de trabajo',
      'f.- Cedida por familiar o amigo',
      'g.- Tomada/Invadida',
      'h.- Otra forma'
    ]);

    expect(wrapperPaso3.find('#tenencia_vivienda_otro').exists()).toBe(false);
    await radiosTenencia[7].setValue(true);
    const emittedTenencia = wrapperPaso3.emitted('update:modelValue')!;
    expect((emittedTenencia[emittedTenencia.length - 1][0] as any).tenencia_vivienda).toBe('otra_forma');

    const conOtraForma = mount(SurveyWizard, { props: { modelValue: { tenencia_vivienda: 'otra_forma' }, step: 2 } });
    expect(conOtraForma.find('#tenencia_vivienda_otro').exists()).toBe(true);
  });

  it('redirige, enfoca y resalta automáticamente la primera pregunta faltante al intentar avanzar', async () => {
    const wrapper = mount(SurveyWizard, {
      attachTo: document.body,
      props: {
        modelValue: {
          parroquia: 'san_simon',
          comunidad_sector: 'CENTRO',
          zona_residencia_od: '160805',
          avenida_calle: '',
          casa_apartamento: ''
        },
        step: 0
      }
    });

    const scrollSpy = vi.fn();
    const avenidaInput = wrapper.get('#avenida_calle').element as HTMLInputElement;
    const avenidaContainer = avenidaInput.closest('.survey-field') as HTMLElement;
    avenidaContainer.scrollIntoView = scrollSpy;

    const btnSiguiente = wrapper.findAll('button').find((b) => b.text().includes('Siguiente'));
    await btnSiguiente!.trigger('click');
    await wrapper.vm.$nextTick();

    expect(scrollSpy).toHaveBeenCalledWith({ behavior: 'smooth', block: 'center' });
    expect(document.activeElement).toBe(avenidaInput);
    expect(avenidaContainer.classList.contains('missing-field-highlight')).toBe(true);

    // Al pulsar el segundo error en el banner, salta directamente a casa_apartamento
    const jumpBtns = wrapper.findAll('[data-testid="btn-jump-missing-field"]');
    expect(jumpBtns).toHaveLength(2);
    const casaInput = wrapper.get('#casa_apartamento').element as HTMLInputElement;
    await jumpBtns[1].trigger('click');
    await wrapper.vm.$nextTick();
    expect(document.activeElement).toBe(casaInput);

    wrapper.unmount();
  });

  it('salta la Sección VI (Transporte Público) si ningún viaje en Sección V usó transporte público (Opción A)', async () => {
    const wrapper = mount(SurveyWizard, {
      props: {
        modelValue: {
          viajes: [
            {
              viaje_numero: 1,
              persona_numero: 1,
              origen_direccion: 'Casa',
              zona_od_origen: 'Centro',
              destino_direccion: 'Trabajo',
              zona_od_destino: 'Tipuro',
              hora_salida: '07:00 AM',
              hora_llegada: '07:30 AM',
              motivo_viaje: '1',
              modo_principal: '4', // Automóvil Particular (no público)
              tiempo_viaje_min: 30
            }
          ]
        },
        step: 4 // Sección V: Viajes
      }
    });

    const btnSiguiente = wrapper.findAll('button').find((b) => b.text().includes('Siguiente'));
    await btnSiguiente!.trigger('click');

    const emitted = wrapper.emitted('update:step');
    expect(emitted).toBeDefined();
    // Debe saltar del paso 4 directo al paso 6 (Sección VII: Movilidad Activa), obviando el paso 5 (Transporte Público)
    expect(emitted![emitted!.length - 1]).toEqual([6]);
  });

  it('limpia campos residuales de Sección VI al enviar si no hubo viajes en transporte público', async () => {
    const wrapper = mount(SurveyWizard, {
      props: {
        modelValue: {
          parroquia: 'boqueron',
          comunidad_sector: 'TIPURO',
          zona_residencia_od: 'Sector Tipuro Norte frente a Palma Real',
          avenida_calle: 'Av. Principal',
          casa_apartamento: 'Casa 12',
          tipo_vivienda: 'casa',
          total_cuartos_vivienda: 4,
          grupos_gastos_separados: 1,
          hogar_numero: 1,
          cuartos_dormir_hogar: 2,
          numero_personas_hogar: 1,
          tenencia_vivienda: 'propia_pagada',
          residentes: [
            {
              persona_numero: 1,
              nombres: 'Carlos Pérez',
              parentesco: '1',
              sexo: '1',
              edad: 34,
              sabe_leer_escribir: 'si',
              nivel_educativo: 'universitario',
              actividad_principal: '1',
              medio_transporte_habitual: '4',
              posee_licencia: 'si',
              tiene_vehiculo_disponible: 'si',
              tipo_vehiculo: 'automovil',
              cantidad_vehiculo: 1
            }
          ],
          viajes: [
            {
              viaje_numero: 1,
              persona_numero: 1,
              origen_direccion: 'Casa',
              zona_od_origen: 'Tipuro',
              destino_direccion: 'Oficina',
              zona_od_destino: 'Centro',
              hora_salida: '07:00 AM',
              hora_llegada: '07:30 AM',
              motivo_viaje: '1',
              modo_principal: '4',
              tiempo_viaje_min: 30
            }
          ],
          // Datos residuales de Sección VI llenados previamente
          rutas_tp_dia: 2,
          rutas_tp_utilizadas: ['ruta_01_y_05_union_de_conductores_lucas_perez'],
          calificacion_servicio_tp: 'bueno',
          gasto_semanal_transporte_bs: 150,
          comentarios_transporte_maturin: 'Comentario viejo',
          // Secciones VII, VIII y IX completas
          cambio_movilidad_5_anos: 'no',
          caminatas_mas_10min: 'si',
          usa_bicicleta: 'no',
          dias_camina_bici_semana: 3,
          modo_actividades_centro: 'caminando',
          aceras_adecuadas: 'no',
          seguridad_desplazamiento_centro: 'neutral',
          frecuencia_visita_parques: 'mensual',
          actividades_parques: ['caminar'],
          caminatas_ciudad: 'si',
          seguridad_parques_dia: 'seguro',
          seguridad_parques_noche: 'inseguro',
          limpieza_parques: 'regular',
          impedimentos_espacios: ['inseguridad'],
          satisfaccion_centro: 'regular',
          mejoras_prioritarias: ['iluminacion'],
          parque_mejorar_primero: 'Parque La Guaricha',
          disposicion_participar_mejoras: 'si',
          sugerencias_esparcimiento: 'Más sombra',
          acera_comoda: 'en_desacuerdo',
          sectores_para_caminar: 'Av. Bolívar',
          facilidad_llegada_parques: 'regular',
          esparcimientos_faltantes: ['bancas'],
          cruce_peatonal_todas: 'no',
          hay_semaforo_peatonal: 'no',
          mapas_senales_caminata: 'no',
          movilidad_reducida_sin_ayuda: 'no',
          nombres_calles_visibles: 'si',
          senalizacion_clara_sin_obstaculos: 'no',
          trayecto_pie_parada_seguro: 'inseguro',
          aire_ruido_aceptables: 'no',
          conductores_ceden_paso: 'no',
          ciudad_prioriza_peaton: 'no',
          participacion_consultas_peatonales: 'no',
          planes_movilidad_peatonal_normativa: 'no_se',
          observaciones_generales: 'Todo bien',
          acepta_declaracion: true
        },
        step: 8
      }
    });

    const submitBtn = wrapper.find('.submit-final-btn');
    await submitBtn.trigger('click');

    const submitted = wrapper.emitted('submit');
    expect(submitted).toBeDefined();
    const payload = submitted![0][0] as Record<string, any>;
    expect(payload.rutas_tp_dia).toBeUndefined();
    expect(payload.rutas_tp_utilizadas).toBeUndefined();
    expect(payload.calificacion_servicio_tp).toBeUndefined();
    expect(payload.gasto_semanal_transporte_bs).toBeUndefined();
    expect(payload.comentarios_transporte_maturin).toBeUndefined();
    expect(payload.zona_residencia_od).toBe('Sector Tipuro Norte frente a Palma Real');
  });
});
