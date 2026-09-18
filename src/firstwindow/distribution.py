from __future__ import annotations

from dataclasses import dataclass


HERMES_DESKTOP_URL = "https://hermes-agent.nousresearch.com/desktop"
AGNES_DESKTOP_URL = "https://agnescode.agnes-ai.cn/zh-Hans/docs/getting-started/installation/"


@dataclass(frozen=True)
class BeginnerSetupAction:
    target_name: str
    kind: str
    target: str
    label: str
    requires_user_action: bool = True


def beginner_setup_action(target: str) -> BeginnerSetupAction:
    if target == "hermes":
        return BeginnerSetupAction(
            target_name="hermes",
            kind="open_url",
            target=HERMES_DESKTOP_URL,
            label="Download Hermes Desktop from the official site",
        )
    if target == "agnes":
        return BeginnerSetupAction(
            target_name="agnes",
            kind="open_url",
            target=AGNES_DESKTOP_URL,
            label="Download Agnes Code Desktop from the official installation page",
        )
    raise ValueError(f"unsupported beginner setup target: {target}")
