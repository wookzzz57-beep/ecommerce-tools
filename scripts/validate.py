from pathlib import Path

REQUIRED = [
    "README.md","LICENSE","AGENTS.md","pyproject.toml",
    "src/firstwindow/cli.py","src/firstwindow/router.py",
    "src/firstwindow/durable.py","src/firstwindow/runners.py",
    "site/index.html","site/app.js","site/styles.css"
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
