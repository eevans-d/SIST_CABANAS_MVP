#!/usr/bin/env python3
"""SIST CABAÑAS MVP - Deployment Status Dashboard.

Genera un reporte visual de estado actual

Usage:
  python backend/scripts/deployment_dashboard.py
  python backend/scripts/deployment_dashboard.py --json
"""

import json
import subprocess  # nosec
import sys
from datetime import datetime
from pathlib import Path

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check_git_status():
    """Verificar estado de git."""
    result = subprocess.run(  # nosec
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd="/home/eevan/ProyectosIA/SIST_CABAÑAS",
    )
    changes = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
    return {"changes": changes, "clean": changes == 0}


def check_files_exist():
    """Verificar existencia de archivos críticos."""
    base_path = Path("/home/eevan/ProyectosIA/SIST_CABAÑAS")
    files_to_check = {
        "fly.toml": base_path / "fly.toml",
        "Dockerfile": base_path / "backend" / "Dockerfile",
        "start-fly.sh": base_path / "backend" / "start-fly.sh",
        "env/.env.fly.staging.template": base_path / "env" / ".env.fly.staging.template",
        "ops/staging-deploy-interactive.sh": base_path / "ops" / "staging-deploy-interactive.sh",
        "STAGING_DEPLOYMENT_QUICK_START.md": base_path
        / "ops"
        / "STAGING_DEPLOYMENT_QUICK_START.md",
        "GO_NO_GO_CHECKLIST.md": base_path / "ops" / "GO_NO_GO_CHECKLIST.md",
        "INCIDENT_RESPONSE_RUNBOOK.md": base_path / "ops" / "INCIDENT_RESPONSE_RUNBOOK.md",
    }
    return {name: path.exists() for name, path in files_to_check.items()}


def check_fly_auth():
    """Verificar autenticación en Fly."""
    result = subprocess.run(  # nosec
        ["flyctl", "auth", "whoami"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def check_app_exists():
    """Verificar si app existe en Fly."""
    result = subprocess.run(  # nosec
        ["flyctl", "apps", "list"],
        capture_output=True,
        text=True,
    )
    return "sist-cabanas-mvp" in result.stdout


def get_commits():
    """Obtener últimos commits."""
    result = subprocess.run(  # nosec
        ["git", "log", "--oneline", "-5"],
        capture_output=True,
        text=True,
        cwd="/home/eevan/ProyectosIA/SIST_CABAÑAS",
    )
    return result.stdout.strip().split("\n")


def render_dashboard(as_json=False):
    """Render deployment status dashboard."""
    git_status = check_git_status()
    files = check_files_exist()
    fly_auth = check_fly_auth()
    app_exists = check_app_exists()
    commits = get_commits()

    data = {
        "timestamp": datetime.now().isoformat(),
        "status": "READY FOR STAGING",
        "git": git_status,
        "files": files,
        "fly": {"authenticated": fly_auth, "app_exists": app_exists},
        "commits": commits,
    }

    if as_json:
        print(json.dumps(data, indent=2))
        return

    # ASCII Dashboard
    print(f"\n{BOLD}{CYAN}")
    print("    ╔══════════════════════════════════════════════════════════════╗")  # noqa: E501
    print("    ║  SIST CABANAS MVP - DEPLOYMENT STATUS DASHBOARD             ║")  # noqa: E501
    print("    ╚══════════════════════════════════════════════════════════════╝")  # noqa: E501
    print(f"{RESET}\n")

    # Overall Status
    print(f"{BOLD}OVERALL STATUS:{RESET}")
    status_color = GREEN if all(files.values()) and git_status["clean"] else YELLOW
    print(f"  {status_color}READY FOR STAGING{RESET}\n")

    # Git
    print(f"{BOLD}GIT REPOSITORY:{RESET}")
    git_msg = (
        f"{GREEN}Clean{RESET}"
        if git_status["clean"]
        else f"{YELLOW}{git_status['changes']} changes{RESET}"
    )
    print(f"  Status: {git_msg}")
    print("  Latest commits:")
    for i, commit in enumerate(commits[:3], 1):
        print(f"    {i}. {commit}")
    print()

    # Files
    print(f"{BOLD}CRITICAL FILES:{RESET}")
    for fname, exists in files.items():
        status = f"{GREEN}OK{RESET}" if exists else f"{RED}MISSING{RESET}"
        print(f"  [{status}] {fname}")
    print()

    # Fly.io
    print(f"{BOLD}FLY.IO INFRASTRUCTURE:{RESET}")
    auth_status = f"{GREEN}Authenticated{RESET}" if fly_auth else f"{RED}Not authenticated{RESET}"
    app_status = f"{GREEN}App exists{RESET}" if app_exists else f"{YELLOW}App not found{RESET}"
    print(f"  Auth: {auth_status}")
    print(f"  App: {app_status}")
    print()

    # Next Steps
    print(f"{BOLD}NEXT STEPS:{RESET}")
    print(f"  1. Fill secrets in env/.env.fly.staging")  # noqa: F541
    print(f"  2. Run: ./ops/staging-deploy-interactive.sh")  # noqa: F541
    print(f"  3. Or manual: flyctl deploy --remote-only -a sist-cabanas-mvp")  # noqa: F541
    print()

    print(f"{BOLD}{GREEN}Ready to deploy!{RESET}\n")


if __name__ == "__main__":
    json_mode = "--json" in sys.argv
    render_dashboard(as_json=json_mode)
