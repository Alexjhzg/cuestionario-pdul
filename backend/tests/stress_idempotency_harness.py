"""
Empirical Stress & Challenge Harness for Milestone 2:
Idempotency, Replay Handling, Duplicate Cédula Conflict (HTTP 409),
Inactive Survey Rejection (HTTP 400), and Malformed Payload Handling (HTTP 422).

This script runs autonomously and asserts every empirical requirement using httpx.AsyncClient.
"""

import asyncio
import sys
import uuid
from typing import Any, Dict, List
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.core.database import Base, get_db
from backend.app.main import create_app
from backend.app.models.encuesta import Encuesta
from backend.app.models.respuesta import RespuestaCiudadana


SAMPLE_FORMIO_SCHEMA: Dict[str, Any] = {
    "display": "wizard",
    "components": [
        {
            "type": "panel",
            "key": "seccion_i",
            "title": "I. Ubicación",
            "components": [
                {
                    "type": "select",
                    "key": "parroquia",
                    "label": "Parroquia",
                    "data": {
                        "values": [
                            {"label": "San Simón", "value": "san_simon"},
                            {"label": "Alto de Los Godos", "value": "alto_de_los_godos"},
                        ]
                    },
                },
                {"type": "textfield", "key": "zona_residencia_od", "label": "Zona OD"},
            ],
        },
        {
            "type": "panel",
            "key": "seccion_cierre",
            "title": "Cierre",
            "components": [
                {
                    "type": "button",
                    "action": "submit",
                    "key": "submit",
                    "label": "Finalizar Encuesta",
                }
            ],
        },
    ],
}


class EmpiricalChallengeRunner:
    def __init__(self) -> None:
        self.results: List[Dict[str, Any]] = []
        self.failures: List[str] = []

    def record(self, scenario: str, passed: bool, detail: str) -> None:
        self.results.append({"scenario": scenario, "passed": passed, "detail": detail})
        status_str = "PASS" if passed else "FAIL"
        print(f"[{status_str}] {scenario}: {detail}")
        if not passed:
            self.failures.append(f"{scenario}: {detail}")

    async def run_all(self) -> bool:
        print("=" * 80)
        print("EMPIRICAL CHALLENGER M2: Commencing Idempotency, Concurrency & RFC 7807 Fuzzing")
        print("=" * 80)

        # Set up isolated in-memory SQLite database
        test_engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            future=True,
        )
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        app = create_app()

        async def override_get_db():
            async with session_factory() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://challenge-test") as client:
            # Setup active survey
            active_survey_id = await self._create_survey(client, "survey-active", activa=True)
            # Setup inactive survey
            inactive_survey_id = await self._create_survey(client, "survey-inactive", activa=False)

            # CHALLENGE SUITE 1: Sequential Idempotency & Replay Handling
            await self.challenge_sequential_idempotency(client, session_factory, active_survey_id)

            # CHALLENGE SUITE 2: Concurrent Replay Stress
            await self.challenge_concurrent_idempotency(client, session_factory, active_survey_id)

            # CHALLENGE SUITE 3: Duplicate Cédula Conflict (HTTP 409 & RFC 7807)
            await self.challenge_duplicate_cedula(client, session_factory, active_survey_id)

            # CHALLENGE SUITE 4: Inactive Survey Rejection (HTTP 400 & RFC 7807)
            await self.challenge_inactive_survey(client, session_factory, inactive_survey_id)

            # CHALLENGE SUITE 5: Malformed & Adversarial Payloads (HTTP 422 & RFC 7807)
            await self.challenge_malformed_payloads(client, active_survey_id)

            # CHALLENGE SUITE 6: Cédula-less Submissions (Census/Household edge case)
            await self.challenge_cedula_less_submissions(client, session_factory, active_survey_id)

        await test_engine.dispose()

        print("=" * 80)
        total = len(self.results)
        passed_count = sum(1 for r in self.results if r["passed"])
        failed_count = len(self.failures)
        print(f"SUMMARY: Total Scenarios: {total} | Passed: {passed_count} | Failed: {failed_count}")
        if self.failures:
            print("\nFAILURES ENCOUNTERED:")
            for f in self.failures:
                print(f"  - {f}")
            print("=" * 80)
            return False
        else:
            print("ALL EMPIRICAL CHALLENGES PASSED.")
            print("=" * 80)
            return True

    async def _create_survey(self, client: AsyncClient, slug_prefix: str, activa: bool) -> str:
        slug = f"{slug_prefix}-{uuid.uuid4().hex[:8]}"
        payload = {
            "titulo": f"Encuesta {slug}",
            "slug": slug,
            "tipo_instrumento": "encuesta_od_pdul",
            "esquema_formio": SAMPLE_FORMIO_SCHEMA,
            "activa": activa,
        }
        res = await client.post("/api/v1/admin/encuestas", json=payload)
        assert res.status_code == 201, f"Failed to create test survey: {res.text}"
        return res.json()["id"]

    async def challenge_sequential_idempotency(
        self, client: AsyncClient, session_factory: async_sessionmaker, survey_id: str
    ) -> None:
        """Verify sequential replay of the same client_submission_id."""
        client_sub_id = str(uuid.uuid4())
        payload = {
            "client_submission_id": client_sub_id,
            "data": {
                "cedula": "V-15.987.654",
                "parroquia": "san_simon",
                "zona_residencia_od": "ZONA_01",
                "tipo_vivienda": "casa",
            },
        }

        # 1. First submission -> Expect 201 Created
        res1 = await client.post(f"/api/v1/encuestas/{survey_id}/respuestas", json=payload)
        p1 = res1.status_code == 201 and res1.json().get("idempotent_replay") is False
        body1 = res1.json()
        sub_id = body1.get("id")
        self.record(
            "Idempotency - Initial Submission",
            p1,
            f"Status={res1.status_code}, idempotent_replay={body1.get('idempotent_replay')}, id={sub_id}",
        )

        # 2. Replay 5 times sequentially -> Expect 200 OK each time, identical ID, idempotent_replay: true
        replay_ok = True
        for i in range(5):
            res_rep = await client.post(f"/api/v1/encuestas/{survey_id}/respuestas", json=payload)
            body_rep = res_rep.json()
            if (
                res_rep.status_code != 200
                or body_rep.get("id") != sub_id
                or body_rep.get("idempotent_replay") is not True
            ):
                replay_ok = False
                break

        self.record(
            "Idempotency - Sequential 5x Replay",
            replay_ok,
            f"All 5 sequential replays returned HTTP 200 with matching ID {sub_id} and idempotent_replay=True",
        )

        # 3. Direct DB row check: verify exactly 1 row exists with this client_submission_id
        async with session_factory() as session:
            count_stmt = select(func.count(RespuestaCiudadana.id)).where(
                RespuestaCiudadana.client_submission_id == uuid.UUID(client_sub_id)
            )
            count_res = await session.execute(count_stmt)
            row_count = count_res.scalar()

        self.record(
            "Idempotency - Zero Duplicate DB Rows",
            row_count == 1,
            f"Exact row count in DB for client_submission_id is {row_count} (expected 1)",
        )

    async def challenge_concurrent_idempotency(
        self, client: AsyncClient, session_factory: async_sessionmaker, survey_id: str
    ) -> None:
        """Send 8 concurrent identical requests with the same client_submission_id."""
        client_sub_id = str(uuid.uuid4())
        payload = {
            "client_submission_id": client_sub_id,
            "data": {
                "cedula": "V-18.765.432",
                "parroquia": "alto_de_los_godos",
                "zona_residencia_od": "ZONA_02",
                "tipo_vivienda": "apartamento",
            },
        }

        tasks = [
            client.post(f"/api/v1/encuestas/{survey_id}/respuestas", json=payload)
            for _ in range(8)
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        statuses = [r.status_code if hasattr(r, "status_code") else type(r).__name__ for r in responses]
        
        # Verify no 500 errors occurred
        has_500 = any(s == 500 for s in statuses)
        self.record(
            "Concurrency - No Internal Server Errors (500)",
            not has_500,
            f"Response statuses from 8 concurrent requests: {statuses}",
        )

        # Verify all concurrent requests resolved with 200 or 201 (idempotent replay, zero 409 misclassifications)
        all_success = all(s in (200, 201) for s in statuses)
        self.record(
            "Concurrency - Idempotent Resolution (200 or 201 only)",
            all_success,
            f"All concurrent requests resolved cleanly without 409 conflict: {statuses}",
        )

        # Verify DB row count: MUST be exactly 1 row
        async with session_factory() as session:
            count_stmt = select(func.count(RespuestaCiudadana.id)).where(
                RespuestaCiudadana.client_submission_id == uuid.UUID(client_sub_id)
            )
            count_res = await session.execute(count_stmt)
            row_count = count_res.scalar()

        self.record(
            "Concurrency - Database Integrity (Single Row)",
            row_count == 1,
            f"Rows persisted in DB under concurrent flood: {row_count} (expected exactly 1)",
        )

    async def challenge_duplicate_cedula(
        self, client: AsyncClient, session_factory: async_sessionmaker, survey_id: str
    ) -> None:
        """Challenge duplicate cédula conflict (HTTP 409) with RFC 7807 compliance."""
        cedula_raw = "V-22.333.444"
        clean_cedula = "22333444"

        # 1. Register first participation
        sub_id_1 = str(uuid.uuid4())
        payload1 = {
            "client_submission_id": sub_id_1,
            "data": {
                "cedula": cedula_raw,
                "parroquia": "las_cocuizas",
            },
        }
        res1 = await client.post(f"/api/v1/encuestas/{survey_id}/respuestas", json=payload1)
        self.record(
            "Duplicate Cédula - Initial Participation",
            res1.status_code == 201,
            f"First submission registered with code {res1.status_code}",
        )

        # 2. Attempt second participation with DIFFERENT client_submission_id and varied format of same cédula
        formats_to_test = [
            clean_cedula,
            f"v-{clean_cedula}",
            f"  {clean_cedula}  ",
            f"E-{clean_cedula}",
        ]

        all_409_ok = True
        rfc7807_ok = True

        for fmt in formats_to_test:
            sub_id_diff = str(uuid.uuid4())
            dup_payload = {
                "client_submission_id": sub_id_diff,
                "data": {
                    "cedula": fmt,
                    "parroquia": "boqueron",
                },
            }
            res_dup = await client.post(f"/api/v1/encuestas/{survey_id}/respuestas", json=dup_payload)
            if res_dup.status_code != 409:
                all_409_ok = False
                break
            
            body = res_dup.json()
            # Verify RFC 7807 fields
            if (
                body.get("code") != "CEDULA_DUPLICADA"
                or body.get("status") != 409
                or body.get("field") != "cedula"
                or not body.get("detail")
            ):
                rfc7807_ok = False
                break

        self.record(
            "Duplicate Cédula - HTTP 409 Conflict across format variations",
            all_409_ok,
            f"All duplicate cédula variations returned HTTP 409",
        )
        self.record(
            "Duplicate Cédula - RFC 7807 Problem Detail Structure",
            rfc7807_ok,
            f"Payload contains code='CEDULA_DUPLICADA', status=409, field='cedula', detail",
        )

        # 3. Check DB has only 1 row for this cédula in this survey
        async with session_factory() as session:
            count_stmt = select(func.count(RespuestaCiudadana.id)).where(
                RespuestaCiudadana.encuesta_id == uuid.UUID(survey_id),
                RespuestaCiudadana.cedula == clean_cedula,
            )
            count_res = await session.execute(count_stmt)
            cedula_rows = count_res.scalar()

        self.record(
            "Duplicate Cédula - Zero Duplicate Cédula Rows in DB",
            cedula_rows == 1,
            f"Total rows for cédula {clean_cedula} in survey: {cedula_rows} (expected 1)",
        )

    async def challenge_inactive_survey(
        self, client: AsyncClient, session_factory: async_sessionmaker, inactive_survey_id: str
    ) -> None:
        """Challenge submission to inactive survey -> HTTP 400 Bad Request with RFC 7807."""
        payload = {
            "client_submission_id": str(uuid.uuid4()),
            "data": {
                "cedula": "V-29.876.543",
                "parroquia": "san_simon",
            },
        }

        res = await client.post(f"/api/v1/encuestas/{inactive_survey_id}/respuestas", json=payload)
        p_code = res.status_code == 400
        body = res.json()
        rfc_ok = (
            body.get("code") == "ENCUESTA_INACTIVA"
            and body.get("status") == 400
            and "inactiva" in body.get("detail", "").lower()
        )

        self.record(
            "Inactive Survey - HTTP 400 Bad Request",
            p_code,
            f"Status={res.status_code} (expected 400)",
        )
        self.record(
            "Inactive Survey - RFC 7807 Problem Detail",
            rfc_ok,
            f"code={body.get('code')}, status={body.get('status')}, detail={body.get('detail')}",
        )

    async def challenge_malformed_payloads(self, client: AsyncClient, survey_id: str) -> None:
        """Challenge malformed and adversarial payloads -> HTTP 422 with RFC 7807 structured errors."""
        test_cases = [
            (
                "Empty Parish String",
                {"data": {"cedula": "12345678", "parroquia": ""}},
                "parroquia",
            ),
            (
                "Whitespace-Only Parish",
                {"data": {"cedula": "12345678", "parroquia": "   "}},
                "parroquia",
            ),
            (
                "Missing Parish",
                {"data": {"cedula": "12345678"}},
                "parroquia",
            ),
            (
                "Cédula Too Short (< 6 digits)",
                {"data": {"cedula": "12345", "parroquia": "san_simon"}},
                "cédula",
            ),
            (
                "Cédula Too Long (> 9 digits)",
                {"data": {"cedula": "1234567890", "parroquia": "san_simon"}},
                "cédula",
            ),
            (
                "Cédula Non-numeric Characters Only",
                {"data": {"cedula": "ABCDEFGH", "parroquia": "san_simon"}},
                "cédula",
            ),
            (
                "Negative Travel Time in Viajes Grid",
                {
                    "data": {
                        "cedula": "12345678",
                        "parroquia": "san_simon",
                        "viajes": [
                            {
                                "zona_od_origen": "ZONA_01",
                                "zona_od_destino": "ZONA_02",
                                "tiempo_viaje_min": -15,
                            }
                        ],
                    }
                },
                "tiempo de viaje",
            ),
            (
                "Zero Travel Time in Viajes Grid",
                {
                    "data": {
                        "cedula": "12345678",
                        "parroquia": "san_simon",
                        "viajes": [
                            {
                                "zona_od_origen": "ZONA_01",
                                "zona_od_destino": "ZONA_02",
                                "tiempo_viaje_min": 0,
                            }
                        ],
                    }
                },
                "tiempo de viaje",
            ),
            (
                "Malformed Client Submission ID (Non-UUID)",
                {"client_submission_id": "not-a-valid-uuid", "data": {"parroquia": "san_simon"}},
                "uuid",
            ),
        ]

        for desc, payload, expected_error_keyword in test_cases:
            res = await client.post(f"/api/v1/encuestas/{survey_id}/respuestas", json=payload)
            body = res.json()
            is_422 = res.status_code == 422
            errors_list = body.get("errors") or []
            rfc_valid = (
                body.get("code") == "VALIDATION_ERROR"
                and body.get("status") == 422
                and isinstance(errors_list, list)
                and len(errors_list) > 0
            )
            # Verify that either the top-level detail or one of the errors mentions the expected keyword
            all_messages = " ".join([e.get("msg", "") for e in errors_list]).lower()
            keyword_match = expected_error_keyword.lower() in all_messages or expected_error_keyword.lower() in str(body.get("detail", "")).lower()

            self.record(
                f"Malformed Payload - {desc}",
                is_422 and rfc_valid and keyword_match,
                f"HTTP {res.status_code}, code={body.get('code')}, field={body.get('field')}, errors_count={len(errors_list)}, matched='{expected_error_keyword}'",
            )

    async def challenge_cedula_less_submissions(
        self, client: AsyncClient, session_factory: async_sessionmaker, survey_id: str
    ) -> None:
        """Challenge anonymous/cédula-less household submissions (allowed in PDUL census)."""
        # Two distinct submissions with no cédula must both succeed
        sub1_id = str(uuid.uuid4())
        payload1 = {
            "client_submission_id": sub1_id,
            "data": {
                "parroquia": "san_simon",
                "zona_residencia_od": "ZONA_03",
                "tipo_vivienda": "rancho",
            },
        }

        sub2_id = str(uuid.uuid4())
        payload2 = {
            "client_submission_id": sub2_id,
            "data": {
                "parroquia": "san_simon",
                "zona_residencia_od": "ZONA_03",
                "tipo_vivienda": "quinta",
            },
        }

        res1 = await client.post(f"/api/v1/encuestas/{survey_id}/respuestas", json=payload1)
        res2 = await client.post(f"/api/v1/encuestas/{survey_id}/respuestas", json=payload2)

        both_201 = res1.status_code == 201 and res2.status_code == 201
        self.record(
            "Cédula-less Submissions - Multiple submissions allowed without collision",
            both_201,
            f"Sub1 status={res1.status_code}, Sub2 status={res2.status_code}",
        )

        # Replay of cédula-less submission must also be idempotent
        res_rep = await client.post(f"/api/v1/encuestas/{survey_id}/respuestas", json=payload1)
        rep_ok = res_rep.status_code == 200 and res_rep.json().get("idempotent_replay") is True
        self.record(
            "Cédula-less Submissions - Idempotent replay supported",
            rep_ok,
            f"Replay status={res_rep.status_code}, idempotent_replay={res_rep.json().get('idempotent_replay')}",
        )


if __name__ == "__main__":
    runner = EmpiricalChallengeRunner()
    success = asyncio.run(runner.run_all())
    sys.exit(0 if success else 1)
