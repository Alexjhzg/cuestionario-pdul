import { describe, it, expect } from 'vitest';
import {
  normalizeCedula,
  isValidCedula,
  isValidParroquia,
  isValidTravelTime,
  isValidTravelCost,
  PARROQUIAS_MATURIN,
  PARROQUIA_NOMBRES,
  formatParroquia
} from '@/utils/validation';

describe('Módulo de Validaciones Ciudadanas PDUL Maturín (validation.ts)', () => {
  describe('normalizeCedula', () => {
    it('elimina puntos, guiones y letras de prefijo venezolanas (V, E)', () => {
      expect(normalizeCedula('V-12.345.678')).toBe('12345678');
      expect(normalizeCedula('V12345678')).toBe('12345678');
      expect(normalizeCedula('E-20.987.654')).toBe('20987654');
      expect(normalizeCedula('J-30.123.456')).toBe('30123456');
    });

    it('elimina espacios en blanco internos y externos', () => {
      expect(normalizeCedula('  14 555 666  ')).toBe('14555666');
    });

    it('maneja valores nulos, indefinidos y vacíos de forma segura', () => {
      expect(normalizeCedula('')).toBe('');
      expect(normalizeCedula(null)).toBe('');
      expect(normalizeCedula(undefined)).toBe('');
    });

    it('maneja entradas numéricas directas', () => {
      expect(normalizeCedula(18500200)).toBe('18500200');
    });
  });

  describe('isValidCedula', () => {
    it('valida cédulas válidas con longitud entre 6 y 9 dígitos', () => {
      expect(isValidCedula('123456')).toBe(true);       // 6 dígitos
      expect(isValidCedula('1234567')).toBe(true);      // 7 dígitos
      expect(isValidCedula('12345678')).toBe(true);     // 8 dígitos
      expect(isValidCedula('123456789')).toBe(true);    // 9 dígitos
      expect(isValidCedula('V-18.234.567')).toBe(true); // Con formato
    });

    it('rechaza cédulas con longitud menor a 6 dígitos o mayor a 9 dígitos', () => {
      expect(isValidCedula('12345')).toBe(false);       // 5 dígitos (muy corta)
      expect(isValidCedula('1234567890')).toBe(false);  // 10 dígitos (muy larga)
    });

    it('rechaza entradas no numéricas o vacías', () => {
      expect(isValidCedula('abcdef')).toBe(false);
      expect(isValidCedula('')).toBe(false);
      expect(isValidCedula(null)).toBe(false);
      expect(isValidCedula(undefined)).toBe(false);
    });
  });

  describe('isValidParroquia (11 Parroquias de Maturín)', () => {
    it('valida positivamente las 11 parroquias oficiales de Maturín', () => {
      expect(PARROQUIAS_MATURIN).toHaveLength(11);
      const expectedParroquias = [
        'alto_de_los_godos',
        'boqueron',
        'las_cocuizas',
        'la_cruz',
        'san_simon',
        'santa_cruz',
        'el_corozo',
        'el_furrial',
        'jusepin',
        'la_pica',
        'san_vicente'
      ];

      expectedParroquias.forEach((parroquia) => {
        expect(isValidParroquia(parroquia)).toBe(true);
      });
    });

    it('acepta mayúsculas o espacios accidentales normalizando a snake_case', () => {
      expect(isValidParroquia(' San_Simon ')).toBe(true);
      expect(isValidParroquia('BOQUERON')).toBe(true);
    });

    it('rechaza parroquias ajenas a Maturín o valores inválidos', () => {
      expect(isValidParroquia('chacao')).toBe(false);
      expect(isValidParroquia('caracas')).toBe(false);
      expect(isValidParroquia('maturin_centro_inexistente')).toBe(false);
      expect(isValidParroquia('')).toBe(false);
      expect(isValidParroquia(null)).toBe(false);
      expect(isValidParroquia(undefined)).toBe(false);
    });
  });

  describe('isValidTravelTime', () => {
    it('acepta tiempos de viaje estrictamente mayores a cero', () => {
      expect(isValidTravelTime(5)).toBe(true);
      expect(isValidTravelTime(30)).toBe(true);
      expect(isValidTravelTime(120)).toBe(true);
      expect(isValidTravelTime('45')).toBe(true);
    });

    it('rechaza tiempos de viaje cero, negativos o no numéricos', () => {
      expect(isValidTravelTime(0)).toBe(false);
      expect(isValidTravelTime(-15)).toBe(false);
      expect(isValidTravelTime('cero')).toBe(false);
      expect(isValidTravelTime('')).toBe(false);
      expect(isValidTravelTime(null)).toBe(false);
    });
  });

  describe('isValidTravelCost', () => {
    it('acepta costos de viaje mayores o iguales a cero', () => {
      expect(isValidTravelCost(0)).toBe(true); // Viaje a pie o gratis
      expect(isValidTravelCost(15.5)).toBe(true);
      expect(isValidTravelCost('30')).toBe(true);
    });

    it('rechaza costos negativos o valores inválidos', () => {
      expect(isValidTravelCost(-5)).toBe(false);
      expect(isValidTravelCost('gratis')).toBe(false);
      expect(isValidTravelCost('')).toBe(false);
      expect(isValidTravelCost(null)).toBe(false);
    });
  });

  describe('formatParroquia (Formateo limpio sin guiones bajos para UI)', () => {
    it('contiene las 11 entradas en el diccionario centralizado PARROQUIA_NOMBRES', () => {
      expect(Object.keys(PARROQUIA_NOMBRES)).toHaveLength(11);
      expect(PARROQUIA_NOMBRES.san_simon).toBe('San Simón');
      expect(PARROQUIA_NOMBRES.las_cocuizas).toBe('Las Cocuizas');
    });

    it('formatea las 11 parroquias de Maturín con sus nombres oficiales acentuados', () => {
      expect(formatParroquia('alto_de_los_godos')).toBe('Alto de Los Godos');
      expect(formatParroquia('boqueron')).toBe('Boquerón');
      expect(formatParroquia('las_cocuizas')).toBe('Las Cocuizas');
      expect(formatParroquia('la_cruz')).toBe('La Cruz');
      expect(formatParroquia('san_simon')).toBe('San Simón');
      expect(formatParroquia('santa_cruz')).toBe('Santa Cruz');
      expect(formatParroquia('el_corozo')).toBe('El Corozo');
      expect(formatParroquia('el_furrial')).toBe('El Furrial');
      expect(formatParroquia('jusepin')).toBe('Jusepín');
      expect(formatParroquia('la_pica')).toBe('La Pica');
      expect(formatParroquia('san_vicente')).toBe('San Vicente');
    });

    it('maneja mayúsculas o espacios accidentales', () => {
      expect(formatParroquia(' SAN_SIMON ')).toBe('San Simón');
      expect(formatParroquia('Las_Cocuizas')).toBe('Las Cocuizas');
    });

    it('retorna cadena vacía para null o undefined', () => {
      expect(formatParroquia(null)).toBe('');
      expect(formatParroquia(undefined)).toBe('');
      expect(formatParroquia('')).toBe('');
    });

    it('aplica fallback limpio si la clave no está en el catálogo', () => {
      expect(formatParroquia('otra_zona_urbana')).toBe('Otra Zona Urbana');
    });
  });
});
