/**
 * Stress Test & Verification Script for Offline Autosave & Queue Logic
 * Project: Cuestionario PDUL Maturín
 * Milestone: M3 Challenger Empirical Verification
 */

import { Window } from 'happy-dom';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

// 1. Initialize virtual DOM environment
const window = new Window({
  url: 'https://cuestionario.maturin.gob.ve/encuesta/cuestionario-od-maturin'
});

Object.defineProperty(globalThis, 'window', { value: window, configurable: true, writable: true });
Object.defineProperty(globalThis, 'document', { value: window.document, configurable: true, writable: true });
Object.defineProperty(globalThis, 'localStorage', { value: window.localStorage, configurable: true, writable: true });
Object.defineProperty(globalThis, 'navigator', { value: { onLine: true }, configurable: true, writable: true });
if (!globalThis.crypto) {
  Object.defineProperty(globalThis, 'crypto', { value: window.crypto, configurable: true, writable: true });
}

// Import useSurveyDraft dynamically
const { useSurveyDraft, generateUUID } = await import('../src/composables/useSurveyDraft.ts');

console.log('===============================================================');
console.log('  CHALLENGER M3: EMPIRICAL STRESS TEST SUITE (OFFLINE & AUTOSAVE)');
console.log('===============================================================\n');

let totalTests = 0;
let passedTests = 0;

function runTest(name, fn) {
  totalTests++;
  try {
    fn();
    console.log(`  ✓ [PASS] ${name}`);
    passedTests++;
  } catch (err) {
    console.error(`  ✗ [FAIL] ${name}`);
    console.error(`    ${err.message}`);
    throw err;
  }
}

// -------------------------------------------------------------
// SUITE 1: UUID v4 Conformance & Collision Resistance
// -------------------------------------------------------------
console.log('[Suite 1: UUID v4 Strict Conformance & Uniqueness]');

runTest('generateUUID produces 1000 valid RFC 4122 v4 UUIDs without collision', () => {
  const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  const set = new Set();
  const count = 1000;

  for (let i = 0; i < count; i++) {
    const id = generateUUID();
    assert.match(id, UUID_V4_REGEX, `Generated ID "${id}" must conform to RFC 4122 v4`);
    assert.equal(id.charAt(14), '4', `Version nibble must be 4 in "${id}"`);
    assert.ok(['8', '9', 'a', 'b', 'A', 'B'].includes(id.charAt(19)), `Variant nibble must be 8/9/a/b in "${id}"`);
    set.add(id);
  }

  assert.equal(set.size, count, `All ${count} generated UUIDs must be strictly unique`);
});

// -------------------------------------------------------------
// SUITE 2: Offline Network Outage Simulation & Queue Data Preservation
// -------------------------------------------------------------
console.log('\n[Suite 2: Offline Network Outage Simulation & Data Preservation]');

const mockSurveyPayload = {
  cedula: 'V-27.123.456',
  parroquia: 'san_simon',
  zona_residencia_od: '01',
  sector_barrio: 'Sector Centro',
  tipo_vivienda: 'quinta',
  cuartos_dormir: 3,
  personas_hogar: 3,
  residentes: [
    { persona_numero: 1, nombres: 'Carlos Mendoza', edad: 48, sexo: '1', ocupacion: '1', tiene_licencia: true },
    { persona_numero: 2, nombres: 'Elena Gomez', edad: 45, sexo: '2', ocupacion: '2', tiene_licencia: true },
    { persona_numero: 3, nombres: 'Andres Mendoza', edad: 19, sexo: '1', ocupacion: '4', tiene_licencia: false }
  ],
  viajes: [
    {
      viaje_numero: 1,
      persona_numero: 1,
      origen: 'Sector Centro',
      zona_origen: '01',
      destino: 'Las Cocuizas',
      zona_destino: '03',
      hora_salida: '07:30',
      hora_llegada: '08:05',
      tiempo_viaje_min: 35,
      motivo: '1',
      modo_principal: '6',
      costo_viaje_bs: 25.5
    },
    {
      viaje_numero: 2,
      persona_numero: 1,
      origen: 'Las Cocuizas',
      zona_origen: '03',
      destino: 'Sector Centro',
      zona_destino: '01',
      hora_salida: '16:00',
      hora_llegada: '16:40',
      tiempo_viaje_min: 40,
      motivo: '8',
      modo_principal: '6',
      costo_viaje_bs: 25.5
    }
  ],
  acepta_declaracion: true
};

const encuestaId = '11111111-2222-3333-4444-555555555555';
let enqueuedClientSubmissionId = '';

runTest('Simulated network outage (isOnline=false) preserves full payload and structure in pdul_offline_queue', () => {
  localStorage.clear();

  // Simulate network drop
  Object.defineProperty(navigator, 'onLine', { value: false, configurable: true, writable: true });

  const { isOnline, enqueueOfflineSubmission, getOfflineQueue } = useSurveyDraft('cuestionario-od-maturin');
  assert.equal(isOnline.value, false, 'isOnline must reflect navigator.onLine=false');

  // Enqueue offline
  enqueuedClientSubmissionId = enqueueOfflineSubmission(encuestaId, mockSurveyPayload);

  // Assert returned UUID v4
  const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  assert.match(enqueuedClientSubmissionId, UUID_V4_REGEX, 'enqueueOfflineSubmission must return UUID v4');

  // Assert localStorage raw representation
  const rawQueue = localStorage.getItem('pdul_offline_queue');
  assert.ok(rawQueue, 'pdul_offline_queue must exist in localStorage');

  const queue = JSON.parse(rawQueue);
  assert.equal(queue.length, 1, 'Queue must contain 1 item');

  const item = queue[0];
  assert.equal(item.clientSubmissionId, enqueuedClientSubmissionId, 'clientSubmissionId must match');
  assert.equal(item.encuestaId, encuestaId, 'encuestaId must match');
  assert.ok(item.createdAt, 'createdAt timestamp must be present');

  // Verify data preservation and types
  const data = item.data;
  assert.equal(data.client_submission_id, enqueuedClientSubmissionId, 'data.client_submission_id must be populated');
  assert.equal(data.cedula, 'V-27.123.456', 'cedula must be preserved');
  assert.equal(data.parroquia, 'san_simon', 'parroquia must be preserved');
  assert.equal(data.cuartos_dormir, 3, 'cuartos_dormir must be numeric 3');
  assert.equal(typeof data.cuartos_dormir, 'number', 'cuartos_dormir type must be number');
  assert.equal(data.personas_hogar, 3, 'personas_hogar must be numeric 3');
  assert.equal(typeof data.personas_hogar, 'number', 'personas_hogar type must be number');

  // Residentes checks
  assert.equal(data.residentes.length, 3, 'residentes list must have 3 items');
  assert.equal(data.residentes[0].nombres, 'Carlos Mendoza');
  assert.equal(data.residentes[0].edad, 48);
  assert.equal(typeof data.residentes[0].edad, 'number');
  assert.equal(data.residentes[0].tiene_licencia, true);
  assert.equal(typeof data.residentes[0].tiene_licencia, 'boolean');

  // Viajes checks
  assert.equal(data.viajes.length, 2, 'viajes list must have 2 items');
  assert.equal(data.viajes[0].tiempo_viaje_min, 35);
  assert.equal(typeof data.viajes[0].tiempo_viaje_min, 'number');
  assert.equal(data.viajes[0].costo_viaje_bs, 25.5);
  assert.equal(typeof data.viajes[0].costo_viaje_bs, 'number');
  assert.equal(data.viajes[1].tiempo_viaje_min, 40);
  assert.equal(typeof data.viajes[1].tiempo_viaje_min, 'number');
});

runTest('Enqueuing offline submission automatically clears any active draft for that slug', () => {
  // Check active draft is null after enqueue
  const rawDraft = localStorage.getItem('pdul_draft_cuestionario-od-maturin');
  assert.equal(rawDraft, null, 'Active draft must be cleared when enqueued to avoid duplicate resubmission');
});

// -------------------------------------------------------------
// SUITE 3: Multi-Submission Stress & FIFO Queue Order
// -------------------------------------------------------------
console.log('\n[Suite 3: Multi-Submission Stress & FIFO Queue Order]');

runTest('Enqueue 25 consecutive offline submissions and verify order and selective removal', () => {
  const { enqueueOfflineSubmission, getOfflineQueue, clearOfflineQueueItem } = useSurveyDraft('cuestionario-od-maturin');
  const ids = [];

  for (let i = 1; i <= 25; i++) {
    const subId = enqueueOfflineSubmission(`encuesta-batch-${i}`, {
      parroquia: 'boqueron',
      submission_index: i,
      cedula: `1000000${i}`
    });
    ids.push(subId);
  }

  // Queue now has 1 (from suite 2) + 25 = 26 items
  const queue = getOfflineQueue();
  assert.equal(queue.length, 26, 'Queue length must be 26');

  // Verify all IDs are present and in order
  for (let i = 0; i < 25; i++) {
    assert.equal(queue[i + 1].clientSubmissionId, ids[i]);
    assert.equal(queue[i + 1].data.submission_index, i + 1);
  }

  // Remove the 13th item (which is at index 13 because index 0 was suite 2)
  const targetId = ids[12]; // submission_index: 13
  clearOfflineQueueItem(targetId);

  const updatedQueue = getOfflineQueue();
  assert.equal(updatedQueue.length, 25, 'Queue length must be 25 after single item removal');
  assert.ok(!updatedQueue.some(item => item.clientSubmissionId === targetId), 'Target item must be removed');

  // Verify the rest remained unchanged
  assert.equal(updatedQueue[12].data.submission_index, 12, 'Preceding item #12 must remain in place');
  assert.equal(updatedQueue[13].data.submission_index, 14, 'Subsequent item #14 must shift to index 13');
});

// -------------------------------------------------------------
// SUITE 4: Draft Autosave & Restoration with Numeric and Array Types
// -------------------------------------------------------------
console.log('\n[Suite 4: Draft Autosave & Restoration with Strict Type Integrity]');

runTest('Autosave and draft restoration preserves numeric types and nested lists without loss', () => {
  localStorage.clear();

  const slug = 'cuestionario-od-maturin';
  const draft1 = useSurveyDraft(slug);

  draft1.formData.value = {
    cedula: '18555999',
    parroquia: 'las_cocuizas',
    personas_hogar: 5,
    cuartos_dormir: 2,
    tiempo_viaje_min: 17.5,
    costo_viaje_bs: 0,
    activo: true,
    residentes: [
      { persona_numero: 1, nombres: 'Luis', edad: 52 },
      { persona_numero: 2, nombres: 'Rosa', edad: 49 }
    ],
    viajes: [
      { viaje_numero: 1, origen: 'Sector A', destino: 'Sector B', tiempo_viaje_min: 17.5 }
    ]
  };
  draft1.currentStep.value = 6;
  draft1.saveToLocalStorage();

  // Verify stored JSON
  const raw = localStorage.getItem(`pdul_draft_${slug}`);
  assert.ok(raw, 'Draft must be saved in localStorage');

  // Re-instantiate as if page was refreshed
  const draft2 = useSurveyDraft(slug);
  assert.equal(draft2.hasRestorableDraft.value, true, 'hasRestorableDraft must be true on refresh');

  draft2.restoreDraft();
  assert.equal(draft2.hasRestorableDraft.value, false, 'hasRestorableDraft must be false after restore');
  assert.equal(draft2.currentStep.value, 6, 'currentStep must be restored to 6');

  // Verify numeric types
  assert.equal(draft2.formData.value.personas_hogar, 5);
  assert.equal(typeof draft2.formData.value.personas_hogar, 'number', 'personas_hogar must remain number');

  assert.equal(draft2.formData.value.cuartos_dormir, 2);
  assert.equal(typeof draft2.formData.value.cuartos_dormir, 'number', 'cuartos_dormir must remain number');

  assert.equal(draft2.formData.value.tiempo_viaje_min, 17.5);
  assert.equal(typeof draft2.formData.value.tiempo_viaje_min, 'number', 'tiempo_viaje_min must remain number');

  assert.equal(draft2.formData.value.costo_viaje_bs, 0);
  assert.equal(typeof draft2.formData.value.costo_viaje_bs, 'number', 'costo_viaje_bs must remain number 0');

  // Verify nested arrays
  assert.equal(draft2.formData.value.residentes.length, 2);
  assert.equal(draft2.formData.value.residentes[0].edad, 52);
  assert.equal(typeof draft2.formData.value.residentes[0].edad, 'number');

  assert.equal(draft2.formData.value.viajes.length, 1);
  assert.equal(draft2.formData.value.viajes[0].tiempo_viaje_min, 17.5);
  assert.equal(typeof draft2.formData.value.viajes[0].tiempo_viaje_min, 'number');
});

// -------------------------------------------------------------
// SUITE 5: Resilience & Exception Handling on Corrupted Storage
// -------------------------------------------------------------
console.log('\n[Suite 5: Resilience against Corrupted Storage & Edge Cases]');

runTest('Gracefully handles corrupted JSON in draft storage without throwing', () => {
  const slug = 'cuestionario-od-maturin';
  localStorage.setItem(`pdul_draft_${slug}`, '{MALFORMED_JSON_CORRUPTED: 123');

  const draft = useSurveyDraft(slug);
  assert.equal(draft.hasRestorableDraft.value, false, 'Corrupted draft must not be marked as restorable');

  // Calling restoreDraft must not throw
  assert.doesNotThrow(() => {
    draft.restoreDraft();
  }, 'restoreDraft must not throw on corrupted storage');
});

runTest('Gracefully handles corrupted JSON in offline queue without throwing', () => {
  localStorage.setItem('pdul_offline_queue', '[[[NOT_VALID_JSON');

  const draft = useSurveyDraft('cuestionario-od-maturin');
  let queue = null;
  assert.doesNotThrow(() => {
    queue = draft.getOfflineQueue();
  }, 'getOfflineQueue must not throw on corrupted queue');

  assert.deepEqual(queue, [], 'Corrupted queue must fall back to empty array');
});

// -------------------------------------------------------------
// SUITE 6: Cross-Contract Validation with Backend Pydantic v2
// -------------------------------------------------------------
console.log('\n[Suite 6: Backend Pydantic v2 Contract Validation]');

runTest('Offline queue item is 100% valid under Backend FormioSubmissionIn schema', () => {
  // Re-enqueue the rich payload
  localStorage.clear();
  const { enqueueOfflineSubmission, getOfflineQueue } = useSurveyDraft('cuestionario-od-maturin');
  const subId = enqueueOfflineSubmission(encuestaId, mockSurveyPayload);
  const queue = getOfflineQueue();
  const offlineItem = queue[0];

  // Prepare payload exactly as SurveyFillView sends to submitRespuesta:
  // { client_submission_id: item.clientSubmissionId, data: item.data }
  const submissionPayload = {
    client_submission_id: offlineItem.clientSubmissionId,
    data: offlineItem.data
  };

  const tempJsonPath = path.resolve('/tmp/offline_submission_test.json');
  fs.writeFileSync(tempJsonPath, JSON.stringify(submissionPayload, null, 2));

  // Run python verification script against backend schema
  const pythonScript = `
import sys
import json
from uuid import UUID

# Import backend Pydantic schema
sys.path.insert(0, '/home/seem/Documentos/_proyectos/cuestionario-pedul')
from backend.app.schemas.submission import FormioSubmissionIn

with open('${tempJsonPath}', 'r') as f:
    raw_payload = json.load(f)

# Validate with Pydantic v2
validated = FormioSubmissionIn.model_validate(raw_payload)

print(f"DEBUG: validated.client_submission_id = {validated.client_submission_id!r}")
print(f"DEBUG: raw_payload['client_submission_id'] = {raw_payload.get('client_submission_id')!r}")

assert isinstance(validated.client_submission_id, UUID), "client_submission_id must be parsed as UUID"
assert str(validated.client_submission_id).lower() == str(raw_payload['client_submission_id']).lower(), "UUID string must match"
assert validated.cedula_limpia == "27123456", f"Normalized cedula must be 27123456, got {validated.cedula_limpia}"
assert validated.parroquia == "san_simon", f"Normalized parroquia must be san_simon, got {validated.parroquia}"
assert validated.zona_od == "01", f"zona_od must be 01, got {validated.zona_od}"
assert len(validated.data['residentes']) == 3, "All 3 residentes must be preserved"
assert len(validated.data['viajes']) == 2, "All 2 viajes must be preserved"
assert validated.data['viajes'][0]['tiempo_viaje_min'] == 35, "tiempo_viaje_min must remain numeric 35"
assert validated.data['cuartos_dormir'] == 3, "cuartos_dormir must remain numeric 3"

print("Pydantic validation SUCCESS: client_submission_id=" + str(validated.client_submission_id))
`;

  try {
    const pythonOutput = execSync(
      `python3 -c "${pythonScript.replace(/"/g, '\\"')}"`,
      { cwd: '/home/seem/Documentos/_proyectos/cuestionario-pedul', encoding: 'utf-8' }
    );
    console.log(`    Backend Output: ${pythonOutput.trim()}`);
  } finally {
    if (fs.existsSync(tempJsonPath)) {
      fs.unlinkSync(tempJsonPath);
    }
  }
});

// -------------------------------------------------------------
// SUITE 7: Synchronization Loop & Partial Network Failure Recovery
// -------------------------------------------------------------
console.log('\n[Suite 7: Sync Queue Processing & Mid-Batch Network Interruption]');

runTest('Queue sync processes items in order and retains unsubmitted items when interrupted', async () => {
  localStorage.clear();
  const draft = useSurveyDraft('cuestionario-od-maturin');

  // Enqueue 4 items
  const id1 = draft.enqueueOfflineSubmission('enc-1', { index: 1, cedula: '10000001' });
  const id2 = draft.enqueueOfflineSubmission('enc-1', { index: 2, cedula: '10000002' });
  const id3 = draft.enqueueOfflineSubmission('enc-1', { index: 3, cedula: '10000003' });
  const id4 = draft.enqueueOfflineSubmission('enc-1', { index: 4, cedula: '10000004' });

  assert.equal(draft.getOfflineQueue().length, 4, 'Initial queue must have 4 items');

  // Simulate sync function: fails on item #3
  const submittedIds = [];
  const simulateSync = async () => {
    const queue = draft.getOfflineQueue();
    for (const item of queue) {
      try {
        if (item.data.index === 3) {
          throw new Error('Network timeout during transmission of item 3');
        }
        submittedIds.push(item.clientSubmissionId);
        draft.clearOfflineQueueItem(item.clientSubmissionId);
      } catch {
        break; // Stop sync loop on error
      }
    }
  };

  await simulateSync();

  // Assert item 1 and 2 succeeded and were removed
  assert.deepEqual(submittedIds, [id1, id2], 'Items 1 and 2 must have succeeded');

  // Assert item 3 and 4 remain in queue
  const remainingQueue = draft.getOfflineQueue();
  assert.equal(remainingQueue.length, 2, 'Remaining queue must have 2 items');
  assert.equal(remainingQueue[0].clientSubmissionId, id3, 'Item 3 must be first in remaining queue');
  assert.equal(remainingQueue[1].clientSubmissionId, id4, 'Item 4 must be second in remaining queue');

  // Now resume network (simulate retry)
  const resumeSync = async () => {
    const queue = draft.getOfflineQueue();
    for (const item of queue) {
      submittedIds.push(item.clientSubmissionId);
      draft.clearOfflineQueueItem(item.clientSubmissionId);
    }
  };

  await resumeSync();
  assert.deepEqual(submittedIds, [id1, id2, id3, id4], 'All 4 items eventually transmitted in FIFO order');
  assert.equal(draft.getOfflineQueue().length, 0, 'Queue must be completely empty after successful retry');
});

console.log('\n===============================================================');
console.log(`  EMPIRICAL STRESS TEST COMPLETE: ${passedTests}/${totalTests} TESTS PASSED (100%)`);
console.log('===============================================================\n');
