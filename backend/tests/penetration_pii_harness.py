"""
Empirical Penetration Test and Aggregation Correctness Harness for Milestone 2.

This harness empirically verifies:
1. PII Leakage Prevention: Injects sensitive PII into survey submissions and asserts
   that sensitive PII strings NEVER appear in serialized responses of all analytics endpoints:
   - /resultados-parroquia
   - /metricas (with valid standard fields)
   - /matriz-od
   - /reparto-modal
   - /kpis
2. Adversarial Penetration: Tests probing /metricas?campo=<pii_field>
   (e.g., campo=cedula, campo=nombre_apellido, campo=telefono, etc.)
   to determine if PII is protected or exposed.
3. Mathematical Correctness of Aggregations:
   - Modal split totals and percentage sums (~100.0%).
   - O-D matrix flow sums and trip counts.
   - Parroquia counts and percentage sums (~100.0%).
   - KPI metrics consistency with ground truth.
4. Export Anonymization Mode:
   - CSV export with redact_pii=True strips all sensitive PII and excludes the 'cedula' column.
   - CSV export with redact_pii=False retains audit data.
"""

import asyncio
import json
import uuid
import sys
from typing import Any, Dict, List

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.database import Base, get_db
from backend.app.main import create_app


SENSITIVE_PII_VALUES = [
    "12345678",
    "Ciudadano Secreto",
    "Calle Secreta Casa 42",
    "0414-9998877",
    "secreto@maturin.gob.ve",
    "Residente Confidencial",
]


async def run_harness():
    print("=" * 70)
    print("STARTING EMPIRICAL PENETRATION & ANALYTICS VERIFICATION HARNESS")
    print("=" * 70)

    # Setup in-memory SQLite database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    app = create_app()

    async def override_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a test survey
        survey_payload = {
            "titulo": "Encuesta PDUL Penetration Test",
            "slug": f"penetration-test-{uuid.uuid4().hex[:8]}",
            "tipo_instrumento": "encuesta_od_pdul",
            "esquema_formio": {
                "display": "wizard",
                "components": [
                    {"type": "textfield", "key": "parroquia", "label": "Parroquia"},
                    {"type": "button", "action": "submit", "key": "submit", "label": "Enviar"},
                ],
            },
            "activa": True,
        }
        res_create = await client.post("/api/v1/admin/encuestas", json=survey_payload)
        assert res_create.status_code == 201, f"Failed to create survey: {res_create.text}"
        encuesta_id = res_create.json()["id"]
        print(f"[OK] Test survey created with ID: {encuesta_id}")

        # 2. Populate submissions containing sensitive PII and diverse trip chains
        # Submission 1: Contains full sensitive PII
        sub1 = {
            "client_submission_id": str(uuid.uuid4()),
            "data": {
                "cedula": "12345678",
                "nombre_apellido": "Ciudadano Secreto",
                "casa_apartamento": "Calle Secreta Casa 42",
                "telefono": "0414-9998877",
                "correo": "secreto@maturin.gob.ve",
                "parroquia": "san_simon",
                "zona_residencia_od": "ZONA_01",
                "tipo_vivienda": "quinta",
                "num_residentes_hogar": 3,
                "residentes": [
                    {"nombre_apellido": "Ciudadano Secreto", "edad": 40, "sexo": "1"},
                    {"nombre_apellido": "Residente Confidencial", "edad": 38, "sexo": "2"},
                ],
                "viajes": [
                    {
                        "zona_od_origen": "ZONA_01",
                        "zona_od_destino": "ZONA_02",
                        "motivo_viaje": "1",
                        "modo_principal": "4",  # Automóvil particular
                        "tiempo_viaje_min": 20,
                        "costo_viaje_bs": 10.0,
                    },
                    {
                        "zona_od_origen": "ZONA_02",
                        "zona_od_destino": "ZONA_01",
                        "motivo_viaje": "5",
                        "modo_principal": "4",
                        "tiempo_viaje_min": 25,
                        "costo_viaje_bs": 10.0,
                    },
                ],
            },
        }

        # Submission 2: Different citizen, different parroquia, different modes
        sub2 = {
            "client_submission_id": str(uuid.uuid4()),
            "data": {
                "cedula": "87654321",
                "nombre_apellido": "Otro Ciudadano",
                "parroquia": "alto_de_los_godos",
                "zona_residencia_od": "ZONA_03",
                "tipo_vivienda": "apartamento",
                "num_residentes_hogar": 2,
                "residentes": [
                    {"nombre_apellido": "Familiar Uno", "edad": 22, "sexo": "1"},
                ],
                "viajes": [
                    {
                        "zona_od_origen": "ZONA_03",
                        "zona_od_destino": "ZONA_01",
                        "motivo_viaje": "2",
                        "modo_principal": "6",  # Transporte público
                        "tiempo_viaje_min": 35,
                        "costo_viaje_bs": 15.0,
                    },
                    {
                        "zona_od_origen": "ZONA_01",
                        "zona_od_destino": "ZONA_03",
                        "motivo_viaje": "5",
                        "modo_principal": "1",  # A pie
                        "tiempo_viaje_min": 50,
                        "costo_viaje_bs": 0.0,
                    },
                ],
            },
        }

        # Submission 3: Third citizen, las_cocuizas, mode 6
        sub3 = {
            "client_submission_id": str(uuid.uuid4()),
            "data": {
                "cedula": "23456789",
                "nombre_apellido": "Tercer Informante",
                "parroquia": "las_cocuizas",
                "zona_residencia_od": "ZONA_02",
                "tipo_vivienda": "quinta",
                "num_residentes_hogar": 1,
                "viajes": [
                    {
                        "zona_od_origen": "ZONA_02",
                        "zona_od_destino": "ZONA_01",
                        "motivo_viaje": "1",
                        "modo_principal": "6",  # Transporte público
                        "tiempo_viaje_min": 30,
                        "costo_viaje_bs": 15.0,
                    }
                ],
            },
        }

        for i, sub in enumerate([sub1, sub2, sub3], 1):
            r = await client.post(f"/api/v1/encuestas/{encuesta_id}/respuestas", json=sub)
            assert r.status_code == 201, f"Failed submission {i}: {r.text}"
            print(f"[OK] Submission {i} registered successfully.")

        # Total expected:
        # Submissions: 3
        # Trips: 2 + 2 + 1 = 5
        # Modal split:
        #   modo 4: 2 trips (40.0%)
        #   modo 6: 2 trips (40.0%)
        #   modo 1: 1 trip (20.0%)
        # Parroquias:
        #   san_simon: 1 (33.33%)
        #   alto_de_los_godos: 1 (33.33%)
        #   las_cocuizas: 1 (33.33%)
        # OD pairs:
        #   ZONA_01 -> ZONA_02: 1
        #   ZONA_02 -> ZONA_01: 2
        #   ZONA_03 -> ZONA_01: 1
        #   ZONA_01 -> ZONA_03: 1

        print("\n--- PHASE 1: Query Standard Analytics Endpoints & String Search for PII ---")
        endpoints_to_test = [
            f"/api/v1/encuestas/{encuesta_id}/resultados-parroquia",
            f"/api/v1/encuestas/{encuesta_id}/metricas?campo=tipo_vivienda",
            f"/api/v1/encuestas/{encuesta_id}/matriz-od",
            f"/api/v1/encuestas/{encuesta_id}/reparto-modal",
            f"/api/v1/encuestas/{encuesta_id}/kpis",
        ]

        found_leakages = []
        for ep in endpoints_to_test:
            resp = await client.get(ep)
            assert resp.status_code == 200, f"Endpoint {ep} returned {resp.status_code}: {resp.text}"
            body_text = resp.text
            print(f"Checking {ep} (status {resp.status_code}, length {len(body_text)} chars)...")

            for pii in SENSITIVE_PII_VALUES:
                if pii in body_text:
                    err = f"CRITICAL PII LEAKAGE in {ep}: Found sensitive string '{pii}' in response body!"
                    print(f"  [FAIL] {err}")
                    found_leakages.append((ep, pii))
                else:
                    # OK
                    pass

        if not found_leakages:
            print("[PASS] No sensitive PII strings detected across all standard analytics endpoints.")
        else:
            print(f"[FAIL] {len(found_leakages)} PII leakages detected in standard analytics endpoints!")

        print("\n--- PHASE 2: Adversarial Penetration on /metricas with PII fields ---")
        adversarial_fields = [
            "cedula",
            "nombre_apellido",
            "nombres_apellidos",
            "telefono",
            "correo",
            "email",
            "casa_apartamento",
            "direccion_exacta",
        ]
        adversarial_leaks = []
        for field in adversarial_fields:
            ep = f"/api/v1/encuestas/{encuesta_id}/metricas?campo={field}"
            resp = await client.get(ep)
            print(f"Probing {ep} -> Status: {resp.status_code}")
            assert resp.status_code == 400, f"Expected 400 for PII field {field}, got {resp.status_code}"
            err_json = resp.json()
            assert err_json.get("code") == "CAMPO_PII_RESTRINGIDO", f"Expected CAMPO_PII_RESTRINGIDO for {field}, got {err_json}"
            if resp.status_code == 200:
                body_text = resp.text
                for pii in SENSITIVE_PII_VALUES:
                    if pii in body_text:
                        err = f"CRITICAL PROBE EXPOSURE on {ep}: PII string '{pii}' leaked in labels!"
                        print(f"  [VULNERABILITY] {err}")
                        adversarial_leaks.append((field, pii, resp.json()))

        print("\n--- PHASE 3: Mathematical Verification of Analytics Aggregations ---")
        # 1. Reparto Modal
        res_modal = await client.get(f"/api/v1/encuestas/{encuesta_id}/reparto-modal")
        modal_data = res_modal.json()
        print("Modal split response:", json.dumps(modal_data, indent=2))
        total_modal_trips = sum(item["total_viajes"] for item in modal_data)
        total_modal_pct = sum(item["porcentaje"] for item in modal_data)
        print(f"Modal split total trips: {total_modal_trips} (expected 5)")
        print(f"Modal split total percentage: {total_modal_pct:.2f}% (expected ~100.0%)")
        assert total_modal_trips == 5, f"Expected 5 total trips in modal split, got {total_modal_trips}"
        assert abs(total_modal_pct - 100.0) < 0.2, f"Modal percentage sum deviates: {total_modal_pct}%"

        # 2. Matriz O-D
        res_od = await client.get(f"/api/v1/encuestas/{encuesta_id}/matriz-od")
        od_data = res_od.json()
        print("OD Matrix response:", json.dumps(od_data, indent=2))
        total_od_trips = sum(row["total_viajes"] for row in od_data)
        print(f"OD Matrix total trips: {total_od_trips} (expected 5)")
        assert total_od_trips == 5, f"Expected 5 trips in OD matrix, got {total_od_trips}"

        # Check ZONA_02 -> ZONA_01 (should have 2 trips)
        z02_z01 = next((r for r in od_data if r["zona_origen"] == "ZONA_02" and r["zona_destino"] == "ZONA_01"), None)
        assert z02_z01 is not None, "Missing flow ZONA_02 -> ZONA_01"
        assert z02_z01["total_viajes"] == 2, f"Expected 2 trips ZONA_02 -> ZONA_01, got {z02_z01['total_viajes']}"
        # Avg time: (25 + 30) / 2 = 27.5
        assert z02_z01["tiempo_promedio_min"] == 27.5, f"Wrong avg time: {z02_z01['tiempo_promedio_min']}"
        # Avg cost: (10 + 15) / 2 = 12.5
        assert z02_z01["costo_promedio_bs"] == 12.5, f"Wrong avg cost: {z02_z01['costo_promedio_bs']}"

        # 3. Resultados Parroquia
        res_parr = await client.get(f"/api/v1/encuestas/{encuesta_id}/resultados-parroquia")
        parr_data = res_parr.json()
        print("Parroquia results:", json.dumps(parr_data, indent=2))
        total_parr_subs = sum(p["total_respuestas"] for p in parr_data)
        total_parr_pct = sum(p["porcentaje"] for p in parr_data)
        print(f"Parroquia total submissions: {total_parr_subs} (expected 3)")
        print(f"Parroquia total percentage sum: {total_parr_pct:.2f}% (expected ~100.0%)")
        assert total_parr_subs == 3, f"Expected 3 submissions in parroquia stats, got {total_parr_subs}"
        assert abs(total_parr_pct - 100.0) < 0.2, f"Parroquia percentage sum deviates: {total_parr_pct}%"

        # 4. KPIs
        res_kpis = await client.get(f"/api/v1/encuestas/{encuesta_id}/kpis")
        kpis = res_kpis.json()
        print("KPIs response:", json.dumps(kpis, indent=2))
        assert kpis["total_encuestas"] == 3
        assert kpis["total_viajes"] == 5
        # Total residentes:
        # sub1: 2 in residentes list
        # sub2: 1 in residentes list
        # sub3: 0 in list, num_residentes_hogar = 1
        # Let's check how KPI calculated it
        print(f"KPI total_residentes: {kpis['total_residentes']}")

        print("\n--- PHASE 4: CSV / JSON Export Anonymization Mode ---")
        # 1. Export CSV with redact_pii=True
        res_csv_redacted = await client.get(f"/api/v1/admin/encuestas/{encuesta_id}/exportar?formato=csv&redact_pii=true")
        assert res_csv_redacted.status_code == 200
        csv_redacted_text = res_csv_redacted.text
        print("CSV Redacted Header & Sample Lines:")
        for line in csv_redacted_text.splitlines()[:5]:
            print("  ", line)

        csv_redacted_leaks = []
        for pii in SENSITIVE_PII_VALUES:
            if pii in csv_redacted_text:
                csv_redacted_leaks.append(pii)

        if not csv_redacted_leaks:
            print("[PASS] CSV export with redact_pii=True contains NO sensitive PII.")
        else:
            print(f"[FAIL] CSV export with redact_pii=True LEAKED: {csv_redacted_leaks}")

        # Assert 'cedula' column is NOT in the header when redact_pii=True
        header_line = csv_redacted_text.splitlines()[0]
        assert "cedula" not in header_line.split(","), "Header should NOT contain 'cedula' column when redacted"

        # 2. Export CSV with redact_pii=False (unredacted supervisor export)
        res_csv_raw = await client.get(f"/api/v1/admin/encuestas/{encuesta_id}/exportar?formato=csv&redact_pii=false")
        assert res_csv_raw.status_code == 200
        csv_raw_text = res_csv_raw.text
        header_raw = csv_raw_text.splitlines()[0]
        assert "cedula" in header_raw.split(","), "Header SHOULD contain 'cedula' when redact_pii=False"
        assert "12345678" in csv_raw_text, "Unredacted export should contain the supervisor data"
        print("[PASS] Unredacted CSV export functions correctly for supervisor audit.")

        # 3. Export JSON with redact_pii=True
        res_json_redacted = await client.get(f"/api/v1/admin/encuestas/{encuesta_id}/exportar?formato=json&redact_pii=true")
        assert res_json_redacted.status_code == 200
        json_redacted_text = res_json_redacted.text
        json_redacted_leaks = [p for p in SENSITIVE_PII_VALUES if p in json_redacted_text]
        if not json_redacted_leaks:
            print("[PASS] JSON export with redact_pii=True contains NO sensitive PII.")
        else:
            print(f"[FAIL] JSON export with redact_pii=True LEAKED: {json_redacted_leaks}")

        print("\n" + "=" * 70)
        print("EMPIRICAL HARNESS SUMMARY RESULTS:")
        print(f"- Standard Analytics Endpoints Leakages: {len(found_leakages)}")
        print(f"- Adversarial /metricas?campo=<pii> Leakages: {len(adversarial_leaks)}")
        print(f"- Aggregation Mathematics: MODAL={total_modal_pct:.2f}%, OD={total_od_trips} trips, PARROQUIA={total_parr_pct:.2f}%")
        print(f"- Redacted CSV Leaks: {len(csv_redacted_leaks)}")
        print(f"- Redacted JSON Leaks: {len(json_redacted_leaks)}")
        print("=" * 70)

        return {
            "standard_leakages": found_leakages,
            "adversarial_leakages": adversarial_leaks,
            "csv_redacted_leaks": csv_redacted_leaks,
            "json_redacted_leaks": json_redacted_leaks,
        }

if __name__ == "__main__":
    results = asyncio.run(run_harness())
    if results["standard_leakages"] or results["csv_redacted_leaks"] or results["json_redacted_leaks"]:
        print("\nFATAL: PII Leakage verified in standard endpoints or redacted export!")
        sys.exit(1)
    if results["adversarial_leakages"]:
        print("\nNOTE: Adversarial probe leakage observed on /metricas with PII fields.")
    sys.exit(0)
