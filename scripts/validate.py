from pathlib import Path


REQUIRED = [
    "README.md","LICENSE","AGENTS.md","pyproject.toml",
    "src/firstwindow/cli.py","src/firstwindow/gui.py","src/firstwindow/router.py",
    "src/firstwindow/durable.py","src/firstwindow/runners.py","src/firstwindow/bootstrap.py",
    "src/firstwindow/system_status.py","src/firstwindow/onboarding.py","src/firstwindow/demo_project.py",
    "scripts/firstwindow_gui.py","site/index.html","site/app.js","site/styles.css",
    ".github/workflows/ci.yml",".github/workflows/windows-build.yml",
]


def main() -> int:
    missing = [path for path in REQUIRED if not Path(path).is_file()]
    if missing:
        print("missing required files:")
        print("\n".join(f"- {path}" for path in missing))
        return 1
    print(f"validated {len(REQUIRED)} required files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
