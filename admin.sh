#!/bin/bash
# Script maestro para administrar el Sistema de Alojamientos
# Centraliza todas las operaciones de configuración, mantenimiento y monitoreo

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Banner del sistema
show_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "🏠 ======================================================"
    echo "   SISTEMA AGÉNTICO MVP DE ALOJAMIENTOS"
    echo "   Administrador Maestro v1.0"
    echo "======================================================${NC}"
    echo ""
}

# Función para imprimir mensajes con colores
print_status() {
    local message="$1"
    local status="${2:-INFO}"

    case $status in
        "SUCCESS") echo -e "${GREEN}✅ $message${NC}" ;;
        "ERROR")   echo -e "${RED}❌ $message${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "INFO")    echo -e "${BLUE}ℹ️  $message${NC}" ;;
        "STEP")    echo -e "${MAGENTA}🔧 $message${NC}" ;;
        "HEADER")  echo -e "${CYAN}${BOLD}📋 $message${NC}" ;;
    esac
}

# Verificar que estamos en el directorio correcto
check_project_directory() {
    if [ ! -f "docker-compose.yml" ]; then
        print_status "Error: No se encuentra docker-compose.yml" "ERROR"
        print_status "Ejecutar desde el directorio raíz del proyecto" "ERROR"
        exit 1
    fi

    if [ ! -d "backend" ]; then
        print_status "Error: No se encuentra el directorio backend" "ERROR"
        exit 1
    fi
}

# Verificar estado del sistema
check_system_status() {
    print_status "Verificando estado del sistema..." "STEP"

    # Verificar Docker
    if ! docker --version >/dev/null 2>&1; then
        print_status "Docker no está instalado o no está disponible" "ERROR"
        return 1
    fi

    # Verificar Docker Compose
    if ! docker-compose --version >/dev/null 2>&1; then
        print_status "Docker Compose no está instalado" "ERROR"
        return 1
    fi

    # Verificar si los contenedores están ejecutándose
    if docker-compose ps | grep -q "Up"; then
        print_status "Sistema ejecutándose" "SUCCESS"

        # Verificar health check
        if curl -s http://localhost/api/v1/healthz >/dev/null 2>&1; then
            print_status "API respondiendo correctamente" "SUCCESS"
            return 0
        else
            print_status "API no responde - revisar logs" "WARNING"
            return 1
        fi
    else
        print_status "Sistema no está ejecutándose" "WARNING"
        return 1
    fi
}

# Mostrar menú principal
show_main_menu() {
    echo -e "${BOLD}🎯 MENÚ PRINCIPAL${NC}"
    echo "=================================="
    echo "1)  🚀 Iniciar/Reiniciar Sistema"
    echo "2)  🛑 Detener Sistema"
    echo "3)  📊 Estado y Monitoreo"
    echo "4)  🔧 Configuración"
    echo "5)  🧪 Pruebas y Validación"
    echo "6)  💾 Backup y Restauración"
    echo "7)  📋 Logs y Diagnóstico"
    echo "8)  📖 Documentación y Ayuda"
    echo "9)  🚪 Salir"
    echo ""
    echo -n "Seleccione una opción [1-9]: "
}

# Submenú de configuración
show_config_menu() {
    echo -e "${BOLD}🔧 CONFIGURACIÓN${NC}"
    echo "=================================="
    echo "1)  🔐 Configurar SSL/HTTPS"
    echo "2)  📱 Configurar WhatsApp"
    echo "3)  📅 Configurar iCal"
    echo "4)  💳 Configurar MercadoPago"
    echo "5)  ⚙️  Variables de Entorno"
    echo "6)  🐳 Configuración Docker"
    echo "7)  🔙 Volver al menú principal"
    echo ""
    echo -n "Seleccione una opción [1-7]: "
}

# Submenú de pruebas
show_test_menu() {
    echo -e "${BOLD}🧪 PRUEBAS Y VALIDACIÓN${NC}"
    echo "=================================="
    echo "1)  🏥 Health Check Completo"
    echo "2)  🔗 Pruebas End-to-End"
    echo "3)  📱 Probar Flujo de Reservas"
    echo "4)  🧠 Probar NLU"
    echo "5)  📅 Probar iCal"
    echo "6)  🔒 Probar Webhooks"
    echo "7)  📊 Generar Datos de Prueba"
    echo "8)  🔙 Volver al menú principal"
    echo ""
    echo -n "Seleccione una opción [1-8]: "
}

# Submenú de monitoreo
show_monitor_menu() {
    echo -e "${BOLD}📊 ESTADO Y MONITOREO${NC}"
    echo "=================================="
    echo "1)  👁️  Dashboard en Tiempo Real"
    echo "2)  📈 Verificación Única"
    echo "3)  🐳 Estado de Contenedores"
    echo "4)  💾 Estado de Base de Datos"
    echo "5)  📡 Estado de Redis"
    echo "6)  🌐 Probar Conectividad"
    echo "7)  📊 Métricas de Rendimiento"
    echo "8)  🔙 Volver al menú principal"
    echo ""
    echo -n "Seleccione una opción [1-8]: "
}

# Funciones de sistema
start_system() {
    print_status "Iniciando sistema de alojamientos..." "STEP"

    # Crear directorios necesarios
    mkdir -p logs
    mkdir -p data/postgres
    mkdir -p data/redis

    # Levantar servicios
    docker-compose up -d

    print_status "Esperando que los servicios estén listos..." "INFO"
    sleep 10

    if check_system_status >/dev/null 2>&1; then
        print_status "Sistema iniciado exitosamente" "SUCCESS"

        # Mostrar información del sistema
        echo ""
        print_status "URLs disponibles:" "INFO"
        echo "  🌐 API Health: http://localhost/api/v1/healthz"
        echo "  📊 Métricas: http://localhost/metrics"
        echo "  📱 WhatsApp Webhook: http://localhost/api/v1/webhooks/whatsapp"
        echo "  💳 MercadoPago Webhook: http://localhost/api/v1/webhooks/mercadopago"
    else
        print_status "Sistema iniciado pero con problemas - revisar logs" "WARNING"
    fi
}

stop_system() {
    print_status "Deteniendo sistema..." "STEP"
    docker-compose down
    print_status "Sistema detenido" "SUCCESS"
}

restart_system() {
    print_status "Reiniciando sistema..." "STEP"
    stop_system
    sleep 3
    start_system
}

# Configuraciones
configure_ssl() {
    if [ -f "scripts/setup_ssl.sh" ]; then
        print_status "Ejecutando configuración SSL..." "STEP"
        ./scripts/setup_ssl.sh
    else
        print_status "Script de SSL no encontrado" "ERROR"
    fi
}

configure_whatsapp() {
    if [ -f "scripts/configure_whatsapp.py" ]; then
        print_status "Ejecutando configuración WhatsApp..." "STEP"
        python3 scripts/configure_whatsapp.py
    else
        print_status "Script de WhatsApp no encontrado" "ERROR"
    fi
}

configure_ical() {
    if [ -f "scripts/configure_ical.py" ]; then
        print_status "Ejecutando configuración iCal..." "STEP"
        python3 scripts/configure_ical.py
    else
        print_status "Script de iCal no encontrado" "ERROR"
    fi
}

# Pruebas
run_health_check() {
    print_status "Ejecutando health check completo..." "STEP"
    curl -s http://localhost/api/v1/healthz | jq . 2>/dev/null || curl -s http://localhost/api/v1/healthz
}

run_e2e_tests() {
    if [ -f "backend/test_e2e.py" ]; then
        print_status "Ejecutando pruebas end-to-end..." "STEP"
        cd backend && python3 test_e2e.py && cd ..
    else
        print_status "Archivo de pruebas E2E no encontrado" "ERROR"
    fi
}

run_reservation_flow_test() {
    if [ -f "backend/test_reservation_flow.py" ]; then
        print_status "Ejecutando pruebas del flujo de reservas..." "STEP"
        cd backend && python3 test_reservation_flow.py && cd ..
    else
        print_status "Archivo de pruebas de reservas no encontrado" "ERROR"
    fi
}

create_test_data() {
    if [ -f "backend/create_test_data.py" ]; then
        print_status "Generando datos de prueba..." "STEP"
        cd backend && python3 create_test_data.py && cd ..
    else
        print_status "Script de datos de prueba no encontrado" "ERROR"
    fi
}

# Monitoreo
show_dashboard() {
    if [ -f "scripts/monitor_system.py" ]; then
        print_status "Iniciando dashboard de monitoreo..." "STEP"
        python3 scripts/monitor_system.py --monitor
    else
        print_status "Script de monitoreo no encontrado" "ERROR"
    fi
}

show_single_check() {
    if [ -f "scripts/monitor_system.py" ]; then
        python3 scripts/monitor_system.py --check
    else
        print_status "Script de monitoreo no encontrado" "ERROR"
    fi
}

show_docker_status() {
    print_status "Estado de contenedores Docker:" "INFO"
    docker-compose ps

    echo ""
    print_status "Uso de recursos:" "INFO"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

show_logs() {
    echo -e "${BOLD}📋 LOGS DEL SISTEMA${NC}"
    echo "=================================="
    echo "1)  📱 Logs de API"
    echo "2)  🐘 Logs de PostgreSQL"
    echo "3)  📡 Logs de Redis"
    echo "4)  🌐 Logs de Nginx"
    echo "5)  🔙 Volver"
    echo ""
    echo -n "Seleccione una opción [1-5]: "

    read -r log_choice

    case $log_choice in
        1) docker logs alojamientos_api --tail=50 -f ;;
        2) docker logs alojamientos_postgres --tail=50 -f ;;
        3) docker logs alojamientos_redis --tail=50 -f ;;
        4) docker logs alojamientos_nginx --tail=50 -f ;;
        5) return ;;
        *) print_status "Opción inválida" "ERROR" ;;
    esac
}

# Función principal
main() {
    show_banner
    check_project_directory

    while true; do
        echo ""
        show_main_menu
        read -r choice

        case $choice in
            1)
                echo ""
                print_status "GESTIÓN DEL SISTEMA" "HEADER"
                echo "1) Iniciar sistema"
                echo "2) Reiniciar sistema"
                echo "3) Detener sistema"
                echo -n "Seleccione [1-3]: "
                read -r sys_choice

                case $sys_choice in
                    1) start_system ;;
                    2) restart_system ;;
                    3) stop_system ;;
                    *) print_status "Opción inválida" "ERROR" ;;
                esac
                ;;

            2)
                stop_system
                ;;

            3)
                while true; do
                    echo ""
                    show_monitor_menu
                    read -r monitor_choice

                    case $monitor_choice in
                        1) show_dashboard ;;
                        2) show_single_check ;;
                        3) show_docker_status ;;
                        4) run_health_check ;;
                        5) docker exec alojamientos_redis redis-cli ping ;;
                        6) curl -s http://localhost/api/v1/healthz >/dev/null && print_status "Conectividad OK" "SUCCESS" || print_status "Sin conectividad" "ERROR" ;;
                        7) curl -s http://localhost/metrics | head -20 ;;
                        8) break ;;
                        *) print_status "Opción inválida" "ERROR" ;;
                    esac

                    if [ "$monitor_choice" != "1" ]; then
                        echo ""
                        echo "Presione Enter para continuar..."
                        read -r
                    fi
                done
                ;;

            4)
                while true; do
                    echo ""
                    show_config_menu
                    read -r config_choice

                    case $config_choice in
                        1) configure_ssl ;;
                        2) configure_whatsapp ;;
                        3) configure_ical ;;
                        4) print_status "Configuración de MercadoPago pendiente" "INFO" ;;
                        5) print_status "Editor de variables de entorno:" "INFO"; nano .env ;;
                        6) print_status "Editor de Docker Compose:" "INFO"; nano docker-compose.yml ;;
                        7) break ;;
                        *) print_status "Opción inválida" "ERROR" ;;
                    esac

                    echo ""
                    echo "Presione Enter para continuar..."
                    read -r
                done
                ;;

            5)
                while true; do
                    echo ""
                    show_test_menu
                    read -r test_choice

                    case $test_choice in
                        1) run_health_check ;;
                        2) run_e2e_tests ;;
                        3) run_reservation_flow_test ;;
                        4) curl -s -X POST http://localhost/api/v1/nlu/analyze -H "Content-Type: application/json" -d '{"text": "Hola, quiero reservar"}' | jq ;;
                        5) print_status "Prueba de iCal pendiente" "INFO" ;;
                        6) print_status "Prueba de webhooks pendiente" "INFO" ;;
                        7) create_test_data ;;
                        8) break ;;
                        *) print_status "Opción inválida" "ERROR" ;;
                    esac

                    echo ""
                    echo "Presione Enter para continuar..."
                    read -r
                done
                ;;

            6)
                print_status "Funciones de backup pendientes" "INFO"
                ;;

            7)
                show_logs
                ;;

            8)
                echo ""
                print_status "DOCUMENTACIÓN Y AYUDA" "HEADER"
                echo "📖 Documentación disponible:"
                echo "  - README.md: Información general del proyecto"
                echo "  - .github/copilot-instructions.md: Instrucciones técnicas"
                echo "  - backend/: Código fuente de la API"
                echo "  - scripts/: Scripts de configuración y mantenimiento"
                echo ""
                echo "🔗 URLs importantes:"
                echo "  - Health Check: http://localhost/api/v1/healthz"
                echo "  - Métricas: http://localhost/metrics"
                echo "  - API Docs: http://localhost/api/v1/docs (si está habilitado)"
                echo ""
                echo "💬 Para soporte técnico, revisar los logs y el health check"
                ;;

            9)
                print_status "¡Hasta luego!" "SUCCESS"
                exit 0
                ;;

            *)
                print_status "Opción inválida. Por favor seleccione 1-9." "ERROR"
                ;;
        esac
    done
}

# Verificar si se pasaron argumentos de línea de comandos
if [ $# -gt 0 ]; then
    case $1 in
        "start") start_system ;;
        "stop") stop_system ;;
        "restart") restart_system ;;
        "status") check_system_status ;;
        "health") run_health_check ;;
        "test") run_e2e_tests ;;
        "monitor") show_dashboard ;;
        "logs") docker-compose logs -f ;;
        "help"|"--help"|"-h")
            echo "Uso: $0 [comando]"
            echo ""
            echo "Comandos disponibles:"
            echo "  start     Iniciar el sistema"
            echo "  stop      Detener el sistema"
            echo "  restart   Reiniciar el sistema"
            echo "  status    Verificar estado"
            echo "  health    Health check"
            echo "  test      Ejecutar pruebas"
            echo "  monitor   Dashboard de monitoreo"
            echo "  logs      Mostrar logs"
            echo "  help      Mostrar esta ayuda"
            echo ""
            echo "Sin argumentos: Ejecutar menú interactivo"
            ;;
        *)
            print_status "Comando desconocido: $1" "ERROR"
            print_status "Use '$0 help' para ver comandos disponibles" "INFO"
            exit 1
            ;;
    esac
else
    main
fi
