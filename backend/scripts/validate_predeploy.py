#!/usr/bin/env python3
"""Pre-Deploy Validation Script.

Valida configuración del MVP sin depender de Fly CLI o servicios externos.
Detecta gaps de config, requirements, Dockerfile, variables de entorno.

Uso:
    python scripts/validate_predeploy.py [--env-file .env]

Salida:
    - Report JSON en stdout
    - Exit code: 0 (success) o 1 (fail)
"""
# flake8: noqa
# pylint: disable=all
# bandit: nosec

import argparse
import json
import re
import sys
import tomllib  # Python 3.11+
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


class PreDeployValidator:
    """Valida readiness de deploy."""

    def __init__(self, repo_root: Path):
        """Initialize validator with repo root."""
        self.repo_root = repo_root

        self.results = {
            "timestamp": None,
            "status": "unknown",
            "checks": {},
            "warnings": [],
            "errors": [],
            "summary": {},
        }
        self.results["timestamp"] = (
            datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )

    def run_all_checks(self) -> int:
        """Ejecuta todas las validaciones."""
        checks = [
            ("fly_toml", self.check_fly_toml),
            ("dockerfile", self.check_dockerfile),
            ("requirements", self.check_requirements),
            ("env_vars", self.check_env_vars),
            ("alembic", self.check_alembic),
            ("backend_structure", self.check_backend_structure),
            ("github_workflows", self.check_github_workflows),
        ]

        for check_name, check_func in checks:
            try:
                self.results["checks"][check_name] = check_func()
            except Exception as e:
                self.results["errors"].append(f"Check '{check_name}' failed: {str(e)}")
                self.results["checks"][check_name] = {"status": "error", "error": str(e)}

        # Calcular estado global
        self.results["status"] = "pass" if not self.results["errors"] else "fail"
        self.results["summary"] = self._summarize()

        return 0 if self.results["status"] == "pass" else 1

    def check_fly_toml(self) -> Dict:
        """Valida fly.toml."""
        fly_toml = self.repo_root / "fly.toml"
        if not fly_toml.exists():
            return {"status": "fail", "message": "fly.toml not found"}

        try:
            with open(fly_toml, "rb") as f:
                config = tomllib.load(f)
        except Exception as e:
            return {"status": "fail", "message": "TOML parse error: {e}".replace("{e}", str(e))}

        checks = []

        # Verificar campos críticos
        required_fields = ["app", "primary_region", "build", "env", "http_service"]
        for field in required_fields:
            if field not in config:
                checks.append({"name": field, "status": "fail", "message": f"Missing: {field}"})
            else:
                checks.append({"name": field, "status": "pass", "message": f"Present"})

        # Verificar env vars en fly.toml
        env_keys = config.get("env", {})
        critical_env = [
            "ENVIRONMENT",
            "PORT",
            "RATE_LIMIT_ENABLED",
            "JOB_EXPIRATION_INTERVAL_SECONDS",
            "JOB_ICAL_INTERVAL_SECONDS",
        ]
        for key in critical_env:
            if key not in env_keys:
                self.results["warnings"].append(
                    f"fly.toml: missing env var {key} (non-critical if in secrets)"
                )

        # Verificar health check
        http_service = config.get("http_service", {})
        checks_list = http_service.get("checks", [])
        if not checks_list:
            checks.append(
                {
                    "name": "http_service.checks",
                    "status": "fail",
                    "message": "No health checks defined",
                }
            )
        else:
            checks.append(
                {
                    "name": "http_service.checks",
                    "status": "pass",
                    "message": f"{len(checks_list)} health check(s)",
                }
            )

        status = "pass" if all(c["status"] == "pass" for c in checks) else "fail"
        return {"status": status, "details": checks}

    def check_dockerfile(self) -> Dict:
        """Valida backend/Dockerfile."""
        dockerfile = self.repo_root / "backend" / "Dockerfile"
        if not dockerfile.exists():
            return {"status": "fail", "message": "backend/Dockerfile not found"}

        content = dockerfile.read_text()
        checks = []

        # Validaciones básicas
        validations = [
            ("FROM python", "Base image defined"),
            ("RUN pip install", "Pip install present"),
            ("EXPOSE", "Port exposed"),
            ("CMD", "Entry point defined"),
        ]

        for pattern, description in validations:
            present = pattern in content
            checks.append(
                {
                    "name": description,
                    "status": "pass" if present else "fail",
                    "message": description,
                }
            )

        # Check ffmpeg (para audio processing)
        ffmpeg_present = "ffmpeg" in content.lower()
        if not ffmpeg_present:
            self.results["warnings"].append("ffmpeg not in Dockerfile (needed for audio)")

        status = "pass" if all(c["status"] == "pass" for c in checks) else "fail"
        return {"status": status, "details": checks}

    def check_requirements(self) -> Dict:
        """Valida backend/requirements.txt."""
        req_file = self.repo_root / "backend" / "requirements.txt"
        if not req_file.exists():
            return {"status": "fail", "message": "backend/requirements.txt not found"}

        content = req_file.read_text()
        checks = []

        # Paquetes críticos
        critical_packages = [
            "fastapi",
            "sqlalchemy",
            "asyncpg",
            "alembic",
            "pydantic",
            "redis",
            "httpx",
        ]

        for pkg in critical_packages:
            present = pkg.lower() in content.lower()
            checks.append(
                {
                    "name": pkg,
                    "status": "pass" if present else "fail",
                    "message": f"{pkg} in requirements",
                }
            )

        # Validar que NO usa >= versiones flexibles (debe ser fijas)
        flexible_versions = re.findall(
            r"^([a-z-]+)>=", content, re.MULTILINE | re.IGNORECASE
        )
        if flexible_versions:
            msg = (
                f"Flexible versions (>=): {', '.join(flexible_versions)} - "
                "Use fixed versions for production"
            )
            self.results["warnings"].append(msg)

        status = "pass" if all(c["status"] == "pass" for c in checks) else "fail"
        return {"status": status, "details": checks}

    def check_env_vars(self) -> Dict:
        """Valida variables de entorno definidas/documentadas."""
        env_template = self.repo_root / "env" / ".env.template"
        env_example = self.repo_root / "env" / ".env.example"

        checks = []

        if env_template.exists():
            checks.append({"name": "env/.env.template", "status": "pass", "message": "Found"})
        else:
            checks.append({"name": "env/.env.template", "status": "fail", "message": "Missing"})

        if env_example.exists():
            checks.append({"name": "env/.env.example", "status": "pass", "message": "Found"})
        else:
            checks.append({"name": "env/.env.example", "status": "fail", "message": "Missing"})

        # Validar que .env NO está en git (si existe)
        gitignore = self.repo_root / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            if ".env" not in content:
                self.results["warnings"].append(".env not in .gitignore (security risk)")
            else:
                checks.append(
                    {
                        "name": ".gitignore includes .env",
                        "status": "pass",
                        "message": "Secrets protected",
                    }
                )

        status = "pass" if any(c["status"] == "pass" for c in checks) else "fail"
        return {"status": status, "details": checks}

    def check_alembic(self) -> Dict:
        """Valida Alembic migrations."""
        alembic_dir = self.repo_root / "backend" / "alembic"
        if not alembic_dir.exists():
            return {
                "status": "fail",
                "message": "alembic/ directory not found",
            }

        checks = []

        # Verificar presencia de env.py
        env_py = alembic_dir / "env.py"
        checks.append(
            {
                "name": "alembic/env.py",
                "status": "pass" if env_py.exists() else "fail",
                "message": "Alembic environment",
            }
        )

        # Verificar presencia de versions/
        versions_dir = alembic_dir / "versions"
        if versions_dir.exists():
            migrations = list(versions_dir.glob("*.py"))
            checks.append(
                {
                    "name": "migrations",
                    "status": "pass",
                    "message": f"{len(migrations)} migration file(s)",
                }
            )
        else:
            checks.append(
                {
                    "name": "migrations",
                    "status": "fail",
                    "message": "No versions/ directory",
                }
            )

        status = "pass" if all(c["status"] == "pass" for c in checks) else "fail"
        return {"status": status, "details": checks}

    def check_backend_structure(self) -> Dict:
        """Valida estructura de backend/app."""
        backend_dir = self.repo_root / "backend" / "app"
        if not backend_dir.exists():
            return {"status": "fail", "message": "backend/app/ not found"}

        checks = []

        required_modules = [
            "main.py",
            "core/config.py",
            "core/database.py",
            "models/__init__.py",
            "routers/__init__.py",
        ]

        for module in required_modules:
            path = backend_dir / module
            checks.append(
                {
                    "name": module,
                    "status": "pass" if path.exists() else "fail",
                    "message": f"app/{module}",
                }
            )

        status = "pass" if all(c["status"] == "pass" for c in checks) else "fail"
        return {"status": status, "details": checks}

    def check_github_workflows(self) -> Dict:
        """Valida GitHub Actions workflows."""
        workflows_dir = self.repo_root / ".github" / "workflows"
        if not workflows_dir.exists():
            return {"status": "fail", "message": ".github/workflows/ not found"}

        checks = []

        critical_workflows = ["ci.yml", "deploy-fly.yml"]
        for workflow in critical_workflows:
            path = workflows_dir / workflow
            checks.append(
                {
                    "name": workflow,
                    "status": "pass" if path.exists() else "fail",
                    "message": f"Workflow {workflow}",
                }
            )

        status = "pass" if all(c["status"] == "pass" for c in checks) else "fail"
        return {"status": status, "details": checks}

    def _summarize(self) -> Dict:
        """Resumen ejecutivo."""
        total_checks = len(self.results["checks"])
        passed = sum(1 for c in self.results["checks"].values() if c.get("status") == "pass")
        failed = total_checks - passed

        return {
            "total": total_checks,
            "passed": passed,
            "failed": failed,
            "warnings": len(self.results["warnings"]),
            "errors": len(self.results["errors"]),
            "ready_for_deploy": failed == 0 and len(self.results["errors"]) == 0,
        }

    def print_report(self):
        """Imprime reporte legible."""
        print("\n" + "=" * 70)
        print("PRE-DEPLOY VALIDATION REPORT")
        print("=" * 70)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Status: {self.results['status'].upper()}")
        print()

        # Summary
        summary = self.results["summary"]
        print(f"Checks: {summary['passed']}/{summary['total']} passed")
        if summary["warnings"]:
            print(f"⚠️  Warnings: {summary['warnings']}")
        if summary["errors"]:
            print(f"❌ Errors: {summary['errors']}")
        print()

        # Details
        for check_name, check_result in self.results["checks"].items():
            status_icon = "✅" if check_result.get("status") == "pass" else "❌"
            print(f"{status_icon} {check_name}")
            if "details" in check_result:
                for detail in check_result["details"]:
                    detail_icon = "  ✓" if detail["status"] == "pass" else "  ✗"
                    print(f"{detail_icon} {detail['name']}: {detail['message']}")

        # Warnings
        if self.results["warnings"]:
            print("\n⚠️  Warnings:")
            for warning in self.results["warnings"]:
                print(f"  - {warning}")

        # Errors
        if self.results["errors"]:
            print("\n❌ Errors:")
            for error in self.results["errors"]:
                print(f"  - {error}")

        print("\n" + "=" * 70)
        if summary["ready_for_deploy"]:
            print("✅ READY FOR DEPLOY")
        else:
            print("❌ NOT READY FOR DEPLOY - Fix issues above")
        print("=" * 70 + "\n")

    def export_json(self) -> str:
        """Exporta resultado en JSON."""
        return json.dumps(self.results, indent=2)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Pre-deploy validation for Fly.io MVP")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).parent.parent.parent),
        help="Root of repository",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of human-readable report",
    )

    args = parser.parse_args()
    repo_root = Path(args.repo_root)

    validator = PreDeployValidator(repo_root)
    exit_code = validator.run_all_checks()

    if args.json:
        print(validator.export_json())
    else:
        validator.print_report()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
