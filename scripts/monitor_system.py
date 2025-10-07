#!/usr/bin/env python3
"""
Dashboard de Monitoreo del Sistema de Alojamientos
Proporciona una vista en tiempo real del estado del sistema
"""

import os
import sys
import requests
import json
import time
from datetime import datetime, timedelta
import threading

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SystemMonitor:
    def __init__(self, base_url="http://localhost"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.running = True
        self.last_health = {}
        self.metrics = {}
        
    def clear_screen(self):
        """Limpiar pantalla"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_health_status(self):
        """Obtener estado de salud del sistema"""
        try:
            response = requests.get(f"{self.api_url}/healthz", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "error", "detail": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}
    
    def get_metrics(self):
        """Obtener métricas de Prometheus"""
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=5)
            if response.status_code == 200:
                return self.parse_prometheus_metrics(response.text)
            else:
                return {}
        except Exception as e:
            return {}
    
    def parse_prometheus_metrics(self, metrics_text):
        """Parsear métricas de Prometheus"""
        metrics = {}
        for line in metrics_text.split('\n'):
            if line.startswith('#') or not line.strip():
                continue
            
            if ' ' in line:
                metric_name, value = line.split(' ', 1)
                try:
                    metrics[metric_name] = float(value)
                except ValueError:
                    metrics[metric_name] = value
        
        return metrics
    
    def format_status(self, status):
        """Formatear estado con colores"""
        status_colors = {
            "ok": Colors.GREEN + "✅ OK",
            "healthy": Colors.GREEN + "✅ HEALTHY", 
            "warning": Colors.YELLOW + "⚠️  WARNING",
            "degraded": Colors.YELLOW + "⚠️  DEGRADED",
            "error": Colors.RED + "❌ ERROR",
            "critical": Colors.RED + "🔥 CRITICAL"
        }
        return status_colors.get(status.lower(), Colors.BLUE + "❓ " + status.upper()) + Colors.END
    
    def format_uptime(self, seconds):
        """Formatear tiempo de actividad"""
        if seconds is None:
            return "Unknown"
        
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def format_bytes(self, bytes_val):
        """Formatear bytes en formato legible"""
        if bytes_val is None:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f}TB"
    
    def display_header(self):
        """Mostrar cabecera del dashboard"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"{Colors.BOLD}{Colors.CYAN}🏠 SISTEMA DE ALOJAMIENTOS - DASHBOARD{Colors.END}")
        print("=" * 60)
        print(f"🕒 Última actualización: {now}")
        print(f"🌐 URL Base: {self.base_url}")
        print("=" * 60)
    
    def display_health_status(self, health_data):
        """Mostrar estado de salud del sistema"""
        print(f"\n{Colors.BOLD}📊 ESTADO DEL SISTEMA{Colors.END}")
        print("-" * 40)
        
        overall_status = health_data.get("status", "unknown")
        print(f"Estado General: {self.format_status(overall_status)}")
        
        if "timestamp" in health_data:
            timestamp = health_data["timestamp"]
            print(f"Última verificación: {timestamp}")
        
        # Mostrar checks individuales
        checks = health_data.get("checks", {})
        
        for check_name, check_data in checks.items():
            if isinstance(check_data, dict):
                status = check_data.get("status", "unknown")
                detail = check_data.get("detail", "")
                
                print(f"  {check_name.title()}: {self.format_status(status)}")
                
                # Información adicional específica
                if check_name == "database" and "latency_ms" in check_data:
                    latency = check_data["latency_ms"]
                    print(f"    └─ Latencia: {latency}ms")
                
                elif check_name == "redis" and "used_memory_human" in check_data:
                    memory = check_data["used_memory_human"]
                    clients = check_data.get("connected_clients", 0)
                    print(f"    └─ Memoria: {memory}, Clientes: {clients}")
                
                elif check_name == "disk" and "free_percent" in check_data:
                    free_percent = check_data["free_percent"]
                    print(f"    └─ Espacio libre: {free_percent:.1f}%")
                
                elif check_name == "ical" and "age_minutes" in check_data:
                    age = check_data["age_minutes"]
                    if age is not None:
                        print(f"    └─ Última sync: {age:.0f} min atrás")
                    else:
                        print(f"    └─ {detail}")
                
                elif check_name == "runtime" and "gunicorn_workers" in check_data:
                    workers = check_data["gunicorn_workers"]
                    pool_size = check_data.get("db_pool_size", 0)
                    print(f"    └─ Workers: {workers}, Pool DB: {pool_size}")
                
                elif detail:
                    print(f"    └─ {detail}")
    
    def display_metrics(self, metrics):
        """Mostrar métricas de rendimiento"""
        if not metrics:
            return
        
        print(f"\n{Colors.BOLD}📈 MÉTRICAS DE RENDIMIENTO{Colors.END}")
        print("-" * 40)
        
        # Métricas HTTP
        http_requests = metrics.get("http_requests_total", 0)
        http_duration = metrics.get("http_request_duration_seconds_sum", 0)
        
        if http_requests > 0:
            avg_duration = (http_duration / http_requests) * 1000
            print(f"HTTP Requests: {int(http_requests)} total")
            print(f"Duración promedio: {avg_duration:.1f}ms")
        
        # Métricas de aplicación
        active_connections = metrics.get("active_connections", 0)
        if active_connections:
            print(f"Conexiones activas: {int(active_connections)}")
        
        # Uptime
        uptime = metrics.get("process_start_time_seconds")
        if uptime:
            current_time = time.time()
            uptime_seconds = current_time - uptime
            print(f"Uptime: {self.format_uptime(uptime_seconds)}")
        
        # Memoria del proceso
        memory_bytes = metrics.get("process_resident_memory_bytes")
        if memory_bytes:
            print(f"Memoria: {self.format_bytes(memory_bytes)}")
    
    def display_reservations_summary(self):
        """Mostrar resumen de reservas (simulado)"""
        print(f"\n{Colors.BOLD}🏠 RESUMEN DE RESERVAS{Colors.END}")
        print("-" * 40)
        
        # En un sistema real, esto vendría de la API
        try:
            # Simular datos de reservas
            print("📅 Hoy:")
            print("  └─ Check-ins: 2")
            print("  └─ Check-outs: 1")
            print("  └─ Pre-reservas activas: 3")
            
            print("📊 Esta semana:")
            print("  └─ Ocupación: 85%")
            print("  └─ Reservas nuevas: 12")
            print("  └─ Cancelaciones: 1")
            
        except Exception as e:
            print(f"Error obteniendo datos de reservas: {str(e)}")
    
    def display_alerts(self, health_data):
        """Mostrar alertas del sistema"""
        alerts = []
        
        # Verificar alertas basadas en health data
        checks = health_data.get("checks", {})
        
        for check_name, check_data in checks.items():
            if isinstance(check_data, dict):
                status = check_data.get("status", "ok")
                
                if status in ["error", "critical"]:
                    alerts.append(f"🔥 {check_name.title()}: {check_data.get('detail', 'Error crítico')}")
                elif status == "warning":
                    alerts.append(f"⚠️  {check_name.title()}: {check_data.get('detail', 'Advertencia')}")
        
        # Verificar alertas adicionales
        if health_data.get("status") == "degraded":
            ical_check = checks.get("ical", {})
            if ical_check.get("status") == "warning":
                alerts.append("⚠️  iCal: Sincronización requerida")
        
        if alerts:
            print(f"\n{Colors.BOLD}🚨 ALERTAS{Colors.END}")
            print("-" * 40)
            for alert in alerts:
                print(f"  {alert}")
        else:
            print(f"\n{Colors.GREEN}✅ Sin alertas activas{Colors.END}")
    
    def display_footer(self):
        """Mostrar pie del dashboard"""
        print("\n" + "=" * 60)
        print(f"{Colors.BLUE}💡 Comandos: [q]uit, [r]efresh, [h]elp{Colors.END}")
        print("Actualización automática cada 30 segundos...")
    
    def run_monitor(self):
        """Ejecutar monitor en tiempo real"""
        try:
            while self.running:
                self.clear_screen()
                
                # Obtener datos
                health_data = self.get_health_status()
                metrics_data = self.get_metrics()
                
                # Mostrar dashboard
                self.display_header()
                self.display_health_status(health_data)
                self.display_metrics(metrics_data)
                self.display_reservations_summary()
                self.display_alerts(health_data)
                self.display_footer()
                
                # Actualizar cada 30 segundos
                time.sleep(30)
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}🛑 Monitor detenido por el usuario{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}❌ Error en monitor: {str(e)}{Colors.END}")
    
    def run_single_check(self):
        """Ejecutar una sola verificación"""
        self.clear_screen()
        
        health_data = self.get_health_status()
        metrics_data = self.get_metrics()
        
        self.display_header()
        self.display_health_status(health_data)
        self.display_metrics(metrics_data)
        self.display_reservations_summary()
        self.display_alerts(health_data)
        
        print(f"\n{Colors.GREEN}✅ Verificación completada{Colors.END}")

def show_help():
    """Mostrar ayuda"""
    print(f"{Colors.BOLD}📖 AYUDA - Sistema de Monitoreo{Colors.END}")
    print("=" * 40)
    print("Uso: python3 monitor_system.py [opción]")
    print("")
    print("Opciones:")
    print("  --monitor, -m    Monitoreo en tiempo real (por defecto)")
    print("  --check, -c      Verificación única")
    print("  --url URL        URL base del sistema (default: http://localhost)")
    print("  --help, -h       Mostrar esta ayuda")
    print("")
    print("Ejemplos:")
    print("  python3 monitor_system.py")
    print("  python3 monitor_system.py --check")
    print("  python3 monitor_system.py --url https://mi-sitio.com")

def main():
    """Función principal"""
    
    # Parsear argumentos simples
    args = sys.argv[1:]
    base_url = "http://localhost"
    mode = "monitor"
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg in ["--help", "-h"]:
            show_help()
            return
        elif arg in ["--monitor", "-m"]:
            mode = "monitor"
        elif arg in ["--check", "-c"]:
            mode = "check"
        elif arg in ["--url"]:
            if i + 1 < len(args):
                base_url = args[i + 1]
                i += 1
            else:
                print("Error: --url requiere un valor")
                return
        else:
            print(f"Opción desconocida: {arg}")
            show_help()
            return
        
        i += 1
    
    # Crear monitor
    monitor = SystemMonitor(base_url)
    
    # Ejecutar según modo
    if mode == "monitor":
        print(f"{Colors.BLUE}🚀 Iniciando monitor en tiempo real...{Colors.END}")
        print(f"{Colors.YELLOW}Presione Ctrl+C para detener{Colors.END}")
        time.sleep(2)
        monitor.run_monitor()
    else:
        monitor.run_single_check()

if __name__ == "__main__":
    main()