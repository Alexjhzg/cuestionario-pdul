"""
Empirical Challenger Test Harness for Milestone 4 (challenger_m4_1).

This harness rigorously verifies:
1. Bulk Export Endpoints:
   - CSV export with redact_pii=True and redact_pii=False.
   - JSON export with redact_pii=True and redact_pii=False.
   - Strict PII redaction: nested PII fields (cedula, nombres, email, telefono, direccion)
     eliminated from both CSV and JSON formats.
   - Content-Disposition headers and media types.
   - Validation of formato parameter (regex ^(json|csv)$) and 404 on invalid survey IDs.
2. Survey Active Status Alternation:
   - PATCH /api/v1/admin/encuestas/{id}/estado with { activa: false } and { activa: true }.
   - Public GET /api/v1/encuestas/{slug} returns 404 when inactive, 200 when active.
   - Public submission POST returns 400 ENCUESTA_INACTIVA when inactive, 201 when active.
   - Error handling for invalid IDs and payloads.
3. Pagination of Submissions:
   - GET /api/v1/admin/encuestas/{id}/respuestas across multiple pages.
   - Boundary checks: skip=0, skip=10, skip=20, skip > total.
   - Validation constraints: skip >= 0, 1 <= limit <= 500.
"""

import asyncio
import csv
import io
import json
import uuid
import sys
from typing import Any, Dict, List

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.database import Base, get_db
from backend.app.main import create_app

PII_SECRET_STRINGS = [
    "12345678",
    "Carlos Mendoza",
    "Maria Mendoza",
    "0412-5551234",
    "carlos.mendoza@maturin.gob.ve",
    "Av. Bicentenario cruce con Calle 10",
    "Casa 42",
]


async def run_challenger_harness():
    print("=" * 80)
    print("STARTING EMPIRICAL CHALLENGER VERIFICATION HARNESS FOR MILESTONE 4")
    print("=" * 80)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    app = create_app()

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # ----------------------------------------------------------------------
        # TEST 1: Creation of Test Survey
        # ----------------------------------------------------------------------
        survey_slug = f"test-m4-survey-{uuid.uuid4().hex[:8]}"
        create_payload = {
            "titulo": "Cuestionario PDUL de Verificación M4",
            "slug": survey_slug,
            "tipo_instrumento": "encuesta_od_pdul",
            "esquema_formio": {
                "display": "form",
                "components": [
                    {"type": "textfield", "key": "parroquia", "label": "Parroquia"},
                    {"type": "button", "action": "submit", "key": "submit"},
                ],
            },
            "activa": True,
        }
        res_create = await client.post("/api/v1/admin/encuestas", json=create_payload)
        assert res_create.status_code == 201, f"Failed to create survey: {res_create.text}"
        survey_data = res_create.json()
        survey_id = survey_data["id"]
        print(f"[OK] Survey created: {survey_id} (slug: {survey_slug})")

        # ----------------------------------------------------------------------
        # TEST 2: Active Status Alternation & Cascading Effects
        # ----------------------------------------------------------------------
        print("\n--- STEP 2: EMPIRICAL VERIFICATION OF STATUS ALTERNATION ---")

        # Verify active initially: public slug returns 200
        res_active = await client.get(f"/api/v1/encuestas/{survey_slug}")
        assert res_active.status_code == 200
        assert res_active.json()["activa"] is True

        # Toggle to INACTIVE
        res_toggle_off = await client.patch(
            f"/api/v1/admin/encuestas/{survey_id}/estado", json={"activa": False}
        )
        assert res_toggle_off.status_code == 200
        assert res_toggle_off.json()["activa"] is False
        print("[OK] PATCH /estado to False succeeded.")

        # Verify public slug is now 404
        res_pub_inactive = await client.get(f"/api/v1/encuestas/{survey_slug}")
        assert res_pub_inactive.status_code == 404
        assert res_pub_inactive.json()["code"] == "ENCUESTA_NO_ENCONTRADA"
        print("[OK] Public GET /{slug} returns 404 when survey is inactive.")

        # Verify submitting to inactive survey is rejected with 400 ENCUESTA_INACTIVA
        dummy_sub = {
            "client_submission_id": str(uuid.uuid4()),
            "data": {
                "parroquia": "san_simon",
                "cedula": "11223344",
            },
        }
        res_sub_inactive = await client.post(
            f"/api/v1/encuestas/{survey_id}/respuestas", json=dummy_sub
        )
        assert res_sub_inactive.status_code == 400
        assert res_sub_inactive.json()["code"] == "ENCUESTA_INACTIVA"
        print("[OK] POST /respuestas returns 400 ENCUESTA_INACTIVA when survey is inactive.")

        # Toggle back to ACTIVE
        res_toggle_on = await client.patch(
            f"/api/v1/admin/encuestas/{survey_id}/estado", json={"activa": True}
        )
        assert res_toggle_on.status_code == 200
        assert res_toggle_on.json()["activa"] is True
        print("[OK] PATCH /estado to True succeeded.")

        # Verify public slug is now 200 again
        res_pub_active = await client.get(f"/api/v1/encuestas/{survey_slug}")
        assert res_pub_active.status_code == 200
        assert res_pub_active.json()["activa"] is True
        print("[OK] Public GET /{slug} restored to 200.")

        # Edge cases for status endpoint
        fake_id = str(uuid.uuid4())
        res_fake = await client.patch(
            f"/api/v1/admin/encuestas/{fake_id}/estado", json={"activa": True}
        )
        assert res_fake.status_code == 404
        print("[OK] Non-existent survey ID returns 404 on PATCH /estado.")

        res_malformed = await client.patch(
            f"/api/v1/admin/encuestas/{survey_id}/estado", json={"activa": "not-a-boolean"}
        )
        assert res_malformed.status_code == 422
        print("[OK] Malformed payload returns 422 on PATCH /estado.")

        # ----------------------------------------------------------------------
        # TEST 3: Populate Submissions with Deep PII
        # ----------------------------------------------------------------------
        print("\n--- STEP 3: POPULATING SUBMISSIONS WITH DEEP PII ---")
        num_submissions = 25
        parroquias = ["san_simon", "boqueron", "las_cocuizas", "alto_de_los_godos", "santa_cruz"]

        for i in range(num_submissions):
            cedula_val = f"1000000{i:02d}"
            sub_payload = {
                "client_submission_id": str(uuid.uuid4()),
                "data": {
                    "cedula": f"V-{cedula_val}",
                    "parroquia": parroquias[i % len(parroquias)],
                    "zona_residencia_od": f"ZONA_{i % 5 + 1:02d}",
                    "nombre_apellido": f"Ciudadano {i} Confidencial",
                    "telefono": f"0414-999{i:04d}",
                    "correo": f"ciudadano{i}@correo.maturin.ve",
                    "casa_apartamento": f"Casa {i}",
                    "avenida_calle": f"Calle {i}",
                    "direccion_exacta": f"Dirección Exacta Nro {i}",
                    "residentes": [
                        {
                            "nombre_apellido": f"Familiar {i}",
                            "cedula": f"2000000{i:02d}",
                            "edad": 20 + i,
                            "sexo": "1" if i % 2 == 0 else "2",
                        }
                    ],
                    "viajes": [
                        {
                            "zona_od_origen": "ZONA_01",
                            "zona_od_destino": "ZONA_02",
                            "motivo_viaje": "1",
                            "modo_principal": "6",
                            "tiempo_viaje_min": 25,
                            "costo_viaje_bs": 15.0,
                        }
                    ],
                },
            }
            res_sub = await client.post(
                f"/api/v1/encuestas/{survey_id}/respuestas", json=sub_payload
            )
            assert res_sub.status_code == 201, f"Failed submission {i}: {res_sub.text}"

        print(f"[OK] Successfully seeded {num_submissions} submissions with deep PII.")

        # ----------------------------------------------------------------------
        # TEST 4: Submissions Pagination Empirical Verification
        # ----------------------------------------------------------------------
        print("\n--- STEP 4: EMPIRICAL VERIFICATION OF SUBMISSIONS PAGINATION ---")

        # Page 1: skip=0, limit=10
        res_p1 = await client.get(f"/api/v1/admin/encuestas/{survey_id}/respuestas?skip=0&limit=10")
        assert res_p1.status_code == 200
        p1 = res_p1.json()
        assert p1["total"] == 25
        assert p1["skip"] == 0
        assert p1["limit"] == 10
        assert len(p1["items"]) == 10
        page1_ids = [item["id"] for item in p1["items"]]
        print(f"[OK] Page 1 (skip=0, limit=10): got 10 items, total=25.")

        # Page 2: skip=10, limit=10
        res_p2 = await client.get(f"/api/v1/admin/encuestas/{survey_id}/respuestas?skip=10&limit=10")
        assert res_p2.status_code == 200
        p2 = res_p2.json()
        assert p2["total"] == 25
        assert p2["skip"] == 10
        assert p2["limit"] == 10
        assert len(p2["items"]) == 10
        page2_ids = [item["id"] for item in p2["items"]]
        # Ensure no overlap between page 1 and page 2
        assert set(page1_ids).isdisjoint(set(page2_ids)), "Page 1 and Page 2 contain overlapping items!"
        print(f"[OK] Page 2 (skip=10, limit=10): got 10 items, no overlap with Page 1.")

        # Page 3: skip=20, limit=10 (remaining 5)
        res_p3 = await client.get(f"/api/v1/admin/encuestas/{survey_id}/respuestas?skip=20&limit=10")
        assert res_p3.status_code == 200
        p3 = res_p3.json()
        assert p3["total"] == 25
        assert p3["skip"] == 20
        assert p3["limit"] == 10
        assert len(p3["items"]) == 5
        page3_ids = [item["id"] for item in p3["items"]]
        assert set(page1_ids).isdisjoint(set(page3_ids))
        assert set(page2_ids).isdisjoint(set(page3_ids))
        print(f"[OK] Page 3 (skip=20, limit=10): got exactly 5 items, completing 25.")

        # Page 4: skip=30, limit=10 (beyond total)
        res_p4 = await client.get(f"/api/v1/admin/encuestas/{survey_id}/respuestas?skip=30&limit=10")
        assert res_p4.status_code == 200
        p4 = res_p4.json()
        assert p4["total"] == 25
        assert len(p4["items"]) == 0
        print("[OK] Page beyond total (skip=30, limit=10): returns 0 items gracefully.")

        # Pagination validations
        res_neg_skip = await client.get(f"/api/v1/admin/encuestas/{survey_id}/respuestas?skip=-1&limit=10")
        assert res_neg_skip.status_code == 422
        print("[OK] skip=-1 rejected with 422.")

        res_zero_limit = await client.get(f"/api/v1/admin/encuestas/{survey_id}/respuestas?skip=0&limit=0")
        assert res_zero_limit.status_code == 422
        print("[OK] limit=0 rejected with 422.")

        res_over_limit = await client.get(f"/api/v1/admin/encuestas/{survey_id}/respuestas?skip=0&limit=501")
        assert res_over_limit.status_code == 422
        print("[OK] limit=501 rejected with 422.")

        res_max_limit = await client.get(f"/api/v1/admin/encuestas/{survey_id}/respuestas?skip=0&limit=500")
        assert res_max_limit.status_code == 200
        assert len(res_max_limit.json()["items"]) == 25
        print("[OK] limit=500 accepted with 200.")

        # ----------------------------------------------------------------------
        # TEST 5: Bulk Export Verification & PII Anonymization
        # ----------------------------------------------------------------------
        print("\n--- STEP 5: EMPIRICAL VERIFICATION OF BULK EXPORT & PII REDACTION ---")

        # 5.1 JSON Export with redact_pii=true
        res_json_redacted = await client.get(
            f"/api/v1/admin/encuestas/{survey_id}/exportar?formato=json&redact_pii=true"
        )
        assert res_json_redacted.status_code == 200
        assert "application/json" in res_json_redacted.headers["content-type"]
        assert f'filename="encuesta_{survey_id}.json"' in res_json_redacted.headers["content-disposition"]
        json_redacted_text = res_json_redacted.text
        data_json_redacted = json.loads(json_redacted_text)
        assert len(data_json_redacted) == 25

        # Check that top-level cedula is absent
        for item in data_json_redacted:
            assert "cedula" not in item, f"Leak: top-level 'cedula' found in item: {item}"
            datos = item.get("datos", {})
            for pii_key in [
                "cedula", "nombre_apellido", "telefono", "correo", "email",
                "casa_apartamento", "avenida_calle", "direccion_exacta"
            ]:
                assert pii_key not in datos, f"Leak: PII key '{pii_key}' found in item['datos']!"

            # Check nested residentes
            if "residentes" in datos:
                for res in datos["residentes"]:
                    assert "nombre_apellido" not in res, f"Leak: 'nombre_apellido' in residentes!"
                    assert "cedula" not in res, f"Leak: 'cedula' in residentes!"

        # String search across the entire serialized response
        for i in range(num_submissions):
            cedula_leak = f"1000000{i:02d}"
            name_leak = f"Ciudadano {i} Confidencial"
            phone_leak = f"0414-999{i:04d}"
            fam_leak = f"Familiar {i}"
            assert cedula_leak not in json_redacted_text, f"Leak: '{cedula_leak}' found in redacted JSON!"
            assert name_leak not in json_redacted_text, f"Leak: '{name_leak}' found in redacted JSON!"
            assert phone_leak not in json_redacted_text, f"Leak: '{phone_leak}' found in redacted JSON!"
            assert fam_leak not in json_redacted_text, f"Leak: '{fam_leak}' found in redacted JSON!"

        print("[PASS] JSON export with redact_pii=true is 100% free of PII strings.")

        # 5.2 JSON Export with redact_pii=false (supervisor audit)
        res_json_unredacted = await client.get(
            f"/api/v1/admin/encuestas/{survey_id}/exportar?formato=json&redact_pii=false"
        )
        assert res_json_unredacted.status_code == 200
        data_json_unredacted = json.loads(res_json_unredacted.text)
        assert len(data_json_unredacted) == 25
        # Verify that supervisor audit mode DOES include cédula
        for item in data_json_unredacted:
            assert "cedula" in item, "Expected 'cedula' in unredacted audit JSON export!"
            assert item["datos"].get("nombre_apellido"), "Expected 'nombre_apellido' in unredacted JSON!"

        print("[PASS] JSON export with redact_pii=false preserves audit fields.")

        # 5.3 CSV Export with redact_pii=true
        res_csv_redacted = await client.get(
            f"/api/v1/admin/encuestas/{survey_id}/exportar?formato=csv&redact_pii=true"
        )
        assert res_csv_redacted.status_code == 200
        assert "text/csv" in res_csv_redacted.headers["content-type"]
        assert f'filename="encuesta_{survey_id}.csv"' in res_csv_redacted.headers["content-disposition"]
        csv_redacted_text = res_csv_redacted.text

        csv_reader = csv.reader(io.StringIO(csv_redacted_text))
        rows = list(csv_reader)
        header = rows[0]
        assert header == ["id", "parroquia", "zona_od", "fecha_registro", "datos_json"], f"Unexpected CSV header: {header}"
        assert "cedula" not in header, "Leak: 'cedula' column present in redacted CSV header!"
        assert len(rows) == 26  # header + 25 rows

        for r_idx, row in enumerate(rows[1:], start=1):
            assert len(row) == 5, f"Row {r_idx} length mismatch: {row}"
            # datos_json must be valid JSON without PII
            datos_parsed = json.loads(row[4])
            assert "cedula" not in datos_parsed
            assert "nombre_apellido" not in datos_parsed
            if "residentes" in datos_parsed:
                for res in datos_parsed["residentes"]:
                    assert "nombre_apellido" not in res
                    assert "cedula" not in res

        # String search across the entire CSV text
        for i in range(num_submissions):
            cedula_leak = f"1000000{i:02d}"
            name_leak = f"Ciudadano {i} Confidencial"
            phone_leak = f"0414-999{i:04d}"
            fam_leak = f"Familiar {i}"
            assert cedula_leak not in csv_redacted_text, f"Leak: '{cedula_leak}' found in redacted CSV!"
            assert name_leak not in csv_redacted_text, f"Leak: '{name_leak}' found in redacted CSV!"
            assert phone_leak not in csv_redacted_text, f"Leak: '{phone_leak}' found in redacted CSV!"
            assert fam_leak not in csv_redacted_text, f"Leak: '{fam_leak}' found in redacted CSV!"

        print("[PASS] CSV export with redact_pii=true is 100% free of PII strings and headers.")

        # 5.4 CSV Export with redact_pii=false (supervisor audit)
        res_csv_unredacted = await client.get(
            f"/api/v1/admin/encuestas/{survey_id}/exportar?formato=csv&redact_pii=false"
        )
        assert res_csv_unredacted.status_code == 200
        csv_unredacted_reader = csv.reader(io.StringIO(res_csv_unredacted.text))
        unredacted_rows = list(csv_unredacted_reader)
        unredacted_header = unredacted_rows[0]
        assert unredacted_header == ["id", "parroquia", "zona_od", "fecha_registro", "cedula", "datos_json"]
        assert len(unredacted_rows) == 26
        for row in unredacted_rows[1:]:
            assert len(row) == 6
            assert row[4].startswith("1000000"), f"Expected cedula in row, got: {row[4]}"

        print("[PASS] CSV export with redact_pii=false correctly includes 'cedula' column.")

        # 5.5 Export Error Cases & Boundary Validations
        res_bad_format = await client.get(
            f"/api/v1/admin/encuestas/{survey_id}/exportar?formato=xml"
        )
        assert res_bad_format.status_code == 422
        print("[OK] Invalid formato=xml rejected with 422.")

        res_bad_format_empty = await client.get(
            f"/api/v1/admin/encuestas/{survey_id}/exportar?formato="
        )
        assert res_bad_format_empty.status_code == 422
        print("[OK] Empty formato rejected with 422.")

        res_bad_id = await client.get(
            f"/api/v1/admin/encuestas/{fake_id}/exportar?formato=csv"
        )
        assert res_bad_id.status_code == 404
        print("[OK] Non-existent survey ID returns 404 on export.")

    print("\n" + "=" * 80)
    print("ALL EMPIRICAL CHALLENGES FOR MILESTONE 4 PASSED WITH ZERO ERRORS!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_challenger_harness())
