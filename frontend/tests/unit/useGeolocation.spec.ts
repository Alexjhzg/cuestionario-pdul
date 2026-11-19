import { describe, it, expect, vi, afterEach } from 'vitest';
import { useGeolocation } from '@/composables/useGeolocation';

describe('useGeolocation composable', () => {
  const originalGeolocation = navigator.geolocation;

  afterEach(() => {
    Object.defineProperty(navigator, 'geolocation', {
      value: originalGeolocation,
      configurable: true,
      writable: true
    });
    vi.restoreAllMocks();
  });

  it('captura coordenadas GPS con alta precisión y redondea valores correctamente', async () => {
    const mockGetCurrentPosition = vi.fn((success: PositionCallback) => {
      success({
        coords: {
          latitude: 9.74581234,
          longitude: -63.18320498,
          accuracy: 5.7,
          altitude: null,
          altitudeAccuracy: null,
          heading: null,
          speed: null,
          toJSON: () => ({})
        },
        timestamp: 1732032000000,
        toJSON: () => ({})
      } as GeolocationPosition);
    });

    Object.defineProperty(navigator, 'geolocation', {
      value: { getCurrentPosition: mockGetCurrentPosition },
      configurable: true
    });

    const { isSupported, isLoading, coords, error, getCurrentLocation, clearLocation } =
      useGeolocation();

    expect(isSupported.value).toBe(true);
    const result = await getCurrentLocation();

    expect(mockGetCurrentPosition).toHaveBeenCalledTimes(1);
    expect(isLoading.value).toBe(false);
    expect(error.value).toBeNull();
    expect(result).toEqual({
      latitude: 9.745812,
      longitude: -63.183205,
      accuracy: 6,
      timestamp: new Date(1732032000000).toISOString()
    });
    expect(coords.value).toEqual(result);

    clearLocation();
    expect(coords.value).toBeNull();
    expect(error.value).toBeNull();
  });

  it('maneja error PERMISSION_DENIED con mensaje amigable en español', async () => {
    const mockGetCurrentPosition = vi.fn((_s: PositionCallback, errCb?: PositionErrorCallback) => {
      errCb?.({
        code: 1,
        message: 'User denied Geolocation',
        PERMISSION_DENIED: 1,
        POSITION_UNAVAILABLE: 2,
        TIMEOUT: 3
      } as GeolocationPositionError);
    });

    Object.defineProperty(navigator, 'geolocation', {
      value: { getCurrentPosition: mockGetCurrentPosition },
      configurable: true
    });

    const { error, coords, getCurrentLocation } = useGeolocation();
    const result = await getCurrentLocation();

    expect(result).toBeNull();
    expect(coords.value).toBeNull();
    expect(error.value).toContain('permisos de ubicación');
  });

  it('maneja error TIMEOUT con mensaje amigable en español', async () => {
    const mockGetCurrentPosition = vi.fn((_s: PositionCallback, errCb?: PositionErrorCallback) => {
      errCb?.({
        code: 3,
        message: 'Timeout expired',
        PERMISSION_DENIED: 1,
        POSITION_UNAVAILABLE: 2,
        TIMEOUT: 3
      } as GeolocationPositionError);
    });

    Object.defineProperty(navigator, 'geolocation', {
      value: { getCurrentPosition: mockGetCurrentPosition },
      configurable: true
    });

    const { error, getCurrentLocation } = useGeolocation();
    const result = await getCurrentLocation();

    expect(result).toBeNull();
    expect(error.value).toContain('tardó demasiado');
  });

  it('reporta error claro cuando el navegador no soporta geolocalización', async () => {
    Object.defineProperty(navigator, 'geolocation', {
      value: undefined,
      configurable: true
    });

    const { isSupported, error, getCurrentLocation } = useGeolocation();
    expect(isSupported.value).toBe(false);

    const result = await getCurrentLocation();
    expect(result).toBeNull();
    expect(error.value).toContain('no soporta geolocalización');
  });
});

