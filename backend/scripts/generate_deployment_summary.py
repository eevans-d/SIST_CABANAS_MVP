#!/usr/bin/env python3
"""Generate Deployment Summary Report.

Consolida estado de readiness y genera DEPLOYMENT_SUMMARY.md automático.
Integra:
- Resultado de validaciones pre-deploy
- Checklist de producción (estado)
- Próximos pasos automatizados

Uso:
    python scripts/generate_deployment_summary.py \
      --validate \
      --repo-root . \
      --output backend/docs/DEPLOYMENT_SUMMARY.md
"""
# flake8: noqa
# pylint: disable=all
# bandit: nosec

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


class DeploymentSummaryGenerator:
    """Genera reporte de resumen de despliegue."""

    def __init__(self, repo_root: Path, output_file: Path):
        """Initialize with repo root and output file."""
        self.repo_root = repo_root
        self.output_file = output_file
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


class DeploymentSummaryGenerator:
    """Genera reporte de resumen de despliegue."""

    def __init__(self, repo_root: Path, output_file: Path):
        self.repo_root = repo_root
        self.output_file = output_file
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

    def run_validation(self) -> dict:
        """Ejecuta script de validación y retorna resultado."""
        script = self.repo_root / "backend" / "scripts" / "validate_predeploy.py"
        if not script.exists():
            return {"status": "error", "message": "validate_predeploy.py not found"}

        try:
            result = subprocess.run(
                ["python", str(script), "--json", "--repo-root", str(self.repo_root)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return json.loads(result.stdout)
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def check_git_status(self) -> dict:
        """Verifica estado de git."""
        try:
            # Cambios pendientes
            result = subprocess.run(
                ["git", "-C", str(self.repo_root), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            changed_files = [line for line in result.stdout.split("\n") if line.strip()]

            # Último commit
            result = subprocess.run(
                ["git", "-C", str(self.repo_root), "log", "-1", "--pretty=%H %s"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            last_commit = result.stdout.strip()

            return {
                "status": "ok",
                "changed_files": len(changed_files),
                "last_commit": last_commit,
                "uncommitted": changed_files[:5],  # Primeros 5
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def check_requirements(self) -> dict:
        """Verifica paquetes críticos en requirements."""
        req_file = self.repo_root / "backend" / "requirements.txt"
        if not req_file.exists():
            return {"status": "error", "message": "requirements.txt not found"}

        content = req_file.read_text()
        critical = ["fastapi", "sqlalchemy", "asyncpg", "redis"]
        present = [pkg for pkg in critical if pkg.lower() in content.lower()]

        return {
            "status": "ok",
            "total_critical": len(critical),
            "present": len(present),
            "packages": present,
        }

    def generate_markdown(self, validation: dict, git_status: dict, requirements: dict) -> str:
        """Genera markdown del reporte."""
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

        # Determinar status global
        global_status = (
            "🟢 READY" if validation.get("summary", {}).get("ready_for_deploy") else "🔴 NOT READY"
        )

        markdown = f"""# Deployment Summary Report

**Generated:** {now}
**Status:** {global_status}

---

## 1. Validation Status

| Metric | Value |
|--------|-------|
| Total Checks | {validation.get('summary', {}).get('total', 0)} |
| Passed | {validation.get('summary', {}).get('passed', 0)} |
| Failed | {validation.get('summary', {}).get('failed', 0)} |
| Warnings | {validation.get('summary', {}).get('warnings', 0)} |
| Ready for Deploy | {"✅ YES" if validation.get('summary', {}).get('ready_for_deploy') else "❌ NO"} |

### Check Results

"""

        for check_name, check_result in validation.get("checks", {}).items():
            status_icon = "✅" if check_result.get("status") == "pass" else "❌"
            markdown += f"- {status_icon} **{check_name}**"
            if check_result.get("status") == "fail":
                markdown += f" - {check_result.get('message', 'Failed')}"
            markdown += "\n"

        if validation.get("warnings"):
            markdown += "\n### Warnings\n\n"
            for warning in validation["warnings"]:
                markdown += f"- ⚠️ {warning}\n"

        if validation.get("errors"):
            markdown += "\n### Errors\n\n"
            for error in validation["errors"]:
                markdown += f"- ❌ {error}\n"

        # Git Status
        markdown += "\n---\n\n## 2. Git Status\n\n"
        if git_status.get("status") == "ok":
            markdown += f"| Item | Value |\n"
            markdown += f"|------|-------|\n"
            markdown += f"| Changed Files | {git_status.get('changed_files', 0)} |\n"
            markdown += f"| Last Commit | `{git_status.get('last_commit', 'N/A')[:40]}...` |\n"
            if git_status.get("uncommitted"):
                markdown += f"\n**Uncommitted Changes:**\n"
                for file in git_status["uncommitted"]:
                    markdown += f"- {file}\n"
        else:
            markdown += f"❌ Error: {git_status.get('message')}\n"

        # Requirements
        markdown += "\n---\n\n## 3. Requirements Check\n\n"
        if requirements.get("status") == "ok":
            markdown += f"| Item | Value |\n"
            markdown += f"|------|-------|\n"
            markdown += f"| Critical Packages | {requirements.get('total_critical', 0)} |\n"
            markdown += f"| Present | {requirements.get('present', 0)} |\n"
            markdown += f"\n**Installed:**\n"
            for pkg in requirements.get("packages", []):
                markdown += f"- ✅ {pkg}\n"
        else:
            markdown += f"❌ Error: {requirements.get('message')}\n"

        # Deployment Checklist
        markdown += "\n---\n\n## 4. Pre-Deployment Checklist\n\n"
        checklist = [
            (
                "All validation checks passed",
                validation.get("summary", {}).get("ready_for_deploy", False),
            ),
            ("No uncommitted changes", git_status.get("changed_files", 0) == 0),
            (
                "Critical packages present",
                requirements.get("present", 0) == requirements.get("total_critical", 0),
            ),
            (
                "fly.toml exists and valid",
                validation.get("checks", {}).get("fly_toml", {}).get("status") == "pass",
            ),
            (
                "Dockerfile valid",
                validation.get("checks", {}).get("dockerfile", {}).get("status") == "pass",
            ),
            (
                "Alembic migrations ready",
                validation.get("checks", {}).get("alembic", {}).get("status") == "pass",
            ),
            (
                "GitHub workflows configured",
                validation.get("checks", {}).get("github_workflows", {}).get("status") == "pass",
            ),
        ]

        for item, done in checklist:
            icon = "✅" if done else "❌"
            markdown += f"- {icon} {item}\n"

        # Next Steps
        markdown += "\n---\n\n## 5. Next Steps\n\n"
        next_steps = [
            "Review validation report above",
            "Fix any failed checks",
            "Commit changes: `git add -A && git commit -m 'pre-deploy: fixes'`",
            "Push to main: `git push origin main`",
            "Use **ops/STAGING_DEPLOYMENT_PLAYBOOK.md** for staging deploy",
            "Monitor deployment with: `flyctl logs -a sist-cabanas-mvp -f`",
            "Validate endpoints: `/api/v1/healthz`, `/metrics`",
            "Run benchmark: `./ops/smoke_and_benchmark.sh <BASE_URL>`",
            "Test anti-double-booking: `RUN_MUTATING=1 python backend/scripts/concurrency_overlap_test.py`",
        ]

        for i, step in enumerate(next_steps, 1):
            markdown += f"{i}. {step}\n"

        # Production Readiness
        markdown += "\n---\n\n## 6. Production Readiness\n\n"
        markdown += "Before moving to production:\n\n"
        markdown += "- [ ] Use **ops/PROD_READINESS_CHECKLIST.md** to verify all items\n"
        markdown += "- [ ] Ensure staging deployment successful and stable (24h)\n"
        markdown += "- [ ] Perform full backup before cutover\n"
        markdown += "- [ ] Schedule maintenance window\n"
        markdown += "- [ ] Have rollback plan ready: `flyctl releases rollback`\n"
        markdown += "- [ ] On-call engineer assigned\n"
        markdown += "- [ ] Monitoring and alerts active\n"

        # Footer
        markdown += f"\n---\n\n**Report Generated:** {now}\n"
        markdown += "**Tools:** validate_predeploy.py + generate_deployment_summary.py\n"

        return markdown

    def generate(self) -> int:
        """Genera el reporte completo."""
        print("📊 Generating deployment summary...")

        # Ejecutar validaciones
        print("  - Running pre-deploy validation...")
        validation = self.run_validation()

        print("  - Checking git status...")
        git_status = self.check_git_status()

        print("  - Checking requirements...")
        requirements = self.check_requirements()

        # Generar markdown
        print("  - Generating markdown...")
        markdown = self.generate_markdown(validation, git_status, requirements)

        # Guardar
        self.output_file.write_text(markdown)
        print(f"✅ Report saved to: {self.output_file}")

        # Print short summary
        print("\n" + "=" * 70)
        summary = validation.get("summary", {})
        print(f"Status: {validation.get('status', 'unknown').upper()}")
        print(f"Checks: {summary.get('passed', 0)}/{summary.get('total', 0)} passed")
        print(f"Ready for Deploy: {'✅ YES' if summary.get('ready_for_deploy') else '❌ NO'}")
        print("=" * 70 + "\n")

        return 0 if summary.get("ready_for_deploy") else 1


def main():
    parser = argparse.ArgumentParser(description="Generate deployment summary report")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).parent.parent.parent),
        help="Root of repository",
    )
    parser.add_argument(
        "--output",
        default="backend/docs/DEPLOYMENT_SUMMARY.md",
        help="Output file path",
    )

    args = parser.parse_args()
    repo_root = Path(args.repo_root)
    output_file = repo_root / args.output

    generator = DeploymentSummaryGenerator(repo_root, output_file)
    return generator.generate()


if __name__ == "__main__":
    sys.exit(main())
