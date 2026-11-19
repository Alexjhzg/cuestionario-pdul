import { ref, computed } from 'vue';

export interface GpsCoordinates {
  latitude: number;
  longitude: number;
  accuracy: number;
  timestamp: string;
}

const DEFAULT_POSITION_OPTIONS: PositionOptions = {
  enableHighAccuracy: true,
  timeout: 15000,
  maximumAge: 0
};

function mapGeolocationError(err: GeolocationPositionError): string {
  switch (err.code) {
    case 1: // PERMISSION_DENIED
      return 'No se otorgaron permisos de ubicación en el navegador. Puedes habilitar el GPS en la configuración o continuar llenando tu dirección manualmente.';
    case 2: // POSITION_UNAVAILABLE
      return 'La señal GPS es débil o no está disponible en este momento. Intenta acercarte a un espacio abierto o continúa manualmente.';
    case 3: // TIMEOUT
      return 'El dispositivo tardó demasiado en obtener la señal satelital. Intenta nuevamente o continúa manualmente.';
    default:
      return 'No se pudo obtener la ubicación GPS. Puedes continuar ingresando tu dirección manualmente.';
  }
}

export function useGeolocation(customOptions?: PositionOptions) {
  const isLoading = ref(false);
  const coords = ref<GpsCoordinates | null>(null);
  const error = ref<string | null>(null);

  const isSupported = computed<boolean>(() => {
    return (
      typeof navigator !== 'undefined' &&
      'geolocation' in navigator &&
      typeof navigator.geolocation?.getCurrentPosition === 'function'
    );
  });

  function getCurrentLocation(): Promise<GpsCoordinates | null> {
    if (!isSupported.value) {
      error.value =
        'Tu navegador o dispositivo no soporta geolocalización GPS. Puedes continuar ingresando tu dirección manualmente.';
      return Promise.resolve(null);
    }

    isLoading.value = true;
    error.value = null;

    const options: PositionOptions = {
      ...DEFAULT_POSITION_OPTIONS,
      ...customOptions
    };

    return new Promise((resolve) => {
      try {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const captured: GpsCoordinates = {
              latitude: Number(position.coords.latitude.toFixed(6)),
              longitude: Number(position.coords.longitude.toFixed(6)),
              accuracy: Math.round(position.coords.accuracy),
              timestamp: new Date(position.timestamp || Date.now()).toISOString()
            };
            coords.value = captured;
            isLoading.value = false;
            resolve(captured);
          },
          (err) => {
            error.value = mapGeolocationError(err);
            isLoading.value = false;
            resolve(null);
          },
          options
        );
      } catch {
        error.value =
          'Ocurrió un error al consultar el sensor GPS. Puedes continuar ingresando tu dirección manualmente.';
        isLoading.value = false;
        resolve(null);
      }
    });
  }

  function clearLocation() {
    coords.value = null;
    error.value = null;
  }

  return {
    isSupported,
    isLoading,
    coords,
    error,
    getCurrentLocation,
    clearLocation
  };
}

