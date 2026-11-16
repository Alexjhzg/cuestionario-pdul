import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  exportarRespuestasAdmin,
  updateEncuestaEstado,
  toggleAdminEncuestaEstado,
  fetchAdminRespuestas,
  fetchAdminEncuestas,
  createAdminEncuesta,
  updateAdminEncuesta,
  triggerBlobDownload,
  descargarBlob,
  ApiError
} from '@/services/api';

describe('Empirical Challenger M4-1: API REST Layer & Export Connectivity (api.ts)', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  // =========================================================================
  // 1. exportarRespuestasAdmin Empirical Tests
  // =========================================================================
  describe('1. exportarRespuestasAdmin', () => {
    it('1.1 Solicitud CSV con redact_pii=true: construye URL correcta, header text/csv y retorna Blob', async () => {
      const mockCsvContent = 'id,parroquia,zona_od,fecha_registro,datos_json\n1,san_simon,Z-01,2026-11-10,{}\n';
      const mockBlob = new Blob([mockCsvContent], { type: 'text/csv' });

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        blob: vi.fn().mockResolvedValue(mockBlob)
      });

      const surveyId = '11111111-2222-3333-4444-555555555555';
      const result = await exportarRespuestasAdmin(surveyId, 'csv', true);

      expect(global.fetch).toHaveBeenCalledTimes(1);
      const [url, options] = vi.mocked(global.fetch).mock.calls[0];
      expect(url).toBe(`/api/v1/admin/encuestas/${surveyId}/exportar?formato=csv&redact_pii=true`);
      expect(options?.headers).toEqual({ Accept: 'text/csv' });
      expect(result).toBeInstanceOf(Blob);
    });

    it('1.2 Solicitud JSON con redact_pii=false: construye URL correcta, header application/json y retorna Blob', async () => {
      const mockJsonContent = JSON.stringify([{ id: 1, cedula: '12345678', datos: {} }]);
      const mockBlob = new Blob([mockJsonContent], { type: 'application/json' });

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        blob: vi.fn().mockResolvedValue(mockBlob)
      });

      const surveyId = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee';
      const result = await exportarRespuestasAdmin(surveyId, 'json', false);

      expect(global.fetch).toHaveBeenCalledTimes(1);
      const [url, options] = vi.mocked(global.fetch).mock.calls[0];
      expect(url).toBe(`/api/v1/admin/encuestas/${surveyId}/exportar?formato=json&redact_pii=false`);
      expect(options?.headers).toEqual({ Accept: 'application/json' });
      expect(result).toBeInstanceOf(Blob);
    });

    it('1.3 Manejo de Error 404 / 422: lanza ApiError con ProblemDetail enriquecido', async () => {
      const problemDetail = {
        code: 'ENCUESTA_NO_ENCONTRADA',
        title: 'No encontrada',
        status: 404,
        detail: 'Encuesta no encontrada en el sistema.'
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: vi.fn().mockResolvedValue(problemDetail)
      });

      const surveyId = '00000000-0000-0000-0000-000000000000';
      await expect(exportarRespuestasAdmin(surveyId, 'csv', true)).rejects.toThrow(ApiError);

      try {
        await exportarRespuestasAdmin(surveyId, 'csv', true);
      } catch (err: any) {
        expect(err).toBeInstanceOf(ApiError);
        expect(err.status).toBe(404);
        expect(err.message).toBe('Encuesta no encontrada en el sistema.');
        expect(err.problem).toEqual(problemDetail);
      }
    });
  });

  // =========================================================================
  // 2. updateEncuestaEstado / toggleAdminEncuestaEstado
  // =========================================================================
  describe('2. updateEncuestaEstado & toggleAdminEncuestaEstado', () => {
    it('2.1 Envía PATCH con body JSON { activa: false } y valida respuesta', async () => {
      const surveyId = '22222222-3333-4444-5555-666666666666';
      const mockResponseData = {
        id: surveyId,
        titulo: 'Encuesta Test',
        slug: 'encuesta-test',
        tipo_instrumento: 'consulta_ciudadana',
        activa: false,
        creado_en: '2026-11-10T12:00:00Z',
        esquema_formio: {}
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue(mockResponseData)
      });

      const result = await updateEncuestaEstado(surveyId, false);

      expect(global.fetch).toHaveBeenCalledTimes(1);
      const [url, options] = vi.mocked(global.fetch).mock.calls[0];
      expect(url).toBe(`/api/v1/admin/encuestas/${surveyId}/estado`);
      expect(options?.method).toBe('PATCH');
      expect(options?.headers).toEqual({
        'Content-Type': 'application/json',
        Accept: 'application/json'
      });
      expect(JSON.parse(options?.body as string)).toEqual({ activa: false });
      expect(result.activa).toBe(false);
    });

    it('2.2 toggleAdminEncuestaEstado es alias estricto de updateEncuestaEstado', async () => {
      expect(toggleAdminEncuestaEstado).toBe(updateEncuestaEstado);
    });

    it('2.3 Manejo de error al cambiar estado: lanza ApiError con detalle', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: vi.fn().mockRejectedValue(new Error('Invalid JSON'))
      });

      await expect(updateEncuestaEstado('fake-id', true)).rejects.toThrow(ApiError);
    });
  });

  // =========================================================================
  // 3. fetchAdminRespuestas Pagination
  // =========================================================================
  describe('3. fetchAdminRespuestas', () => {
    it('3.1 Consulta paginada con skip y limit por defecto (0, 50)', async () => {
      const surveyId = '33333333-4444-5555-6666-777777777777';
      const mockData = {
        total: 100,
        skip: 0,
        limit: 50,
        items: []
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue(mockData)
      });

      const result = await fetchAdminRespuestas(surveyId);

      const [url] = vi.mocked(global.fetch).mock.calls[0];
      expect(url).toBe(`/api/v1/admin/encuestas/${surveyId}/respuestas?skip=0&limit=50`);
      expect(result.total).toBe(100);
    });

    it('3.2 Consulta paginada con skip y limit personalizados (skip=20, limit=10)', async () => {
      const surveyId = '33333333-4444-5555-6666-777777777777';
      const mockData = {
        total: 25,
        skip: 20,
        limit: 10,
        items: [{ id: 21 }, { id: 22 }, { id: 23 }, { id: 24 }, { id: 25 }]
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue(mockData)
      });

      const result = await fetchAdminRespuestas(surveyId, 20, 10);

      const [url] = vi.mocked(global.fetch).mock.calls[0];
      expect(url).toBe(`/api/v1/admin/encuestas/${surveyId}/respuestas?skip=20&limit=10`);
      expect(result.items.length).toBe(5);
    });
  });

  // =========================================================================
  // 4. triggerBlobDownload & descargarBlob
  // =========================================================================
  describe('4. triggerBlobDownload & descargarBlob', () => {
    it('4.1 Dispara descarga creando elemento anchor en DOM, simulando click y limpiando URL', () => {
      const mockBlob = new Blob(['datos csv de prueba'], { type: 'text/csv' });
      const mockUrl = 'blob:http://localhost/test-uuid';

      const createObjectURLSpy = vi.spyOn(window.URL, 'createObjectURL').mockReturnValue(mockUrl);
      const revokeObjectURLSpy = vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {});

      const appendSpy = vi.spyOn(document.body, 'appendChild');
      const removeSpy = vi.spyOn(document.body, 'removeChild');

      vi.useFakeTimers();

      triggerBlobDownload(mockBlob, 'test_descarga.csv');

      expect(createObjectURLSpy).toHaveBeenCalledWith(mockBlob);
      expect(appendSpy).toHaveBeenCalled();

      const createdAnchor = appendSpy.mock.calls[0][0] as HTMLAnchorElement;
      expect(createdAnchor.tagName.toLowerCase()).toBe('a');
      expect(createdAnchor.download).toBe('test_descarga.csv');
      expect(createdAnchor.href).toBe(mockUrl);

      // Avanzar temporizador para limpieza
      vi.advanceTimersByTime(150);

      expect(removeSpy).toHaveBeenCalledWith(createdAnchor);
      expect(revokeObjectURLSpy).toHaveBeenCalledWith(mockUrl);

      vi.useRealTimers();
    });

    it('4.2 descargarBlob es alias idéntico de triggerBlobDownload', () => {
      expect(descargarBlob).toBe(triggerBlobDownload);
    });
  });

  // =========================================================================
  // 5. Gestión General de Encuestas (fetchAdminEncuestas, create, update)
  // =========================================================================
  describe('5. Gestión General de Encuestas (fetchAdminEncuestas, create, update)', () => {
    it('5.1 fetchAdminEncuestas consulta GET /admin/encuestas', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue([{ id: '1', titulo: 'E1' }])
      });

      const list = await fetchAdminEncuestas();
      expect(list.length).toBe(1);
      const [url] = vi.mocked(global.fetch).mock.calls[0];
      expect(url).toBe('/api/v1/admin/encuestas');
    });

    it('5.2 createAdminEncuesta envía POST /admin/encuestas con payload estructurado', async () => {
      const payload = {
        titulo: 'Nueva Encuesta',
        slug: 'nueva-encuesta',
        tipo_instrumento: 'consulta_ciudadana',
        activa: true,
        esquema_formio: { display: 'form', components: [] }
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 201,
        json: vi.fn().mockResolvedValue({ id: '999', ...payload })
      });

      const created = await createAdminEncuesta(payload);
      expect(created.id).toBe('999');
      const [url, options] = vi.mocked(global.fetch).mock.calls[0];
      expect(url).toBe('/api/v1/admin/encuestas');
      expect(options?.method).toBe('POST');
      expect(JSON.parse(options?.body as string)).toEqual(payload);
    });

    it('5.3 updateAdminEncuesta envía PUT /admin/encuestas/{id} con payload parcial', async () => {
      const surveyId = '77777777-8888-9999-aaaa-bbbbbbbbbbbb';
      const payload = {
        titulo: 'Título Actualizado',
        activa: false
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue({ id: surveyId, ...payload })
      });

      const updated = await updateAdminEncuesta(surveyId, payload);
      expect(updated.titulo).toBe('Título Actualizado');
      const [url, options] = vi.mocked(global.fetch).mock.calls[0];
      expect(url).toBe(`/api/v1/admin/encuestas/${surveyId}`);
      expect(options?.method).toBe('PUT');
    });
  });
});
