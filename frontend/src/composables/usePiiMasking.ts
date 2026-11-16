import { PII_FIELD_SET } from '@shared/types/pii';

const MASKED_PLACEHOLDER = '[PROTEGIDO / PII]';

/**
 * Enmascara recursivamente campos de identificación personal (PII) en objetos de respuesta
 * utilizando el catálogo canónico compartido en @shared/types/pii.
 */
export function maskPiiData<T = unknown>(obj: T, maskEnabled = true): T {
  if (!maskEnabled || obj === null || obj === undefined) {
    return obj;
  }
  if (Array.isArray(obj)) {
    return obj.map((item) => maskPiiData(item, maskEnabled)) as T;
  }
  if (typeof obj === 'object') {
    const masked: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj as Record<string, unknown>)) {
      if (PII_FIELD_SET.has(key.toLowerCase())) {
        masked[key] = MASKED_PLACEHOLDER;
      } else {
        masked[key] = maskPiiData(value, maskEnabled);
      }
    }
    return masked as T;
  }
  return obj;
}

export function usePiiMasking() {
  return {
    PII_FIELD_SET,
    MASKED_PLACEHOLDER,
    maskPiiData
  };
}
