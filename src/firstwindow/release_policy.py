from __future__ import annotations


def validate_windows_release_workflow(text: str) -> list[str]:
    failures: list[str] = []
    lowered = text.lower()

    if "v0.2.0" in lowered:
        failures.append("release workflow must not contain a hard-coded legacy v0.2.0 release")

    tag_driven = (
        "tags:" in text
        and "v*" in text
        and "refs/tags/" in text
    )
    if not tag_driven:
        failures.append("release publication must be tag-driven from v* refs")

    if "refs/heads/main" in text and ("gh release create" in lowered or "gh release edit" in lowered):
        failures.append("main push must not mutate a release; publication must be tag-driven")

    if "sha256sums.txt" not in lowered:
        failures.append("release workflow must produce and publish a SHA256 checksum asset")

    if "gh release create" not in lowered:
        failures.append("release workflow must create a release for a version tag")

    return failures
