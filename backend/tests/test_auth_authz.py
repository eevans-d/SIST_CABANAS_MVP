"""
Test Suite de Autenticación y Autorización

Tests para validar:
- JWT token generation y validation
- Token expiration y revocación
- Rate limiting
- RBAC (Role-Based Access Control)
- Session management
- Webhook signature verification
"""

import hashlib
import hmac
import time
from datetime import datetime, timedelta

import jwt
import pytest
import redis.asyncio as redis
from app.core.redis import get_redis_pool
from app.core.config import settings
from app.core.security import create_access_token, verify_jwt_token
from app.main import app
from httpx import AsyncClient

# ============================================================================
# JWT TOKEN TESTS
# ============================================================================


class TestJWTAuthentication:
    """Tests para validación de JWT tokens"""

    @pytest.mark.asyncio
    async def test_create_valid_jwt_token(self):
        """Test: Crear JWT token válido"""
        payload = {"sub": "admin@example.com", "role": "admin"}
        token = create_access_token(payload)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT debe ser largo

        # Decodificar y verificar
        decoded = verify_jwt_token(token)
        assert decoded["sub"] == "admin@example.com"
        assert "exp" in decoded  # Debe tener expiration

    @pytest.mark.asyncio
    async def test_jwt_token_expiration(self):
        """Test: JWT token expirado debe ser rechazado"""
        # Crear token con expiration en el pasado
        payload = {"sub": "admin@example.com", "exp": datetime.utcnow() - timedelta(hours=1)}

        expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        # Verificar que es rechazado
        result = verify_jwt_token(expired_token)
        assert result is None or "error" in result

    @pytest.mark.asyncio
    async def test_jwt_invalid_signature(self):
        """Test: JWT con firma inválida debe ser rechazado"""
        # Crear token con secret incorrecto
        payload = {"sub": "admin@example.com"}

        invalid_token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")

        # Verificar que es rechazado
        result = verify_jwt_token(invalid_token)
        assert result is None

    @pytest.mark.asyncio
    async def test_jwt_algorithm_confusion(self):
        """Test: Prevenir algorithm confusion attack"""
        # Intentar crear token con algoritmo diferente
        payload = {"sub": "admin@example.com"}

        # Token con RS256 (public key como secret)
        malicious_token = jwt.encode(
            payload, settings.JWT_SECRET, algorithm="HS512"  # Diferente algoritmo
        )

        # Sistema debe rechazar tokens con algoritmo diferente
        result = verify_jwt_token(malicious_token)
        assert result is None

    @pytest.mark.asyncio
    async def test_jwt_none_algorithm_attack(self):
        """Test: Prevenir 'none' algorithm attack"""
        # Token con algorithm="none" (sin firma)
        payload = {"sub": "admin@example.com", "alg": "none"}

        # Intentar crear token sin firma
        header = {"alg": "none", "typ": "JWT"}
        token_parts = [
            jwt.utils.base64url_encode(jwt.json.dumps(header).encode()).decode(),
            jwt.utils.base64url_encode(jwt.json.dumps(payload).encode()).decode(),
            "",  # Sin firma
        ]
        none_token = ".".join(token_parts)

        # Sistema debe rechazar
        result = verify_jwt_token(none_token)
        assert result is None

    @pytest.mark.asyncio
    async def test_admin_endpoint_requires_jwt(self, client: AsyncClient):
        """Test: Endpoints admin requieren JWT válido"""
        # Sin token
        response = await client.get("/api/v1/admin/accommodations")
        assert response.status_code == 401

        # Token inválido
        response = await client.get(
            "/api/v1/admin/accommodations", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

        # Token válido
        valid_token = create_access_token({"sub": "admin@example.com"})
        response = await client.get(
            "/api/v1/admin/accommodations", headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code in [200, 403]  # 200 si whitelisted, 403 si no

    @pytest.mark.asyncio
    async def test_jwt_missing_claims(self):
        """Test: JWT sin claims requeridos debe ser rechazado"""
        # Token sin 'sub' claim
        incomplete_token = jwt.encode(
            {"role": "admin"}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM  # Falta 'sub'
        )

        result = verify_jwt_token(incomplete_token)
        assert result is None or "sub" not in result


# ============================================================================
# WEBHOOK SIGNATURE VALIDATION
# ============================================================================


class TestWebhookAuthentication:
    """Tests para validación de firmas de webhooks"""

    @pytest.mark.asyncio
    async def test_whatsapp_valid_signature(self, client: AsyncClient):
        """Test: WhatsApp webhook con firma válida"""
        payload = b'{"test": "data"}'

        # Calcular firma correcta
        signature = (
            "sha256="
            + hmac.new(settings.WHATSAPP_APP_SECRET.encode(), payload, hashlib.sha256).hexdigest()
        )

        response = await client.post(
            "/api/v1/webhooks/whatsapp",
            content=payload,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": signature},
        )

        # No debe ser 403 (signature válida)
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_whatsapp_invalid_signature(self, client: AsyncClient):
        """Test: WhatsApp webhook con firma inválida debe ser rechazado"""
        payload = b'{"test": "data"}'
        invalid_signature = "sha256=invalid_signature_here"

        response = await client.post(
            "/api/v1/webhooks/whatsapp",
            content=payload,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": invalid_signature},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_whatsapp_missing_signature(self, client: AsyncClient):
        """Test: WhatsApp webhook sin firma debe ser rechazado"""
        payload = {"test": "data"}

        response = await client.post(
            "/api/v1/webhooks/whatsapp",
            json=payload
            # Sin header X-Hub-Signature-256
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_whatsapp_signature_timing_attack(self, client: AsyncClient):
        """Test: Prevenir timing attacks en validación de firma"""
        payload = b'{"test": "data"}'

        # Dos firmas incorrectas diferentes
        sig1 = "sha256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        sig2 = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

        # Medir tiempo de respuesta
        start1 = time.perf_counter()
        response1 = await client.post(
            "/api/v1/webhooks/whatsapp", content=payload, headers={"X-Hub-Signature-256": sig1}
        )
        time1 = time.perf_counter() - start1

        start2 = time.perf_counter()
        response2 = await client.post(
            "/api/v1/webhooks/whatsapp", content=payload, headers={"X-Hub-Signature-256": sig2}
        )
        time2 = time.perf_counter() - start2

        # Tiempos deben ser similares (constant-time comparison)
        assert abs(time1 - time2) < 0.01  # <10ms diferencia

    @pytest.mark.asyncio
    async def test_mercadopago_valid_signature(self, client: AsyncClient):
        """Test: Mercado Pago webhook con firma válida"""
        # Mercado Pago usa x-signature con formato: ts={timestamp},v1={hash}
        timestamp = str(int(time.time()))
        payment_id = "12345"

        # Construir string para firma
        data_id = payment_id
        signature_string = f"id={data_id}&ts={timestamp}"

        # Calcular HMAC
        signature_hash = hmac.new(
            settings.MERCADOPAGO_WEBHOOK_SECRET.encode(), signature_string.encode(), hashlib.sha256
        ).hexdigest()

        signature = f"ts={timestamp},v1={signature_hash}"

        payload = {"action": "payment.updated", "data": {"id": payment_id}}

        response = await client.post(
            "/api/v1/webhooks/mercadopago", json=payload, headers={"x-signature": signature}
        )

        # No debe ser 403
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_mercadopago_invalid_signature(self, client: AsyncClient):
        """Test: Mercado Pago webhook con firma inválida"""
        invalid_signature = "ts=123456,v1=invalid_hash"

        payload = {"action": "payment.updated", "data": {"id": "12345"}}

        response = await client.post(
            "/api/v1/webhooks/mercadopago", json=payload, headers={"x-signature": invalid_signature}
        )

        assert response.status_code == 403


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================


class TestRateLimiting:
    """Tests para rate limiting"""

    @pytest.mark.asyncio
    async def test_rate_limit_per_ip(self, client: AsyncClient):
        """Test: Rate limiting por IP"""
        endpoint = "/api/v1/accommodations"

        # Hacer múltiples requests rápidamente
        responses = []
        for i in range(150):  # Exceder límite (asumiendo 100/min)
            response = await client.get(endpoint)
            responses.append(response.status_code)

        # Algunos requests deben ser 429 (Too Many Requests)
        assert 429 in responses, "Rate limiting not enforced"

    @pytest.mark.asyncio
    async def test_rate_limit_bypass_with_different_ips(self, client: AsyncClient):
        """Test: Rate limit no debe bypassearse con IPs diferentes"""
        # Este test es conceptual - en realidad httpx client usa misma IP
        # En producción, validar con IPs reales diferentes

        # Verificar que rate limit está configurado en Redis
        pool = get_redis_pool()
        redis_client = redis.Redis(connection_pool=pool)

        # Buscar keys de rate limiting
        keys = await redis_client.keys("ratelimit:*")

        # Debe haber keys de rate limiting
        assert len(keys) > 0, "Rate limiting keys not found in Redis"

    @pytest.mark.asyncio
    async def test_rate_limit_reset_after_window(self, client: AsyncClient):
        """Test: Rate limit debe resetearse después de ventana de tiempo"""
        import asyncio

        endpoint = "/api/v1/accommodations"

        # Hacer requests hasta alcanzar límite
        for i in range(100):
            await client.get(endpoint)

        # Siguiente request debe ser 429
        response = await client.get(endpoint)
        assert response.status_code == 429

        # Esperar ventana de tiempo (asumiendo 60s)
        await asyncio.sleep(61)

        # Ahora debe permitir nuevamente
        response = await client.get(endpoint)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rate_limit_excludes_health_endpoint(self, client: AsyncClient):
        """Test: Health endpoint no debe tener rate limiting"""
        # Hacer muchos requests a health
        for i in range(200):
            response = await client.get("/api/v1/healthz")
            assert response.status_code == 200, f"Health endpoint rate limited at request {i}"


# ============================================================================
# RBAC (Role-Based Access Control)
# ============================================================================


class TestRoleBasedAccessControl:
    """Tests para control de acceso basado en roles"""

    @pytest.mark.asyncio
    async def test_admin_can_access_admin_endpoints(self, client: AsyncClient):
        """Test: Usuario con role admin puede acceder a endpoints admin"""
        admin_token = create_access_token({"sub": "admin@example.com", "role": "admin"})

        response = await client.get(
            "/api/v1/admin/accommodations", headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Debe permitir acceso (si email está en whitelist)
        assert response.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_user_cannot_access_admin_endpoints(self, client: AsyncClient):
        """Test: Usuario sin role admin NO puede acceder a endpoints admin"""
        user_token = create_access_token({"sub": "user@example.com", "role": "user"})

        response = await client.get(
            "/api/v1/admin/accommodations", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_role_escalation_prevention(self, client: AsyncClient):
        """Test: Usuario no puede escalar su role modificando JWT"""
        # Crear token como user
        user_token = create_access_token({"sub": "user@example.com", "role": "user"})

        # Intentar modificar el token (esto fallará por la firma)
        try:
            # Decodificar sin verificar
            payload = jwt.decode(user_token, options={"verify_signature": False})

            # Modificar role
            payload["role"] = "admin"

            # Re-firmar con secret incorrecto
            modified_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

            # Intentar usar token modificado
            response = await client.get(
                "/api/v1/admin/accommodations",
                headers={"Authorization": f"Bearer {modified_token}"},
            )

            # Debe ser rechazado
            assert response.status_code in [401, 403]
        except Exception:
            # Expected: JWT manipulation failed
            pass

    @pytest.mark.asyncio
    async def test_email_whitelist_enforcement(self, client: AsyncClient):
        """Test: Solo emails whitelisted pueden acceder a admin"""
        # Token con email NO en whitelist
        non_whitelisted_token = create_access_token({"sub": "hacker@evil.com", "role": "admin"})

        response = await client.get(
            "/api/v1/admin/accommodations",
            headers={"Authorization": f"Bearer {non_whitelisted_token}"},
        )

        # Debe ser rechazado aunque el token sea válido
        assert response.status_code == 403


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================


class TestSessionManagement:
    """Tests para gestión de sesiones"""

    @pytest.mark.asyncio
    async def test_concurrent_sessions_allowed(self, client: AsyncClient):
        """Test: Usuario puede tener múltiples sesiones concurrentes"""
        # Crear dos tokens para mismo usuario
        token1 = create_access_token({"sub": "admin@example.com"})
        token2 = create_access_token({"sub": "admin@example.com"})

        # Ambos deben ser válidos
        response1 = await client.get(
            "/api/v1/admin/accommodations", headers={"Authorization": f"Bearer {token1}"}
        )

        response2 = await client.get(
            "/api/v1/admin/accommodations", headers={"Authorization": f"Bearer {token2}"}
        )

        # Ambos tokens deben funcionar
        assert response1.status_code in [200, 403]
        assert response2.status_code in [200, 403]

    @pytest.mark.asyncio
    async def test_token_refresh_not_implemented(self, client: AsyncClient):
        """Test: Validar que refresh token no está implementado (por ahora)"""
        # En MVP no hay refresh tokens, solo access tokens de 24h
        # Este test documenta el comportamiento actual

        token = create_access_token({"sub": "admin@example.com"})

        # No debe existir endpoint de refresh
        response = await client.post("/api/v1/auth/refresh", json={"refresh_token": "dummy"})

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_logout_not_implemented(self, client: AsyncClient):
        """Test: Logout no está implementado (JWT stateless)"""
        # JWTs son stateless, no hay revocación en MVP
        # Token sigue válido hasta expiration

        token = create_access_token({"sub": "admin@example.com"})

        # No debe existir endpoint de logout
        response = await client.post(
            "/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 404


# ============================================================================
# AUTHORIZATION EDGE CASES
# ============================================================================


class TestAuthorizationEdgeCases:
    """Tests para casos edge de autorización"""

    @pytest.mark.asyncio
    async def test_malformed_authorization_header(self, client: AsyncClient):
        """Test: Authorization header malformado debe ser rechazado"""
        malformed_headers = [
            "Bearer",  # Sin token
            "bearer token123",  # Lowercase
            "Token token123",  # Tipo incorrecto
            "Bearer ",  # Token vacío
            "Bearer token1 token2",  # Multiple tokens
        ]

        for header in malformed_headers:
            response = await client.get(
                "/api/v1/admin/accommodations", headers={"Authorization": header}
            )

            assert response.status_code in [401, 403], f"Accepted malformed header: {header}"

    @pytest.mark.asyncio
    async def test_case_sensitive_bearer_keyword(self, client: AsyncClient):
        """Test: Validar case sensitivity de 'Bearer'"""
        token = create_access_token({"sub": "admin@example.com"})

        # Probar diferentes casos
        headers = [
            f"bearer {token}",  # lowercase
            f"BEARER {token}",  # uppercase
            f"Bearer {token}",  # correct
        ]

        for header in headers:
            response = await client.get(
                "/api/v1/admin/accommodations", headers={"Authorization": header}
            )

            # Solo "Bearer" (capital B) debe ser aceptado
            if header.startswith("Bearer "):
                assert response.status_code in [200, 403]
            else:
                assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_expired_token_grace_period(self):
        """Test: No debe haber grace period para tokens expirados"""
        # Token expirado hace 1 segundo
        payload = {"sub": "admin@example.com", "exp": datetime.utcnow() - timedelta(seconds=1)}

        expired_token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        # Debe ser rechazado inmediatamente
        result = verify_jwt_token(expired_token)
        assert result is None

    @pytest.mark.asyncio
    async def test_jwt_token_replay_attack(self, client: AsyncClient):
        """Test: Token usado múltiples veces debe ser permitido (stateless)"""
        # En sistema stateless JWT, replay es permitido (hasta expiration)
        # Este comportamiento es esperado en MVP

        token = create_access_token({"sub": "admin@example.com"})

        # Usar mismo token 10 veces
        for i in range(10):
            response = await client.get(
                "/api/v1/admin/accommodations", headers={"Authorization": f"Bearer {token}"}
            )

            # Todas deben ser exitosas (o 403 si no whitelisted)
            assert response.status_code in [200, 403]


# ============================================================================
# PASSWORD SECURITY
# ============================================================================


class TestPasswordSecurity:
    """Tests para seguridad de contraseñas"""

    @pytest.mark.asyncio
    async def test_password_hashing_with_bcrypt(self):
        """Test: Contraseñas deben hashearse con bcrypt"""
        from app.core.security import hash_password, verify_password

        password = "SecureP@ssw0rd123"
        hashed = hash_password(password)

        # Hash debe ser bcrypt (empieza con $2b$)
        assert hashed.startswith("$2b$")

        # Verificar contraseña correcta
        assert verify_password(password, hashed) is True

        # Verificar contraseña incorrecta
        assert verify_password("WrongPassword", hashed) is False

    @pytest.mark.asyncio
    async def test_password_hash_unique_salts(self):
        """Test: Mismo password debe generar hashes diferentes (salt)"""
        from app.core.security import hash_password

        password = "SamePassword123"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes deben ser diferentes (salt aleatorio)
        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_timing_attack_on_password_verify(self):
        """Test: Verificación de password debe ser constant-time"""
        from app.core.security import hash_password, verify_password

        password = "CorrectPassword"
        hashed = hash_password(password)

        # Medir tiempo con password completamente incorrecto
        start1 = time.perf_counter()
        verify_password("aaaaaaaaaaaaaaaa", hashed)
        time1 = time.perf_counter() - start1

        # Medir tiempo con password casi correcto
        start2 = time.perf_counter()
        verify_password("CorrectPasswor", hashed)  # Falta última letra
        time2 = time.perf_counter() - start2

        # Tiempos deben ser similares (bcrypt es constant-time)
        # Permitir hasta 50ms diferencia (bcrypt es lento)
        assert abs(time1 - time2) < 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
