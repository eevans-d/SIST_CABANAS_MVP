#!/bin/bash
# supervisor.sh - Script para supervisar y realizar tareas comunes en el sistema
#
# Este script proporciona una interfaz para realizar tareas comunes de supervisión
# y administración del sistema de alojamientos.

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Función para mostrar el menú principal
show_menu() {
    clear
    echo -e "${BLUE}============================================${NC}"
    echo -e "${YELLOW}   SISTEMA DE ALOJAMIENTOS - SUPERVISOR   ${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo -e "${CYAN}Fecha:${NC} $(date '+%d/%m/%Y %H:%M:%S')"
    echo
    echo -e "${GREEN}1.${NC} Ver estado del sistema"
    echo -e "${GREEN}2.${NC} Gestionar contenedores"
    echo -e "${GREEN}3.${NC} Administrar base de datos"
    echo -e "${GREEN}4.${NC} Administrar Redis"
    echo -e "${GREEN}5.${NC} Gestionar webhooks"
    echo -e "${GREEN}6.${NC} Logs y monitoreo"
    echo -e "${GREEN}7.${NC} Configuración SSL/HTTPS"
    echo -e "${GREEN}8.${NC} Datos de prueba"
    echo -e "${GREEN}9.${NC} Ejecutar pruebas"
    echo -e "${GREEN}0.${NC} Salir"
    echo
    echo -e "${YELLOW}Seleccione una opción:${NC} "
    read -r option
}

# Función para mostrar el estado del sistema
show_status() {
    clear
    echo -e "${BLUE}============================================${NC}"
    echo -e "${YELLOW}           ESTADO DEL SISTEMA             ${NC}"
    echo -e "${BLUE}============================================${NC}"
    
    echo -e "\n${CYAN}Estado de los contenedores:${NC}"
    docker-compose ps
    
    echo -e "\n${CYAN}Health check de la API:${NC}"
    curl -s http://localhost:8000/api/v1/healthz | python3 -m json.tool
    
    echo -e "\n${CYAN}Uso de recursos:${NC}"
    docker stats --no-stream
    
    echo -e "\n${CYAN}Presione Enter para volver al menú principal${NC}"
    read -r
}

# Función para gestionar contenedores
manage_containers() {
    local container_option
    
    while true; do
        clear
        echo -e "${BLUE}============================================${NC}"
        echo -e "${YELLOW}           GESTIÓN DE CONTENEDORES        ${NC}"
        echo -e "${BLUE}============================================${NC}"
        
        echo -e "${GREEN}1.${NC} Ver estado de los contenedores"
        echo -e "${GREEN}2.${NC} Iniciar todos los contenedores"
        echo -e "${GREEN}3.${NC} Detener todos los contenedores"
        echo -e "${GREEN}4.${NC} Reiniciar contenedores"
        echo -e "${GREEN}5.${NC} Reconstruir contenedores (--build)"
        echo -e "${GREEN}6.${NC} Ver logs de un contenedor"
        echo -e "${GREEN}0.${NC} Volver al menú principal"
        
        echo -e "\n${YELLOW}Seleccione una opción:${NC} "
        read -r container_option
        
        case $container_option in
            1)
                echo -e "\n${CYAN}Estado de los contenedores:${NC}"
                docker-compose ps
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            2)
                echo -e "\n${CYAN}Iniciando contenedores...${NC}"
                docker-compose up -d
                echo -e "\n${GREEN}Contenedores iniciados${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            3)
                echo -e "\n${CYAN}Deteniendo contenedores...${NC}"
                docker-compose down
                echo -e "\n${GREEN}Contenedores detenidos${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            4)
                echo -e "\n${CYAN}Reiniciando contenedores...${NC}"
                docker-compose restart
                echo -e "\n${GREEN}Contenedores reiniciados${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            5)
                echo -e "\n${CYAN}Reconstruyendo contenedores...${NC}"
                docker-compose up -d --build
                echo -e "\n${GREEN}Contenedores reconstruidos${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            6)
                echo -e "\n${CYAN}Contenedores disponibles:${NC}"
                docker-compose ps --services
                echo -e "\n${YELLOW}Ingrese el nombre del servicio para ver sus logs:${NC} "
                read -r service
                
                if [ -z "$service" ]; then
                    echo -e "${RED}Nombre de servicio no válido${NC}"
                else
                    echo -e "\n${CYAN}Mostrando logs de $service (Ctrl+C para salir):${NC}"
                    docker-compose logs -f "$service"
                fi
                ;;
            0)
                return
                ;;
            *)
                echo -e "\n${RED}Opción inválida. Presione Enter para continuar.${NC}"
                read -r
                ;;
        esac
    done
}

# Función para administrar la base de datos
manage_database() {
    local db_option
    
    while true; do
        clear
        echo -e "${BLUE}============================================${NC}"
        echo -e "${YELLOW}        ADMINISTRACIÓN DE BASE DE DATOS    ${NC}"
        echo -e "${BLUE}============================================${NC}"
        
        echo -e "${GREEN}1.${NC} Ejecutar migraciones (alembic upgrade head)"
        echo -e "${GREEN}2.${NC} Crear backup de la base de datos"
        echo -e "${GREEN}3.${NC} Restaurar backup de la base de datos"
        echo -e "${GREEN}4.${NC} Ejecutar SQL personalizado"
        echo -e "${GREEN}5.${NC} Ver tablas de la base de datos"
        echo -e "${GREEN}6.${NC} Generar datos de prueba"
        echo -e "${GREEN}0.${NC} Volver al menú principal"
        
        echo -e "\n${YELLOW}Seleccione una opción:${NC} "
        read -r db_option
        
        case $db_option in
            1)
                echo -e "\n${CYAN}Ejecutando migraciones...${NC}"
                docker-compose exec api alembic upgrade head
                echo -e "\n${GREEN}Migraciones ejecutadas${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            2)
                echo -e "\n${CYAN}Creando backup de la base de datos...${NC}"
                BACKUP_FILE="backup_$(date '+%Y%m%d_%H%M%S').sql"
                docker-compose exec -T postgres pg_dump -U alojamientos alojamientos_db > "$BACKUP_FILE"
                echo -e "\n${GREEN}Backup creado: $BACKUP_FILE${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            3)
                echo -e "\n${CYAN}Backups disponibles:${NC}"
                ls -la backup_*.sql 2>/dev/null || echo "No hay backups disponibles"
                
                echo -e "\n${YELLOW}Ingrese el nombre del archivo de backup a restaurar:${NC} "
                read -r backup_file
                
                if [ -f "$backup_file" ]; then
                    echo -e "\n${YELLOW}¡ADVERTENCIA! Esta operación sobrescribirá la base de datos actual.${NC}"
                    echo -e "${YELLOW}¿Está seguro de que desea continuar? (s/n)${NC} "
                    read -r confirm
                    
                    if [ "$confirm" = "s" ]; then
                        echo -e "\n${CYAN}Restaurando backup...${NC}"
                        cat "$backup_file" | docker-compose exec -T postgres psql -U alojamientos alojamientos_db
                        echo -e "\n${GREEN}Backup restaurado${NC}"
                    else
                        echo -e "\n${YELLOW}Operación cancelada${NC}"
                    fi
                else
                    echo -e "\n${RED}Archivo no encontrado${NC}"
                fi
                
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            4)
                echo -e "\n${YELLOW}Ingrese la consulta SQL a ejecutar:${NC} "
                read -r sql_query
                
                if [ -n "$sql_query" ]; then
                    echo -e "\n${CYAN}Ejecutando consulta...${NC}"
                    echo "$sql_query" | docker-compose exec -T postgres psql -U alojamientos alojamientos_db
                else
                    echo -e "\n${RED}Consulta vacía${NC}"
                fi
                
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            5)
                echo -e "\n${CYAN}Tablas de la base de datos:${NC}"
                docker-compose exec postgres psql -U alojamientos -c "\dt" alojamientos_db
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            6)
                echo -e "\n${CYAN}Generando datos de prueba...${NC}"
                docker-compose exec api python create_test_data.py
                echo -e "\n${GREEN}Datos de prueba generados${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            0)
                return
                ;;
            *)
                echo -e "\n${RED}Opción inválida. Presione Enter para continuar.${NC}"
                read -r
                ;;
        esac
    done
}

# Función para administrar Redis
manage_redis() {
    local redis_option
    
    while true; do
        clear
        echo -e "${BLUE}============================================${NC}"
        echo -e "${YELLOW}           ADMINISTRACIÓN DE REDIS         ${NC}"
        echo -e "${BLUE}============================================${NC}"
        
        echo -e "${GREEN}1.${NC} Ver información de Redis (INFO)"
        echo -e "${GREEN}2.${NC} Ver claves activas"
        echo -e "${GREEN}3.${NC} Ver locks de reservas activos"
        echo -e "${GREEN}4.${NC} Limpiar todas las claves (FLUSHALL)"
        echo -e "${GREEN}5.${NC} Monitorear comandos Redis en tiempo real"
        echo -e "${GREEN}6.${NC} Probar conexión a Redis"
        echo -e "${GREEN}0.${NC} Volver al menú principal"
        
        echo -e "\n${YELLOW}Seleccione una opción:${NC} "
        read -r redis_option
        
        case $redis_option in
            1)
                echo -e "\n${CYAN}Información de Redis:${NC}"
                docker-compose exec redis redis-cli -a redispass info | grep -v -e "^#" -e "^$"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            2)
                echo -e "\n${CYAN}Claves activas:${NC}"
                docker-compose exec redis redis-cli -a redispass keys "*"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            3)
                echo -e "\n${CYAN}Locks de reservas activos:${NC}"
                docker-compose exec redis redis-cli -a redispass keys "lock:acc:*"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            4)
                echo -e "\n${YELLOW}¡ADVERTENCIA! Esta operación eliminará todas las claves de Redis.${NC}"
                echo -e "${YELLOW}¿Está seguro de que desea continuar? (s/n)${NC} "
                read -r confirm
                
                if [ "$confirm" = "s" ]; then
                    echo -e "\n${CYAN}Limpiando Redis...${NC}"
                    docker-compose exec redis redis-cli -a redispass flushall
                    echo -e "\n${GREEN}Redis limpiado${NC}"
                else
                    echo -e "\n${YELLOW}Operación cancelada${NC}"
                fi
                
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            5)
                echo -e "\n${CYAN}Monitoreando comandos Redis (Ctrl+C para salir):${NC}"
                docker-compose exec redis redis-cli -a redispass monitor
                ;;
            6)
                echo -e "\n${CYAN}Probando conexión a Redis:${NC}"
                docker-compose exec api python app/test_redis_docker.py
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            0)
                return
                ;;
            *)
                echo -e "\n${RED}Opción inválida. Presione Enter para continuar.${NC}"
                read -r
                ;;
        esac
    done
}

# Función para gestionar webhooks
manage_webhooks() {
    local webhook_option
    
    while true; do
        clear
        echo -e "${BLUE}============================================${NC}"
        echo -e "${YELLOW}           GESTIÓN DE WEBHOOKS            ${NC}"
        echo -e "${BLUE}============================================${NC}"
        
        echo -e "${GREEN}1.${NC} Configurar webhook de WhatsApp"
        echo -e "${GREEN}2.${NC} Configurar webhook de Mercado Pago"
        echo -e "${GREEN}3.${NC} Probar webhook de WhatsApp"
        echo -e "${GREEN}4.${NC} Probar webhook de Mercado Pago"
        echo -e "${GREEN}5.${NC} Ver logs de webhooks recientes"
        echo -e "${GREEN}0.${NC} Volver al menú principal"
        
        echo -e "\n${YELLOW}Seleccione una opción:${NC} "
        read -r webhook_option
        
        case $webhook_option in
            1)
                echo -e "\n${CYAN}Configurando webhook de WhatsApp...${NC}"
                python3 scripts/configure_whatsapp.py
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            2)
                echo -e "\n${CYAN}Configurando webhook de Mercado Pago...${NC}"
                # Este script se implementará en el futuro
                echo -e "${YELLOW}Funcionalidad no implementada aún${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            3)
                echo -e "\n${CYAN}Probando webhook de WhatsApp...${NC}"
                python3 scripts/configure_whatsapp.py --test-message
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            4)
                echo -e "\n${CYAN}Probando webhook de Mercado Pago...${NC}"
                # Este script se implementará en el futuro
                echo -e "${YELLOW}Funcionalidad no implementada aún${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            5)
                echo -e "\n${CYAN}Logs de webhooks recientes:${NC}"
                docker-compose exec api grep -i webhook /app/logs/app.log | tail -n 50
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            0)
                return
                ;;
            *)
                echo -e "\n${RED}Opción inválida. Presione Enter para continuar.${NC}"
                read -r
                ;;
        esac
    done
}

# Función para logs y monitoreo
logs_and_monitoring() {
    local logs_option
    
    while true; do
        clear
        echo -e "${BLUE}============================================${NC}"
        echo -e "${YELLOW}           LOGS Y MONITOREO               ${NC}"
        echo -e "${BLUE}============================================${NC}"
        
        echo -e "${GREEN}1.${NC} Ver logs de la API"
        echo -e "${GREEN}2.${NC} Ver logs de Nginx"
        echo -e "${GREEN}3.${NC} Ver logs de PostgreSQL"
        echo -e "${GREEN}4.${NC} Ver logs de Redis"
        echo -e "${GREEN}5.${NC} Iniciar dashboard de monitoreo"
        echo -e "${GREEN}6.${NC} Ver métricas Prometheus"
        echo -e "${GREEN}0.${NC} Volver al menú principal"
        
        echo -e "\n${YELLOW}Seleccione una opción:${NC} "
        read -r logs_option
        
        case $logs_option in
            1)
                echo -e "\n${CYAN}Logs de la API (Ctrl+C para salir):${NC}"
                docker-compose logs -f api
                ;;
            2)
                echo -e "\n${CYAN}Logs de Nginx (Ctrl+C para salir):${NC}"
                docker-compose logs -f nginx
                ;;
            3)
                echo -e "\n${CYAN}Logs de PostgreSQL (Ctrl+C para salir):${NC}"
                docker-compose logs -f postgres
                ;;
            4)
                echo -e "\n${CYAN}Logs de Redis (Ctrl+C para salir):${NC}"
                docker-compose logs -f redis
                ;;
            5)
                echo -e "\n${CYAN}Iniciando dashboard de monitoreo...${NC}"
                python3 scripts/monitor_system.py &
                echo -e "\n${GREEN}Dashboard iniciado en segundo plano${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            6)
                echo -e "\n${CYAN}Métricas Prometheus:${NC}"
                curl -s http://localhost:8000/metrics
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            0)
                return
                ;;
            *)
                echo -e "\n${RED}Opción inválida. Presione Enter para continuar.${NC}"
                read -r
                ;;
        esac
    done
}

# Función para configuración SSL/HTTPS
manage_ssl() {
    local ssl_option
    
    while true; do
        clear
        echo -e "${BLUE}============================================${NC}"
        echo -e "${YELLOW}        CONFIGURACIÓN SSL/HTTPS            ${NC}"
        echo -e "${BLUE}============================================${NC}"
        
        echo -e "${GREEN}1.${NC} Configurar SSL para desarrollo (auto-firmado)"
        echo -e "${GREEN}2.${NC} Configurar SSL para producción (Let's Encrypt)"
        echo -e "${GREEN}3.${NC} Ver estado de certificados"
        echo -e "${GREEN}4.${NC} Recargar configuración de Nginx"
        echo -e "${GREEN}0.${NC} Volver al menú principal"
        
        echo -e "\n${YELLOW}Seleccione una opción:${NC} "
        read -r ssl_option
        
        case $ssl_option in
            1)
                echo -e "\n${CYAN}Configurando SSL para desarrollo...${NC}"
                bash scripts/setup_ssl.sh dev
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            2)
                echo -e "\n${YELLOW}Ingrese el dominio para el certificado:${NC} "
                read -r domain
                
                if [ -n "$domain" ]; then
                    echo -e "\n${CYAN}Configurando SSL para producción ($domain)...${NC}"
                    bash scripts/setup_ssl.sh prod "$domain"
                else
                    echo -e "\n${RED}Dominio no válido${NC}"
                fi
                
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            3)
                echo -e "\n${CYAN}Estado de certificados:${NC}"
                ls -la nginx/ssl/
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            4)
                echo -e "\n${CYAN}Recargando configuración de Nginx...${NC}"
                docker-compose exec nginx nginx -s reload
                echo -e "\n${GREEN}Configuración recargada${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            0)
                return
                ;;
            *)
                echo -e "\n${RED}Opción inválida. Presione Enter para continuar.${NC}"
                read -r
                ;;
        esac
    done
}

# Función para datos de prueba
manage_test_data() {
    local test_data_option
    
    while true; do
        clear
        echo -e "${BLUE}============================================${NC}"
        echo -e "${YELLOW}           DATOS DE PRUEBA                 ${NC}"
        echo -e "${BLUE}============================================${NC}"
        
        echo -e "${GREEN}1.${NC} Generar datos de prueba básicos"
        echo -e "${GREEN}2.${NC} Generar datos de reservaciones"
        echo -e "${GREEN}3.${NC} Generar datos para iCal"
        echo -e "${GREEN}4.${NC} Limpiar todos los datos"
        echo -e "${GREEN}0.${NC} Volver al menú principal"
        
        echo -e "\n${YELLOW}Seleccione una opción:${NC} "
        read -r test_data_option
        
        case $test_data_option in
            1)
                echo -e "\n${CYAN}Generando datos de prueba básicos...${NC}"
                docker-compose exec api python create_test_data.py --basic
                echo -e "\n${GREEN}Datos generados${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            2)
                echo -e "\n${CYAN}Generando datos de reservaciones...${NC}"
                docker-compose exec api python create_test_data.py --reservations
                echo -e "\n${GREEN}Datos generados${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            3)
                echo -e "\n${CYAN}Generando datos para iCal...${NC}"
                docker-compose exec api python create_test_data.py --ical
                echo -e "\n${GREEN}Datos generados${NC}"
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            4)
                echo -e "\n${YELLOW}¡ADVERTENCIA! Esta operación eliminará todos los datos.${NC}"
                echo -e "${YELLOW}¿Está seguro de que desea continuar? (s/n)${NC} "
                read -r confirm
                
                if [ "$confirm" = "s" ]; then
                    echo -e "\n${CYAN}Limpiando datos...${NC}"
                    docker-compose exec api python create_test_data.py --clean
                    echo -e "\n${GREEN}Datos limpiados${NC}"
                else
                    echo -e "\n${YELLOW}Operación cancelada${NC}"
                fi
                
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            0)
                return
                ;;
            *)
                echo -e "\n${RED}Opción inválida. Presione Enter para continuar.${NC}"
                read -r
                ;;
        esac
    done
}

# Función para ejecutar pruebas
run_tests() {
    local test_option
    
    while true; do
        clear
        echo -e "${BLUE}============================================${NC}"
        echo -e "${YELLOW}           EJECUTAR PRUEBAS                ${NC}"
        echo -e "${BLUE}============================================${NC}"
        
        echo -e "${GREEN}1.${NC} Ejecutar todas las pruebas"
        echo -e "${GREEN}2.${NC} Ejecutar pruebas unitarias"
        echo -e "${GREEN}3.${NC} Ejecutar pruebas de integración"
        echo -e "${GREEN}4.${NC} Ejecutar pruebas de doble-booking"
        echo -e "${GREEN}5.${NC} Ejecutar pruebas end-to-end"
        echo -e "${GREEN}6.${NC} Ejecutar test_reservation_flow.py"
        echo -e "${GREEN}0.${NC} Volver al menú principal"
        
        echo -e "\n${YELLOW}Seleccione una opción:${NC} "
        read -r test_option
        
        case $test_option in
            1)
                echo -e "\n${CYAN}Ejecutando todas las pruebas...${NC}"
                docker-compose exec api pytest
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            2)
                echo -e "\n${CYAN}Ejecutando pruebas unitarias...${NC}"
                docker-compose exec api pytest tests/unit
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            3)
                echo -e "\n${CYAN}Ejecutando pruebas de integración...${NC}"
                docker-compose exec api pytest tests/integration
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            4)
                echo -e "\n${CYAN}Ejecutando pruebas de doble-booking...${NC}"
                docker-compose exec api pytest tests/test_double_booking.py -v
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            5)
                echo -e "\n${CYAN}Ejecutando pruebas end-to-end...${NC}"
                docker-compose exec api python test_e2e.py
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            6)
                echo -e "\n${CYAN}Ejecutando test_reservation_flow.py...${NC}"
                docker-compose exec api python test_reservation_flow.py
                echo -e "\n${CYAN}Presione Enter para continuar${NC}"
                read -r
                ;;
            0)
                return
                ;;
            *)
                echo -e "\n${RED}Opción inválida. Presione Enter para continuar.${NC}"
                read -r
                ;;
        esac
    done
}

# Función principal
main() {
    local option
    
    while true; do
        show_menu
        
        case $option in
            1)
                show_status
                ;;
            2)
                manage_containers
                ;;
            3)
                manage_database
                ;;
            4)
                manage_redis
                ;;
            5)
                manage_webhooks
                ;;
            6)
                logs_and_monitoring
                ;;
            7)
                manage_ssl
                ;;
            8)
                manage_test_data
                ;;
            9)
                run_tests
                ;;
            0)
                echo -e "\n${GREEN}¡Hasta luego!${NC}"
                exit 0
                ;;
            *)
                echo -e "\n${RED}Opción inválida. Presione Enter para continuar.${NC}"
                read -r
                ;;
        esac
    done
}

# Ejecutar función principal
main