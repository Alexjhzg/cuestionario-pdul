export type TipoDispositivo = 'movil' | 'tablet' | 'escritorio';

export interface DeviceMetadata {
  dispositivo_tipo: TipoDispositivo;
  dispositivo_so: string;
  dispositivo_navegador: string;
  dispositivo_viewport?: string;
}

export interface DeviceDetectionInput {
  userAgent?: string;
  maxTouchPoints?: number;
  viewportWidth?: number;
  viewportHeight?: number;
  uaDataMobile?: boolean;
}

export function detectDeviceInfo(input?: DeviceDetectionInput): DeviceMetadata {
  const nav = typeof navigator !== 'undefined' ? navigator : undefined;
  const win = typeof window !== 'undefined' ? window : undefined;

  const ua = input?.userAgent ?? nav?.userAgent ?? '';
  const maxTouchPoints = input?.maxTouchPoints ?? nav?.maxTouchPoints ?? 0;
  const width = input?.viewportWidth ?? win?.innerWidth;
  const height = input?.viewportHeight ?? win?.innerHeight;
  const uaDataMobile =
    input?.uaDataMobile ??
    ((nav as Navigator & { userAgentData?: { mobile?: boolean } })?.userAgentData?.mobile);

  const dispositivo_tipo = classifyDeviceType(ua, maxTouchPoints, width, uaDataMobile);
  const dispositivo_so = detectOs(ua, maxTouchPoints);
  const dispositivo_navegador = detectBrowser(ua);

  const meta: DeviceMetadata = {
    dispositivo_tipo,
    dispositivo_so,
    dispositivo_navegador
  };

  if (typeof width === 'number' && typeof height === 'number' && width > 0 && height > 0) {
    meta.dispositivo_viewport = `${Math.round(width)}x${Math.round(height)}`;
  }

  return meta;
}

function classifyDeviceType(
  ua: string,
  maxTouchPoints: number,
  width?: number,
  uaDataMobile?: boolean
): TipoDispositivo {
  const lower = ua.toLowerCase();

  // iPadOS 13+ reporta Macintosh + touch points
  if (lower.includes('ipad') || (lower.includes('macintosh') && maxTouchPoints > 1)) {
    return 'tablet';
  }
  if (lower.includes('tablet') || lower.includes('playbook') || lower.includes('silk')) {
    return 'tablet';
  }
  if (lower.includes('android') && !lower.includes('mobile')) {
    return 'tablet';
  }
  if (
    uaDataMobile === true ||
    /mobi|iphone|ipod|android.*mobile|windows phone|blackberry|opera mini|iemobile/i.test(ua)
  ) {
    return 'movil';
  }
  if (typeof width === 'number' && width > 0 && maxTouchPoints > 0) {
    if (width < 768) return 'movil';
    if (width <= 1024) return 'tablet';
  }
  return 'escritorio';
}

function detectOs(ua: string, maxTouchPoints: number): string {
  const lower = ua.toLowerCase();
  if (lower.includes('android')) return 'Android';
  if (lower.includes('iphone') || lower.includes('ipad') || lower.includes('ipod')) return 'iOS';
  if (lower.includes('macintosh') && maxTouchPoints > 1) return 'iOS';
  if (lower.includes('windows')) return 'Windows';
  if (lower.includes('mac os x') || lower.includes('macintosh')) return 'macOS';
  if (lower.includes('linux') || lower.includes('x11')) return 'Linux';
  return 'Otro';
}

function detectBrowser(ua: string): string {
  if (/edg\//i.test(ua)) return 'Edge';
  if (/opr\/|opera/i.test(ua)) return 'Opera';
  if (/firefox|fxios/i.test(ua)) return 'Firefox';
  if (/chrome|crios/i.test(ua)) return 'Chrome';
  if (/safari/i.test(ua)) return 'Safari';
  return 'Otro';
}
