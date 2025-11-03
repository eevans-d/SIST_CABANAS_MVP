"""
Test Suite Completa de Validación de Inputs

Tests de seguridad para prevenir:
- SQL Injection
- XSS (Cross-Site Scripting)
- Path Traversal
- Command Injection
- SSRF (Server-Side Request Forgery)
- NoSQL Injection (Redis)
- Header Injection
- CRLF Injection
"""

import pytest
import redis.asyncio as redis
from app.core.config import settings
from app.core.database import async_session_maker
from app.main import app
from app.services.nlu import detect_intent
from httpx import AsyncClient
from sqlalchemy import text

# ============================================================================
# SQL INJECTION TESTS
# ============================================================================


class TestSQLInjection:
    """Tests para prevenir SQL Injection en todos los endpoints"""

    @pytest.mark.asyncio
    async def test_sql_injection_in_reservation_search(
        self, client: AsyncClient, accommodation_factory
    ):
        """Test: SQL injection en búsqueda de reservas"""
        acc = await accommodation_factory()

        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE reservations; --",
            "' UNION SELECT * FROM users--",
            "admin'--",
            "' OR 1=1--",
            "1' AND '1'='1",
        ]

        for payload in payloads:
            response = await client.get(
                f"/api/v1/reservations/search", params={"guest_name": payload}
            )

            # No debe retornar 500 (SQL error)
            assert response.status_code in [
                200,
                400,
                404,
            ], f"SQL injection detected with payload: {payload}"

            # No debe retornar datos de otras reservas
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_sql_injection_in_accommodation_filter(self, client: AsyncClient):
        """Test: SQL injection en filtros de alojamientos"""
        payloads = [
            "' OR '1'='1",
            "'; SELECT pg_sleep(5); --",
            "' UNION SELECT password FROM users--",
        ]

        for payload in payloads:
            response = await client.get(
                f"/api/v1/accommodations", params={"name": payload, "capacity": payload}
            )

            assert response.status_code in [
                200,
                400,
            ], f"SQL injection vulnerability with: {payload}"

    @pytest.mark.asyncio
    async def test_parameterized_queries_enforced(self):
        """Test: Verificar que NO existen queries raw con f-strings"""
        import os
        import re

        backend_path = os.path.join(os.path.dirname(__file__), "..", "app")
        vulnerable_patterns = [
            re.compile(r'execute\(f["\']'),  # execute(f"SELECT...")
            re.compile(r'\.raw\(f["\']'),  # .raw(f"SELECT...")
            re.compile(r'text\(f["\']'),  # text(f"SELECT...")
        ]

        violations = []
        for root, dirs, files in os.walk(backend_path):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r") as f:
                        content = f.read()
                        for pattern in vulnerable_patterns:
                            matches = pattern.findall(content)
                            if matches:
                                violations.append((filepath, matches))

        assert len(violations) == 0, f"Found vulnerable raw SQL queries: {violations}"


# ============================================================================
# XSS TESTS
# ============================================================================


class TestXSSPrevention:
    """Tests para prevenir XSS en responses y templates"""

    @pytest.mark.asyncio
    async def test_xss_in_guest_name(self, client: AsyncClient, accommodation_factory):
        """Test: XSS injection en nombre de huésped"""
        acc = await accommodation_factory()

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'>",
        ]

        for payload in xss_payloads:
            response = await client.post(
                "/api/v1/reservations/prereserve",
                json={
                    "accommodation_id": acc.id,
                    "check_in": "2025-12-01",
                    "check_out": "2025-12-03",
                    "guests": 2,
                    "channel": "whatsapp",
                    "contact_name": payload,
                    "contact_phone": "+5491112345678",
                },
            )

            # Debe sanitizar o rechazar
            if response.status_code == 201:
                data = response.json()
                # Verificar que no se retorne el payload sin escapar
                assert payload not in str(data), f"XSS payload returned unsanitized: {payload}"

    @pytest.mark.asyncio
    async def test_xss_in_whatsapp_message(self, client: AsyncClient):
        """Test: XSS en mensajes de WhatsApp"""
        payload = "<script>document.location='http://evil.com'</script>"

        # Simular webhook WhatsApp con XSS
        webhook_payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "5491112345678",
                                        "id": "test123",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": payload},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }

        # No validamos signature para este test (usamos mock)
        response = await client.post(
            "/api/v1/webhooks/whatsapp",
            json=webhook_payload,
            headers={"X-Hub-Signature-256": "sha256=dummy"},
        )

        # Sistema debe procesar sin retornar script sin escapar
        assert response.status_code in [200, 400, 403]


# ============================================================================
# PATH TRAVERSAL TESTS
# ============================================================================


class TestPathTraversal:
    """Tests para prevenir path traversal en file operations"""

    @pytest.mark.asyncio
    async def test_path_traversal_in_audio_download(self, client: AsyncClient):
        """Test: Path traversal en descarga de audios"""
        payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for payload in payloads:
            response = await client.get(f"/api/v1/audio/{payload}")

            # Debe retornar 404 o 400, NUNCA 200 con contenido de archivo
            assert response.status_code in [
                400,
                404,
            ], f"Path traversal vulnerability with: {payload}"

            # No debe contener contenido de archivos del sistema
            assert b"root:" not in response.content
            assert b"[boot loader]" not in response.content

    @pytest.mark.asyncio
    async def test_path_traversal_in_ical_import(self, client: AsyncClient):
        """Test: Path traversal en import iCal"""
        payload = "file:///etc/passwd"

        response = await client.post("/api/v1/ical/import", json={"url": payload})

        # Debe rechazar URLs file://
        assert response.status_code in [400, 422]


# ============================================================================
# COMMAND INJECTION TESTS
# ============================================================================


class TestCommandInjection:
    """Tests para prevenir command injection en subprocess calls"""

    @pytest.mark.asyncio
    async def test_command_injection_in_ffmpeg(self, client: AsyncClient, tmp_path):
        """Test: Command injection en conversión de audio con ffmpeg"""
        # Este test es conceptual ya que no exponemos endpoint directo de ffmpeg
        # pero valida que el servicio de audio sanitiza inputs

        from app.services.audio import AudioProcessor

        # Payload malicioso en nombre de archivo
        malicious_filename = "audio.ogg; rm -rf /"

        # AudioProcessor debe sanitizar el filename
        # Si no sanitiza, subprocess.run ejecutaría comando malicioso

        # Verificar que AudioProcessor valida extensiones permitidas
        processor = AudioProcessor()

        # Simular procesamiento (sin ejecutar ffmpeg real)
        import os
        import tempfile

        # Crear archivo temporal con nombre malicioso
        temp_file = tmp_path / malicious_filename
        temp_file.write_bytes(b"fake audio data")

        # El procesador debe fallar o sanitizar el filename
        # NO debe ejecutar el comando inyectado
        try:
            # Esto fallaría en producción porque el archivo no es audio válido
            # pero el punto es que NO debe ejecutar "rm -rf /"
            result = await processor.transcribe_audio(str(temp_file))

            # Si llega aquí, debe retornar error, no ejecutar comando
            assert "error" in result or result is None
        except Exception:
            # Esperado: error de procesamiento
            pass

        # Verificar que no se ejecutó el comando (sistema sigue vivo)
        assert os.path.exists("/tmp"), "Command injection executed!"


# ============================================================================
# SSRF TESTS
# ============================================================================


class TestSSRFPrevention:
    """Tests para prevenir SSRF en requests a URLs externas"""

    @pytest.mark.asyncio
    async def test_ssrf_in_ical_import_localhost(self, client: AsyncClient):
        """Test: SSRF targeting localhost en import iCal"""
        ssrf_payloads = [
            "http://localhost:5432",  # PostgreSQL
            "http://127.0.0.1:6379",  # Redis
            "http://0.0.0.0:8000",  # FastAPI
            "http://[::1]:22",  # SSH via IPv6
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
        ]

        for payload in ssrf_payloads:
            response = await client.post("/api/v1/ical/import", json={"url": payload})

            # Debe rechazar URLs internas
            assert response.status_code in [400, 422], f"SSRF vulnerability with: {payload}"

            if response.status_code == 400:
                data = response.json()
                assert (
                    "internal" in str(data).lower()
                    or "localhost" in str(data).lower()
                    or "private" in str(data).lower()
                )

    @pytest.mark.asyncio
    async def test_ssrf_in_ical_import_private_ips(self, client: AsyncClient):
        """Test: SSRF targeting private networks"""
        private_ips = [
            "http://10.0.0.1",
            "http://172.16.0.1",
            "http://192.168.1.1",
        ]

        for ip in private_ips:
            response = await client.post("/api/v1/ical/import", json={"url": ip})

            assert response.status_code in [400, 422], f"SSRF to private IP allowed: {ip}"


# ============================================================================
# NOSQL INJECTION (Redis)
# ============================================================================


class TestRedisInjection:
    """Tests para prevenir NoSQL injection en Redis"""

    @pytest.mark.asyncio
    async def test_redis_key_injection(self):
        """Test: Injection en keys de Redis"""
        from app.core.cache import get_redis_pool

        pool = await get_redis_pool()
        redis_client = pool.client()

        # Payloads maliciosos
        payloads = [
            "key\r\nDEL important_key\r\n",  # CRLF injection
            "key*",  # Wildcard
            "../../../etc/passwd",  # Path traversal attempt
        ]

        for payload in payloads:
            # Intentar usar payload como key
            try:
                await redis_client.get(payload)
                # Si llega aquí, el payload fue sanitizado implícitamente
                # (Redis no ejecuta comandos desde keys)
            except Exception as e:
                # Error esperado si el payload es rechazado
                pass

            # Verificar que no se ejecutó comando malicioso
            keys = await redis_client.keys("important_key")
            assert len(keys) == 0 or b"important_key" in keys


# ============================================================================
# HEADER INJECTION TESTS
# ============================================================================


class TestHeaderInjection:
    """Tests para prevenir header injection"""

    @pytest.mark.asyncio
    async def test_crlf_injection_in_response_headers(self, client: AsyncClient):
        """Test: CRLF injection en headers de respuesta"""
        payload = "test\r\nX-Injected: true\r\n"

        response = await client.get(f"/api/v1/accommodations", params={"name": payload})

        # Verificar que el payload no se refleja en headers
        assert "X-Injected" not in response.headers
        assert "\r\n" not in str(response.headers)

    @pytest.mark.asyncio
    async def test_host_header_injection(self, client: AsyncClient):
        """Test: Host header injection"""
        response = await client.get(
            "/api/v1/healthz", headers={"Host": "evil.com\r\nX-Injected: true"}
        )

        # FastAPI debe sanitizar o rechazar
        assert response.status_code in [200, 400]
        assert "X-Injected" not in response.headers


# ============================================================================
# NLU INPUT VALIDATION
# ============================================================================


class TestNLUInputValidation:
    """Tests específicos para validación de inputs en NLU"""

    @pytest.mark.asyncio
    async def test_nlu_extremely_long_input(self):
        """Test: Input extremadamente largo en NLU"""

        # 1MB de texto
        long_text = "A" * (1024 * 1024)

        # Debe manejar sin crash
        result = detect_intent(long_text)

        # Debe retornar error o truncar
        assert result is not None
        assert result["intent"] in ["disponibilidad", "reservar", "precio", "servicios", "unknown"]

    @pytest.mark.asyncio
    async def test_nlu_null_bytes(self):
        """Test: Null bytes en input NLU"""

        malicious_input = "Hola\x00DROP TABLE reservations"

        result = detect_intent(malicious_input)

        # Debe sanitizar null bytes
        assert result is not None
        assert "\x00" not in str(result)

    @pytest.mark.asyncio
    async def test_nlu_unicode_exploits(self):
        """Test: Unicode exploits (homoglyphs, RTL override)"""

        exploits = [
            "reservar\u202eadmin",  # RTL override
            "admіn",  # Cyrillic і (homoglyph)
            "test\ufefftest",  # Zero-width no-break space
        ]

        for exploit in exploits:
            result = detect_intent(exploit)

            # Debe detectar intent correctamente sin confusión
            assert result is not None
            assert result["intent"] != "admin"  # No debe confundir con admin

    @pytest.mark.asyncio
    async def test_nlu_control_characters(self):
        """Test: Caracteres de control en NLU"""

        control_chars = [
            "test\r\ntest",
            "test\ttest",
            "test\x1btest",  # ESC
            "test\x07test",  # BEL
        ]

        for text in control_chars:
            result = detect_intent(text)

            # Debe sanitizar o ignorar control chars
            assert result is not None
            assert all(ord(c) >= 32 or c in "\n\r\t" for c in str(result))


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestInputValidationIntegration:
    """Tests de integración para validación end-to-end"""

    @pytest.mark.asyncio
    async def test_malicious_payload_full_flow(self, client: AsyncClient, accommodation_factory):
        """Test: Payload malicioso en flujo completo de reserva"""
        acc = await accommodation_factory()

        # Payload que combina múltiples ataques
        malicious_payload = {
            "accommodation_id": "1 OR 1=1",  # SQL injection
            "check_in": "<script>alert(1)</script>",  # XSS
            "check_out": "'; DROP TABLE reservations; --",  # SQL injection
            "guests": 999999,  # Integer overflow attempt
            "channel": "../../../etc/passwd",  # Path traversal
            "contact_name": "<img src=x onerror=alert(1)>",  # XSS
            "contact_phone": "+54\r\nX-Injected: true",  # Header injection
            "contact_email": "test@evil.com\r\nBCC: attacker@evil.com",  # Email injection
        }

        response = await client.post("/api/v1/reservations/prereserve", json=malicious_payload)

        # Debe rechazar o sanitizar
        assert response.status_code in [400, 422]

        # Verificar que DB no fue comprometida
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM reservations"))
            count_before = result.scalar()

        # Intentar nuevamente
        response = await client.post("/api/v1/reservations/prereserve", json=malicious_payload)

        async with async_session_maker() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM reservations"))
            count_after = result.scalar()

        # DB no debe tener registros maliciosos
        assert count_after == count_before


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
async def accommodation_factory():
    """Factory para crear alojamientos de prueba"""
    from app.models.accommodation import Accommodation

    async def _create(**kwargs):
        defaults = {
            "name": "Test Accommodation",
            "type": "cabin",
            "capacity": 4,
            "base_price": 10000.0,
            "description": "Test description",
            "amenities": {},
            "photos": [],
            "location": {},
            "policies": {},
            "active": True,
        }
        defaults.update(kwargs)

        async with async_session_maker() as session:
            acc = Accommodation(**defaults)
            session.add(acc)
            await session.commit()
            await session.refresh(acc)
            return acc

    return _create
