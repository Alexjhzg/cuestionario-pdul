import parroquiasCatalog from '@shared/catalogs/parroquias.json';
import type { ParroquiaCatalogItem } from '@shared/types';

/**
 * Utilidades de validación ciudadana y del PDUL Maturín
 */

const CATALOG_ITEMS = parroquiasCatalog as ParroquiaCatalogItem[];

export const PARROQUIAS_MATURIN = CATALOG_ITEMS.map((item) => item.codigo);

export type ParroquiaMaturin = string;

/**
 * Catálogo centralizado de nombres de parroquias formateados para visualización UI (sin guiones bajos).
 * Se deriva del catálogo canónico compartido en @shared/catalogs/parroquias.json.
 */
export const PARROQUIA_NOMBRES: Record<string, string> = Object.fromEntries(
  CATALOG_ITEMS.map((item) => [
    item.codigo,
    item.codigo === 'alto_de_los_godos' ? 'Alto de Los Godos' : item.label
  ])
);

export const PARROQUIA_CANONICAL_LABELS: Record<string, string> = Object.fromEntries(
  CATALOG_ITEMS.map((item) => [item.codigo, item.label])
);

/**
 * Formatea el identificador snake_case de una parroquia a su nombre oficial limpio para la UI.
 * Si no coincide con el catálogo, reemplaza guiones bajos y aplica mayúsculas iniciales.
 */
export function formatParroquia(key?: string | null): string {
  if (!key) return '';
  const cleanKey = String(key).trim().toLowerCase();
  if (PARROQUIA_NOMBRES[cleanKey]) {
    return PARROQUIA_NOMBRES[cleanKey];
  }
  return cleanKey.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

/**
 * Convierte el texto escrito por el ciudadano al código interno de parroquia si coincide
 * con una parroquia oficial (ignora mayúsculas, acentos y espacios); si no coincide,
 * devuelve el texto tal cual para respetar la respuesta abierta.
 */
export function parroquiaToKey(text?: string | null): string {
  if (!text) return '';
  const raw = String(text);
  const key = raw
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[\s-]+/g, '_');
  return PARROQUIAS_MATURIN.includes(key) ? key : raw;
}

/**
 * Texto a mostrar en el campo de parroquia: nombre formal si es una parroquia oficial,
 * o el texto libre escrito por el ciudadano.
 */
export function parroquiaDisplayText(value?: string | null): string {
  if (!value) return '';
  const v = String(value);
  return PARROQUIA_NOMBRES[v] ?? v;
}

/**
 * Normaliza la cédula venezolana:
 * Elimina letras (V, E, J), puntos, guiones y espacios en blanco,
 * dejando únicamente la secuencia numérica.
 */
export function normalizeCedula(input: string | number | null | undefined): string {
  if (input === null || input === undefined) return '';
  const str = String(input).trim();
  return str.replace(/[^0-9]/g, '');
}

/**
 * Valida si la cédula venezolana tiene un formato válido (entre 6 y 9 dígitos numéricos).
 */
export function isValidCedula(input: string | number | null | undefined): boolean {
  const normalized = normalizeCedula(input);
  return /^[0-9]{6,9}$/.test(normalized);
}

/**
 * Valida si el código de parroquia pertenece a las 11 parroquias oficiales del Municipio Maturín.
 */
export function isValidParroquia(parroquia: string | null | undefined): boolean {
  if (!parroquia) return false;
  return PARROQUIAS_MATURIN.includes(parroquia.trim().toLowerCase());
}

/**
 * Valida que el tiempo de viaje sea un número estrictamente mayor a 0 minutos.
 */
export function isValidTravelTime(minutos: number | string | null | undefined): boolean {
  if (minutos === null || minutos === undefined || minutos === '') return false;
  const num = typeof minutos === 'number' ? minutos : Number(minutos);
  return !isNaN(num) && isFinite(num) && num > 0;
}

/**
 * Valida que el costo de viaje sea un número no negativo (>= 0).
 */
export function isValidTravelCost(costo: number | string | null | undefined): boolean {
  if (costo === null || costo === undefined || costo === '') return false;
  const num = typeof costo === 'number' ? costo : Number(costo);
  return !isNaN(num) && isFinite(num) && num >= 0;
}
