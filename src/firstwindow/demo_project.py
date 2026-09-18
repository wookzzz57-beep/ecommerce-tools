from __future__ import annotations

from pathlib import Path


_README = """# FirstWindow Demo

This tiny project is a safe place to try your first coding-agent task.

Suggested task:

> Improve this page with a polished hero section, keep it dependency-free, and verify the HTML still contains the FirstWindow Demo heading.

Files:
- index.html — the demo page
- README.md — this guide
"""

_INDEX = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FirstWindow Demo</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 760px; margin: 80px auto; padding: 24px; }
    h1 { font-size: clamp(42px, 8vw, 72px); letter-spacing: -0.04em; }
    p { color: #5b6470; font-size: 18px; line-height: 1.6; }
  </style>
</head>
<body>
  <h1>FirstWindow Demo</h1>
  <p>This page is intentionally small so a first-time user can watch an agent make a visible change.</p>
</body>
</html>
"""


def create_demo_project(target: Path) -> Path:
    target = target.expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty folder: {target}")
    target.mkdir(parents=True, exist_ok=True)
    (target / "README.md").write_text(_README, encoding="utf-8")
    (target / "index.html").write_text(_INDEX, encoding="utf-8")
    return target
