import { ref, computed, isRef, type Ref } from 'vue';
import type { ViajeOD } from '@/types/survey';

export type { ViajeOD };

export function useTripChain(
  zonaResidenciaRef: Ref<string> | string = '',
  initialViajes: ViajeOD[] = []
) {
  const getZonaResidencia = (): string => {
    return isRef(zonaResidenciaRef) ? zonaResidenciaRef.value : zonaResidenciaRef;
  };

  const viajes = ref<ViajeOD[]>([...initialViajes]);

  const defaultOrigen = computed(() => {
    if (viajes.value.length > 0) {
      const ultimo = viajes.value[viajes.value.length - 1];
      return ultimo.zona_od_destino || getZonaResidencia();
    }
    return getZonaResidencia();
  });

  const nuevoViaje = ref<ViajeOD>({
    viaje_numero: initialViajes.length + 1,
    persona_numero: 1,
    zona_od_origen: defaultOrigen.value,
    zona_od_destino: '',
    motivo_viaje: '',
    modo_principal: '',
    tiempo_viaje_min: 0,
    costo_viaje_bs: 0
  });

  function getSiguienteOrigen(): string {
    if (viajes.value.length === 0) {
      return getZonaResidencia();
    }
    const ultimo = viajes.value[viajes.value.length - 1];
    return ultimo.zona_od_destino || getZonaResidencia();
  }

  function agregarViaje(datos?: Partial<ViajeOD>): ViajeOD {
    const origen = datos?.zona_od_origen || nuevoViaje.value.zona_od_origen || getSiguienteOrigen();
    const viaje: ViajeOD = {
      viaje_numero: viajes.value.length + 1,
      persona_numero: datos?.persona_numero ?? nuevoViaje.value.persona_numero ?? 1,
      zona_od_origen: origen,
      zona_od_destino: datos?.zona_od_destino ?? nuevoViaje.value.zona_od_destino,
      motivo_viaje: datos?.motivo_viaje ?? nuevoViaje.value.motivo_viaje ?? '',
      modo_principal: datos?.modo_principal ?? nuevoViaje.value.modo_principal ?? '',
      tiempo_viaje_min: datos?.tiempo_viaje_min ?? nuevoViaje.value.tiempo_viaje_min ?? 0,
      costo_viaje_bs: datos?.costo_viaje_bs ?? nuevoViaje.value.costo_viaje_bs ?? 0
    };

    viajes.value.push(viaje);

    // Encadenamiento automático: el siguiente origen toma el destino de este viaje
    nuevoViaje.value = {
      viaje_numero: viajes.value.length + 1,
      persona_numero: viaje.persona_numero,
      zona_od_origen: viaje.zona_od_destino,
      zona_od_destino: '',
      motivo_viaje: '',
      modo_principal: '',
      tiempo_viaje_min: 0,
      costo_viaje_bs: 0
    };

    return viaje;
  }

  function crearViajeRegreso(viajeIda: ViajeOD, destinoFinal?: string): ViajeOD {
    const destinoRegreso = destinoFinal || getZonaResidencia() || viajeIda.zona_od_origen;
    return {
      viaje_numero: viajes.value.length + 1,
      persona_numero: viajeIda.persona_numero,
      zona_od_origen: viajeIda.zona_od_destino,
      zona_od_destino: destinoRegreso,
      motivo_viaje: viajeIda.motivo_viaje,
      modo_principal: viajeIda.modo_principal,
      tiempo_viaje_min: viajeIda.tiempo_viaje_min,
      costo_viaje_bs: viajeIda.costo_viaje_bs
    };
  }

  function agregarViajeRegreso(viajeIda: ViajeOD, destinoFinal?: string): ViajeOD {
    const regreso = crearViajeRegreso(viajeIda, destinoFinal);
    viajes.value.push(regreso);

    // Encadenar siguiente viaje tras el regreso
    nuevoViaje.value = {
      viaje_numero: viajes.value.length + 1,
      persona_numero: regreso.persona_numero,
      zona_od_origen: regreso.zona_od_destino,
      zona_od_destino: '',
      motivo_viaje: regreso.motivo_viaje,
      modo_principal: regreso.modo_principal,
      tiempo_viaje_min: regreso.tiempo_viaje_min,
      costo_viaje_bs: regreso.costo_viaje_bs
    };

    return regreso;
  }

  function eliminarViaje(index: number) {
    if (index >= 0 && index < viajes.value.length) {
      viajes.value.splice(index, 1);
      // Renumerar
      viajes.value.forEach((v, idx) => {
        v.viaje_numero = idx + 1;
      });
      nuevoViaje.value.viaje_numero = viajes.value.length + 1;
      nuevoViaje.value.zona_od_origen = getSiguienteOrigen();
    }
  }

  return {
    viajes,
    nuevoViaje,
    defaultOrigen,
    getSiguienteOrigen,
    agregarViaje,
    crearViajeRegreso,
    agregarViajeRegreso,
    eliminarViaje
  };
}
