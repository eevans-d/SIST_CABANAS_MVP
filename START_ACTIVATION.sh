#!/bin/bash

# 🚀 COMANDO ÚNICO PARA ACTIVACIÓN A PRODUCCIÓN
# Ejecuta esto después de fazer login con Fly.io

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════════╗
║                     🚀 COMANDO ÚNICO PARA ACTIVACIÓN                          ║
║                                                                                ║
║  Este es el comando FINAL que te llevará de DESARROLLO a PRODUCCIÓN en        ║
║  ~25 minutos. Solo necesitas ejecutarlo UNA VEZ después del login.            ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝


📋 CHECKLIST PRE-ACTIVACIÓN (5 segundos):

  [ ] Terminal en: /home/eevan/ProyectosIA/SIST_CABAÑAS
  [ ] PATH configurado: export PATH="/home/eevan/.fly/bin:$PATH"
  [ ] Autenticado: flyctl auth whoami (muestra tu email)
  [ ] Validado: ./pre_deploy_validation.sh (muestra 15/15 ✅)
  [ ] Git clean: git status (no hay cambios sin commitear)


🎯 COMANDO ÚNICO - CÓPIALO Y EJECUTA:

  bash activation_complete.sh


⏱️  QUÉ SUCEDERÁ DESPUÉS:

  1. Script mostrará opción de continuar → Presiona 's' (sí)
  2. FASE 1 (~10 min): Crea PostgreSQL, configura secretos
  3. Script pausará → Presiona 's' para continuar
  4. FASE 2 (~5 min): Deploy automático a Fly.io
  5. Script pausará → Presiona 's' para continuar
  6. FASE 3 (~5 min): 5 smoke tests de validación
  7. ✅ RESULTADO: APP EN VIVO en https://sist-cabanas-mvp.fly.dev


📊 RESULTADO ESPERADO AL FINAL:

  ╔════════════════════════════════════════════╗
  ║ 🎉 ¡ACTIVACIÓN COMPLETADA EXITOSAMENTE! 🎉 ║
  ║                                            ║
  ║ 🌐 APLICACIÓN EN VIVO:                      ║
  ║    https://sist-cabanas-mvp.fly.dev        ║
  ║                                            ║
  ║ 📊 DASHBOARD:                               ║
  ║    https://fly.io/apps/sist-cabanas-mvp    ║
  ║                                            ║
  ║ ✅ 5/5 SMOKE TESTS PASADOS                 ║
  ║                                            ║
  ║ 🔗 PRÓXIMOS PASOS:                          ║
  ║    1. Monitorear: flyctl logs -f ...       ║
  ║    2. Probar: curl https://...healthz      ║
  ║    3. Verificar métricas: /metrics         ║
  ║                                            ║
  ╚════════════════════════════════════════════╝


💡 ALTERNATIVAS:

  Si prefieres ejecutar fases individualmente:
    1. bash fase_1_setup.sh
    2. bash fase_2_deploy.sh
    3. bash fase_3_smoke_tests.sh

  Si quieres ver más documentación:
    • QUICK_START.sh - Guía visual
    • ACTIVATION_GUIDE.md - Guía completa


🆘 SI ALGO FALLA:

  Ver logs en vivo:
    flyctl logs -f --app sist-cabanas-mvp

  SSH a máquina de Fly.io:
    flyctl ssh console --app sist-cabanas-mvp

  Rollback:
    flyctl releases rollback --app sist-cabanas-mvp


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                  👉 COPIA Y EJECUTA ESTE COMANDO AHORA:

                         bash activation_complete.sh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
