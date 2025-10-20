#!/bin/bash

# ============================================================================
# QUICK START: GUÍA RÁPIDA PARA ACTIVACIÓN A PRODUCCIÓN
# ============================================================================

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                   ⚡ QUICK START - ACTIVACIÓN A PRODUCCIÓN ⚡                  ║
║                                                                                ║
║                   SIST_CABAÑAS MVP - Sistema de Reservas                      ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝

🎯 OBJETIVO: Desplegar aplicación en Fly.io en 25 minutos.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 ESTADO ACTUAL (Resumen Validación)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Backend MVP: 100% completo
✅ Fly.io CLI: Instalado (v0.3.195)
❌ Fly.io Auth: PENDIENTE (necesita login interactivo)
✅ Validación pre-deploy: 15/15 checks listos
✅ Scripts de activación: 4 archivos, listos para ejecutar

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 FLUJO DE ACTIVACIÓN (4 FASES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔵 FASE 0: AUTENTICACIÓN (5 minutos) ⏳ REQUERIDA AHORA
   └─ Paso 1: Login con Fly.io
   └─ Paso 2: Re-validación (debe mostrar 15/15 ✅)

🟢 FASE 1: SETUP FLY.IO (10 minutos)
   └─ Crear PostgreSQL en región eze (Buenos Aires)
   └─ Conectar database a la app
   └─ Generar 5 secretos criptográficos
   └─ Configurar secretos en Fly.io

🟡 FASE 2: DEPLOY (5 minutos)
   └─ Re-validación pre-deploy
   └─ Ejecutar: flyctl deploy --strategy immediate
   └─ Monitoreo de logs en vivo

🟣 FASE 3: SMOKE TESTS (5 minutos)
   └─ Test 1: Health check (/api/v1/healthz)
   └─ Test 2: Readiness (/api/v1/readyz)
   └─ Test 3: Metrics (/metrics)
   └─ Test 4: Homepage (/)
   └─ Test 5: Database connectivity (SSH)

   = 25 MINUTOS TOTALES → 🎉 PRODUCCIÓN LIVE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 ARCHIVOS DISPONIBLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. activation_complete.sh ........... Script maestro (orquesta todas las fases)
2. fase_1_setup.sh ................. Setup Fly.io + PostgreSQL + Secrets
3. fase_2_deploy.sh ................ Deploy a producción
4. fase_3_smoke_tests.sh ........... 5 tests de validación
5. pre_deploy_validation.sh ........ Validación pre-deploy (15 checks)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ EMPEZAR (2 OPCIONES)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OPCIÓN A: MODO AUTOMÁTICO (RECOMENDADO)
──────────────────────────────────────

Ejecuta todo de una vez (con confirmaciones en cada fase):

  bash activation_complete.sh

✨ Beneficios:
  • Automatiza las 4 fases
  • Validaciones integradas
  • Pausas para confirmar entre fases
  • Manejo de errores automático

OPCIÓN B: MODO MANUAL (CONTROL TOTAL)
──────────────────────────────────────

Ejecuta cada fase por separado:

  # FASE 0: Autenticación (MANUAL)
  export PATH="/home/eevan/.fly/bin:$PATH"
  flyctl auth login
  ./pre_deploy_validation.sh

  # FASE 1: Setup
  bash fase_1_setup.sh

  # FASE 2: Deploy
  bash fase_2_deploy.sh

  # FASE 3: Tests
  bash fase_3_smoke_tests.sh

✨ Beneficios:
  • Control granular
  • Debugging más fácil
  • Pausas para inspeccionar cada paso

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 FASE 0: AUTENTICACIÓN (ANTES DE CONTINUAR)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  EJECUTA LOGIN:

    export PATH="/home/eevan/.fly/bin:$PATH" && flyctl auth login

2️⃣  AUTORIZA EN EL BROWSER:
    
    • Se abrirá https://fly.io/app/auth/cli/
    • Si no se abre, copia el link del terminal
    • Pega el device code en el browser
    • Click en "Authorize"

3️⃣  VERIFICA AUTENTICACIÓN:

    flyctl auth whoami
    
    ✅ Debería mostrar tu email

4️⃣  RE-VALIDA:

    ./pre_deploy_validation.sh
    
    ✅ Debería mostrar 15/15 ✅

5️⃣  ENTONCES CONTINÚA:

    bash activation_complete.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❓ TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

P: "flyctl: command not found"
R: Ejecuta: export PATH="/home/eevan/.fly/bin:$PATH"

P: "Error: No access token available"
R: Ejecuta: flyctl auth login

P: "FASE 1 falla en crear PostgreSQL"
R: Verifica: flyctl apps list | grep sist-cabanas-mvp
   Si no existe, debes crear la app primero.

P: "FASE 2 falla en deploy"
R: Revisa logs: flyctl logs -f --app sist-cabanas-mvp

P: "Smoke tests fallan"
R: SSH a la máquina: flyctl ssh console --app sist-cabanas-mvp

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CRITERIOS DE ÉXITO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ FASE 1 OK:
   • PostgreSQL creado en eze
   • Database conectada
   • 5 secretos en Fly.io

✅ FASE 2 OK:
   • Build completó sin errores
   • Release command OK
   • Health check PASSING

✅ FASE 3 OK:
   • 5/5 tests PASADOS
   • URL en vivo: https://sist-cabanas-mvp.fly.dev
   • Logs sin errores críticos

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 SIGUIENTE PASO INMEDIATO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Abre terminal en este directorio:
   cd /home/eevan/ProyectosIA/SIST_CABAÑAS

2. Ejecuta FASE 0 (autenticación):
   export PATH="/home/eevan/.fly/bin:$PATH" && flyctl auth login

3. Luego retorna y ejecuta:
   bash activation_complete.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

¡Listos para ir a producción en 25 minutos! 🚀

EOF
