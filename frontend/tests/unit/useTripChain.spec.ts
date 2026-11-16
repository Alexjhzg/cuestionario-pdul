import { describe, it, expect } from 'vitest';
import { ref } from 'vue';
import { useTripChain } from '@/composables/useTripChain';

describe('Composable useTripChain (Encadenamiento Inteligente y Viaje de Regreso)', () => {
  it('pre-llena el origen con la zona de residencia del hogar cuando no hay viajes previos', () => {
    const zonaResidencia = ref('alto_de_los_godos');
    const { nuevoViaje, getSiguienteOrigen } = useTripChain(zonaResidencia);

    expect(getSiguienteOrigen()).toBe('alto_de_los_godos');
    expect(nuevoViaje.value.zona_od_origen).toBe('alto_de_los_godos');
  });

  it('encadena correctamente origen_siguiente = destino_anterior tras registrar un viaje', () => {
    const { viajes, nuevoViaje, agregarViaje, getSiguienteOrigen } = useTripChain('san_simon');

    // Registrar primer viaje: de San Simón (hogar) a Las Cocuizas (trabajo)
    agregarViaje({
      zona_od_origen: 'san_simon',
      zona_od_destino: 'las_cocuizas',
      modo_principal: '6',
      tiempo_viaje_min: 35
    });

    expect(viajes.value).toHaveLength(1);
    expect(viajes.value[0].viaje_numero).toBe(1);
    expect(viajes.value[0].zona_od_origen).toBe('san_simon');
    expect(viajes.value[0].zona_od_destino).toBe('las_cocuizas');

    // El siguiente viaje debe tener como origen automático el destino anterior ('las_cocuizas')
    expect(getSiguienteOrigen()).toBe('las_cocuizas');
    expect(nuevoViaje.value.zona_od_origen).toBe('las_cocuizas');
    expect(nuevoViaje.value.zona_od_destino).toBe('');

    // Registrar segundo viaje encadenado: de Las Cocuizas a Boquerón
    agregarViaje({
      zona_od_destino: 'boqueron',
      modo_principal: '4',
      tiempo_viaje_min: 20
    });

    expect(viajes.value).toHaveLength(2);
    expect(viajes.value[1].viaje_numero).toBe(2);
    expect(viajes.value[1].zona_od_origen).toBe('las_cocuizas');
    expect(viajes.value[1].zona_od_destino).toBe('boqueron');

    // Ahora el tercer viaje se encadena desde Boquerón
    expect(getSiguienteOrigen()).toBe('boqueron');
    expect(nuevoViaje.value.zona_od_origen).toBe('boqueron');
  });

  it('genera viaje de retorno invirtiendo origen y destino en 1 toque hacia la residencia', () => {
    const zonaResidencia = 'santa_cruz';
    const { viajes, agregarViaje, agregarViajeRegreso } = useTripChain(zonaResidencia);

    // Viaje de ida: Santa Cruz -> San Simón (Centro)
    const viajeIda = agregarViaje({
      persona_numero: 2,
      zona_od_origen: 'santa_cruz',
      zona_od_destino: 'san_simon',
      modo_principal: '6',
      tiempo_viaje_min: 40,
      costo_viaje_bs: 15
    });

    expect(viajes.value).toHaveLength(1);

    // Acción rápida en 1 toque: Retorno a casa
    const viajeRegreso = agregarViajeRegreso(viajeIda);

    expect(viajes.value).toHaveLength(2);
    expect(viajeRegreso.viaje_numero).toBe(2);
    expect(viajeRegreso.persona_numero).toBe(2);
    // El origen del retorno es el destino de ida
    expect(viajeRegreso.zona_od_origen).toBe('san_simon');
    // El destino del retorno es la residencia ('santa_cruz')
    expect(viajeRegreso.zona_od_destino).toBe('santa_cruz');
    // Copia el modo de transporte y tiempo estimado
    expect(viajeRegreso.modo_principal).toBe('6');
    expect(viajeRegreso.tiempo_viaje_min).toBe(40);
    expect(viajeRegreso.costo_viaje_bs).toBe(15);
  });

  it('elimina un viaje de la lista y renumera secuencialmente los viajes restantes', () => {
    const { viajes, agregarViaje, eliminarViaje } = useTripChain('la_cruz');

    agregarViaje({ zona_od_destino: 'san_simon' });    // Viaje 1
    agregarViaje({ zona_od_destino: 'las_cocuizas' }); // Viaje 2
    agregarViaje({ zona_od_destino: 'la_cruz' });      // Viaje 3

    expect(viajes.value).toHaveLength(3);

    // Eliminar el segundo viaje (índice 1)
    eliminarViaje(1);

    expect(viajes.value).toHaveLength(2);
    expect(viajes.value[0].viaje_numero).toBe(1);
    expect(viajes.value[0].zona_od_destino).toBe('san_simon');
    expect(viajes.value[1].viaje_numero).toBe(2);
    expect(viajes.value[1].zona_od_destino).toBe('la_cruz');
  });
});
