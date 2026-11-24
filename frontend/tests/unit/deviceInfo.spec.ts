import { describe, it, expect } from 'vitest';
import { detectDeviceInfo } from '@/utils/deviceInfo';

describe('detectDeviceInfo', () => {
  it('detecta teléfono móvil Android con Chrome', () => {
    const info = detectDeviceInfo({
      userAgent:
        'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
      maxTouchPoints: 5,
      viewportWidth: 390,
      viewportHeight: 844
    });

    expect(info).toEqual({
      dispositivo_tipo: 'movil',
      dispositivo_so: 'Android',
      dispositivo_navegador: 'Chrome',
      dispositivo_viewport: '390x844'
    });
  });

  it('detecta tablet iPadOS (Macintosh + touch points)', () => {
    const info = detectDeviceInfo({
      userAgent:
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
      maxTouchPoints: 5,
      viewportWidth: 820,
      viewportHeight: 1180
    });

    expect(info.dispositivo_tipo).toBe('tablet');
    expect(info.dispositivo_so).toBe('iOS');
    expect(info.dispositivo_navegador).toBe('Safari');
  });

  it('detecta computadora de escritorio Windows con Edge', () => {
    const info = detectDeviceInfo({
      userAgent:
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0',
      maxTouchPoints: 0,
      viewportWidth: 1920,
      viewportHeight: 1080
    });

    expect(info).toEqual({
      dispositivo_tipo: 'escritorio',
      dispositivo_so: 'Windows',
      dispositivo_navegador: 'Edge',
      dispositivo_viewport: '1920x1080'
    });
  });
});

