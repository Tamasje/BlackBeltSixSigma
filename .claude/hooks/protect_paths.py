#!/usr/bin/env python3
"""PreToolUse guard for Edit/Write/MultiEdit.

Blocks (exit 2) any write inside `source/`, and any write to
`inventory/worked_examples.json` once the git tag `oracle-approved` exists.
"""
import json
import os
import subprocess
import sys

ORACLE_REL = os.path.join("inventory", "worked_examples.json")
ORACLE_TAG = "oracle-approved"


def block(message: str) -> None:
    """Print the reason for Claude and exit 2, which makes Claude Code refuse the tool call."""
    print(f"protect_paths: {message}", file=sys.stderr)
    sys.exit(2)


def canonical(path: str) -> str:
    """Resolve symlinks and '..', then casefold, because macOS volumes are case-insensitive
    and 'Source/x' would otherwise slip past a case-sensitive comparison."""
    return os.path.realpath(path).casefold()


def is_inside(path: str, directory: str) -> bool:
    """True if `path` is `directory` itself or anything below it."""
    return path == directory or path.startswith(directory + os.sep)


def oracle_tag_exists(project_dir: str) -> bool:
    """True if the git tag that locks the oracle exists in the project repository."""
    result = subprocess.run(
        ["git", "-C", project_dir, "rev-parse", "-q", "--verify", f"refs/tags/{ORACLE_TAG}"],
        capture_output=True,
    )
    return result.returncode == 0


def main() -> None:
    """Read the hook JSON from stdin and decide whether the write may proceed."""
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Fail closed: an unreadable payload must not become a silent bypass.
        block("could not parse hook input; refusing the write.")

    file_path = (payload.get("tool_input") or {}).get("file_path")
    if not file_path:
        sys.exit(0)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()
    # os.path.join keeps absolute paths as they are and anchors relative ones at the project.
    target = canonical(os.path.join(project_dir, file_path))
    root = canonical(project_dir)

    if is_inside(target, os.path.join(root, "source")):
        block(f"{file_path} is inside source/, which is read-only (CLAUDE.md).")

    if target == os.path.join(root, ORACLE_REL.casefold()) and oracle_tag_exists(project_dir):
        block(
            f"{ORACLE_REL} is locked by the git tag '{ORACLE_TAG}'. "
            "Only the user extends the oracle and moves the tag."
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
