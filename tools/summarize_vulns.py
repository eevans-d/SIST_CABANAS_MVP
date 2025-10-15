#!/usr/bin/env python3
"""
tools/summarize_vulns.py - Vulnerability Report Summarizer

Analiza los reportes JSON de seguridad generados por audit.sh y produce
un resumen ejecutivo consolidado en formato Markdown.

Uso:
    python3 tools/summarize_vulns.py <reports_dir>

Ejemplo:
    python3 tools/summarize_vulns.py reports/
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def load_json_report(filepath: Path) -> Dict[str, Any]:
    """Carga un reporte JSON de forma segura."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"⚠️  Error loading {filepath}: {e}", file=sys.stderr)
        return {}


def summarize_pip_audit(data: Dict[str, Any]) -> Dict[str, Any]:
    """Procesa reporte de pip-audit."""
    vulns = data.get("vulnerabilities", [])

    by_severity = defaultdict(list)
    by_package = defaultdict(int)

    for vuln in vulns:
        name = vuln.get("name", "Unknown")
        severity = vuln.get("severity", "UNKNOWN")
        cve_id = vuln.get("id", "No CVE")

        by_severity[severity].append(
            {
                "package": name,
                "cve": cve_id,
                "version": vuln.get("version", "?"),
                "fix": vuln.get("fix_versions", ["N/A"])[0] if vuln.get("fix_versions") else "N/A",
            }
        )
        by_package[name] += 1

    return {
        "total": len(vulns),
        "by_severity": dict(by_severity),
        "by_package": dict(by_package),
        "critical_count": len(by_severity.get("CRITICAL", [])),
        "high_count": len(by_severity.get("HIGH", [])),
        "medium_count": len(by_severity.get("MEDIUM", [])),
    }


def summarize_safety(data: Dict[str, Any]) -> Dict[str, Any]:
    """Procesa reporte de safety."""
    vulns = data.get("vulnerabilities", [])

    by_package = defaultdict(list)

    for vuln in vulns:
        pkg = vuln.get("package_name", "Unknown")
        by_package[pkg].append(
            {
                "cve": vuln.get("vulnerability_id", "No CVE"),
                "severity": vuln.get("severity", "UNKNOWN"),
                "affected": vuln.get("analyzed_version", "?"),
            }
        )

    return {
        "total": len(vulns),
        "affected_packages": len(by_package),
        "by_package": dict(by_package),
    }


def summarize_trivy(data: Dict[str, Any]) -> Dict[str, Any]:
    """Procesa reporte de trivy."""
    results = data.get("Results", [])

    total_vulns = 0
    by_severity = defaultdict(int)
    by_target = defaultdict(int)

    for result in results:
        target = result.get("Target", "Unknown")
        vulns = result.get("Vulnerabilities", [])

        if not vulns:
            continue

        by_target[target] = len(vulns)
        total_vulns += len(vulns)

        for vuln in vulns:
            severity = vuln.get("Severity", "UNKNOWN")
            by_severity[severity] += 1

    return {
        "total": total_vulns,
        "by_severity": dict(by_severity),
        "by_target": dict(by_target),
        "critical_count": by_severity.get("CRITICAL", 0),
        "high_count": by_severity.get("HIGH", 0),
    }


def summarize_gitleaks(data: Dict[str, Any]) -> Dict[str, Any]:
    """Procesa reporte de gitleaks."""
    # Gitleaks puede ser lista o dict con 'findings'
    if isinstance(data, list):
        findings = data
    else:
        findings = data.get("findings", data.get("results", []))

    by_rule = defaultdict(int)
    files_affected = set()

    for finding in findings:
        rule = finding.get("RuleID", finding.get("rule", "Unknown"))
        file = finding.get("File", finding.get("file", "Unknown"))

        by_rule[rule] += 1
        files_affected.add(file)

    return {
        "total": len(findings),
        "by_rule": dict(by_rule),
        "files_affected": len(files_affected),
        "files_list": sorted(list(files_affected))[:10],  # Top 10
    }


def generate_markdown_report(reports_dir: Path, summaries: Dict[str, Dict]) -> str:
    """Genera reporte consolidado en Markdown."""

    md = f"""# 🔒 Reporte de Seguridad Consolidado

**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Fuente:** {reports_dir}

---

## 📊 Resumen Ejecutivo

"""

    # Vulnerabilities overview
    total_vulns = 0
    critical_vulns = 0
    high_vulns = 0

    if "pip_audit" in summaries:
        pa = summaries["pip_audit"]
        total_vulns += pa["total"]
        critical_vulns += pa["critical_count"]
        high_vulns += pa["high_count"]

    if "trivy" in summaries:
        tv = summaries["trivy"]
        total_vulns += tv["total"]
        critical_vulns += tv["critical_count"]
        high_vulns += tv["high_count"]

    # Status determination
    if critical_vulns > 0:
        status = "🔴 CRÍTICO"
    elif high_vulns > 0:
        status = "🟠 ALTO"
    elif total_vulns > 0:
        status = "🟡 MEDIO"
    else:
        status = "🟢 BUENO"

    md += f"""| Métrica | Valor |
|---------|-------|
| **Estado General** | {status} |
| **Vulnerabilidades Totales** | {total_vulns} |
| **Críticas** | {critical_vulns} |
| **Altas** | {high_vulns} |
| **Secretos Expuestos** | {summaries.get('gitleaks', {}).get('total', 0)} |

"""

    # Pip-audit details
    if "pip_audit" in summaries:
        pa = summaries["pip_audit"]
        md += f"""## 📦 Dependencias Python (pip-audit)

**Total vulnerabilidades:** {pa['total']}

### Por Severidad
"""
        for severity, vulns in pa["by_severity"].items():
            md += f"- **{severity}:** {len(vulns)}\n"

        if pa["critical_count"] > 0 or pa["high_count"] > 0:
            md += "\n### ⚠️  Vulnerabilidades Críticas/Altas\n\n"
            md += "| Paquete | CVE | Versión Actual | Fix Disponible |\n"
            md += "|---------|-----|----------------|----------------|\n"

            for vuln in pa["by_severity"].get("CRITICAL", [])[:10]:
                md += f"| {vuln['package']} | {vuln['cve']} | {vuln['version']} | {vuln['fix']} |\n"

            for vuln in pa["by_severity"].get("HIGH", [])[:10]:
                md += f"| {vuln['package']} | {vuln['cve']} | {vuln['version']} | {vuln['fix']} |\n"

        md += "\n"

    # Trivy details
    if "trivy" in summaries:
        tv = summaries["trivy"]
        md += f"""## 🐳 Análisis Filesystem/Container (Trivy)

**Total vulnerabilidades:** {tv['total']}

### Por Severidad
"""
        for severity, count in tv["by_severity"].items():
            md += f"- **{severity}:** {count}\n"

        md += "\n### Por Target\n"
        for target, count in list(tv["by_target"].items())[:5]:
            md += f"- `{target}`: {count} vulnerabilidades\n"

        md += "\n"

    # Gitleaks details
    if "gitleaks" in summaries:
        gl = summaries["gitleaks"]
        md += f"""## 🔑 Secrets Scanning (Gitleaks)

**Total secretos encontrados:** {gl['total']}
**Archivos afectados:** {gl['files_affected']}

"""
        if gl["total"] > 0:
            md += "### ⚠️  ACCIÓN REQUERIDA\n\n"
            md += "Se encontraron posibles secretos en el código. Revisar inmediatamente:\n\n"

            md += "| Tipo de Secreto | Ocurrencias |\n"
            md += "|-----------------|-------------|\n"
            for rule, count in sorted(gl["by_rule"].items(), key=lambda x: x[1], reverse=True):
                md += f"| {rule} | {count} |\n"

            md += "\n**Archivos afectados (Top 10):**\n"
            for file in gl["files_list"]:
                md += f"- `{file}`\n"
        else:
            md += "✅ No se encontraron secretos hardcodeados.\n"

        md += "\n"

    # Safety details
    if "safety" in summaries:
        sf = summaries["safety"]
        md += f"""## 🛡️  Safety Check

**Total vulnerabilidades:** {sf['total']}
**Paquetes afectados:** {sf['affected_packages']}

"""
        if sf["total"] > 0:
            md += "### Paquetes Afectados\n\n"
            for pkg, vulns in list(sf["by_package"].items())[:10]:
                md += f"- **{pkg}:** {len(vulns)} vulnerabilidades\n"

        md += "\n"

    # Recommendations
    md += """---

## 🚀 Recomendaciones

### Acción Inmediata (24h)
"""

    if critical_vulns > 0:
        md += f"1. **Actualizar {critical_vulns} dependencias críticas** listadas arriba\n"
        md += "2. Ejecutar tests completos después de actualizar\n"

    if summaries.get("gitleaks", {}).get("total", 0) > 0:
        md += "3. **Rotar secretos expuestos** identificados por Gitleaks\n"
        md += "4. Remover secretos del historial de git si es necesario\n"

    md += """
### Esta Semana
1. Configurar renovate/dependabot para actualizaciones automáticas
2. Añadir pre-commit hooks con secrets scanning
3. Ejecutar auditoría completa en CI/CD

### Este Mes
1. Implementar SBOM (Software Bill of Materials)
2. Configurar alertas de seguridad automáticas
3. Documentar política de actualizaciones de dependencias

---

## 📎 Archivos Analizados

"""

    # List analyzed files
    for filepath in sorted(reports_dir.glob("audit_*")):
        size = filepath.stat().st_size / 1024  # KB
        md += f"- `{filepath.name}` ({size:.1f} KB)\n"

    md += f"""
---

**Reporte generado por:** `tools/summarize_vulns.py`
**Próxima auditoría:** {(datetime.now()).strftime('%Y-%m-%d')} (recomendado: semanal)
"""

    return md


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 tools/summarize_vulns.py <reports_dir>")
        sys.exit(1)

    reports_dir = Path(sys.argv[1])

    if not reports_dir.exists():
        print(f"❌ Directorio no encontrado: {reports_dir}")
        sys.exit(1)

    print(f"🔍 Analizando reportes en: {reports_dir}")
    print("")

    summaries = {}

    # Find latest audit timestamp
    audit_files = list(reports_dir.glob("audit_*"))
    if not audit_files:
        print("❌ No se encontraron reportes de auditoría")
        sys.exit(1)

    # Get the most recent timestamp
    timestamps = set()
    for f in audit_files:
        parts = f.stem.split("_")
        if len(parts) >= 3:
            timestamps.add(f"{parts[1]}_{parts[2]}")

    if not timestamps:
        print("❌ No se pudo determinar timestamp de auditoría")
        sys.exit(1)

    latest_ts = sorted(timestamps)[-1]
    print(f"📅 Última auditoría: {latest_ts}")
    print("")

    # Process each report type
    print("📊 Procesando reportes...")

    # pip-audit
    pip_audit_file = reports_dir / f"audit_{latest_ts}_pip_audit.json"
    if pip_audit_file.exists():
        data = load_json_report(pip_audit_file)
        if data:
            summaries["pip_audit"] = summarize_pip_audit(data)
            print(f"  ✓ pip-audit: {summaries['pip_audit']['total']} vulnerabilidades")

    # safety
    safety_file = reports_dir / f"audit_{latest_ts}_safety.json"
    if safety_file.exists():
        data = load_json_report(safety_file)
        if data:
            summaries["safety"] = summarize_safety(data)
            print(f"  ✓ safety: {summaries['safety']['total']} vulnerabilidades")

    # trivy
    trivy_file = reports_dir / f"audit_{latest_ts}_trivy_fs.json"
    if trivy_file.exists():
        data = load_json_report(trivy_file)
        if data:
            summaries["trivy"] = summarize_trivy(data)
            print(f"  ✓ trivy: {summaries['trivy']['total']} vulnerabilidades")

    # gitleaks
    gitleaks_file = reports_dir / f"audit_{latest_ts}_gitleaks.json"
    if gitleaks_file.exists():
        data = load_json_report(gitleaks_file)
        if data:
            summaries["gitleaks"] = summarize_gitleaks(data)
            print(f"  ✓ gitleaks: {summaries['gitleaks']['total']} secretos")

    print("")

    if not summaries:
        print("⚠️  No se encontraron reportes JSON válidos")
        sys.exit(0)

    # Generate markdown report
    print("📝 Generando reporte consolidado...")
    markdown = generate_markdown_report(reports_dir, summaries)

    output_file = reports_dir / f"audit_{latest_ts}_CONSOLIDATED_REPORT.md"
    with open(output_file, "w") as f:
        f.write(markdown)

    print(f"✅ Reporte generado: {output_file}")
    print("")
    print("=" * 60)
    print("RESUMEN RÁPIDO:")
    print("=" * 60)

    total_issues = sum(s.get("total", 0) for s in summaries.values())
    critical_issues = sum(s.get("critical_count", 0) for s in summaries.values())

    if critical_issues > 0:
        print(f"🔴 CRÍTICO: {critical_issues} vulnerabilidades críticas encontradas")
    elif total_issues > 0:
        print(f"🟡 {total_issues} issues de seguridad encontrados")
    else:
        print("🟢 No se encontraron vulnerabilidades")

    print("")
    print(f"👉 Revisar reporte completo: {output_file}")


if __name__ == "__main__":
    main()
