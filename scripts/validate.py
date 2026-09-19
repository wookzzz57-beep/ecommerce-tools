from pathlib import Path

from check_project_state import load_project_state, validate_project_state


REQUIRED = [
    "README.md","LICENSE","AGENTS.md","PROJECT_STATE.json","pyproject.toml",
    "docs/EXECUTION_CONTROL.md","docs/DURABLE_STATE.md",
    "src/firstwindow/cli.py","src/firstwindow/gui.py","src/firstwindow/router.py",
    "src/firstwindow/durable.py","src/firstwindow/runners.py","src/firstwindow/bootstrap.py",
    "src/firstwindow/system_status.py","src/firstwindow/onboarding.py","src/firstwindow/i18n.py","src/firstwindow/readiness.py","src/firstwindow/demo_project.py","src/firstwindow/windows_paths.py","src/firstwindow/resume.py","src/firstwindow/distribution.py","src/firstwindow/release_policy.py",
    "scripts/check_project_state.py","scripts/firstwindow_gui.py","site/index.html","site/app.js","site/styles.css",
    ".github/workflows/ci.yml",".github/workflows/windows-build.yml",
]


def main() -> int:
    missing = [path for path in REQUIRED if not Path(path).is_file()]
    if missing:
        print("missing required files:")
        print("\n".join(f"- {path}" for path in missing))
        return 1

    failures = validate_project_state(load_project_state())
    if failures:
        print("project state validation failed:")
        print("\n".join(f"- {item}" for item in failures))
        return 1

    print(f"validated {len(REQUIRED)} required files and project control state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
