import re
import sys
import subprocess
import argparse
from pathlib import Path


PII_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    (
        "Email",
        "email address",
        re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    ),
    (
        "Phone",
        "phone number",
        re.compile(
            r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"
        ),
    ),
    (
        "SSN",
        "social security number",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    ),
    (
        "Credit Card",
        "credit card number",
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    ),
    (
        "API Key",
        "API key (sk- format)",
        re.compile(r"\b(?:sk|pk)_[a-zA-Z0-9]{20,}\b"),
    ),
    (
        "AWS Key",
        "AWS access key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "GitHub Token",
        "GitHub personal access token",
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,}\b"),
    ),
    (
        "Slack Token",
        "Slack bot/webhook token",
        re.compile(r"\bxox[baprs]-[a-zA-Z0-9-]{10,}\b"),
    ),
    (
        "Password Assignment",
        "password/secret assignment",
        re.compile(
            r"""(?i)(?:password|passwd|pwd|secret|private_key|api_key|apikey)\s*[=:]\s*['\"][^'\"]+['\"]"""
        ),
    ),
    (
        "Private IP",
        "private IP address",
        re.compile(
            r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
        ),
    ),
    (
        "Token in URL",
        "access token in URL",
        re.compile(r"(?:\?|&)(?:token|api_key|access_token|secret)=[^&\s]+"),
    ),
]


def scan_content(
    file_path: str, content: str
) -> list[tuple[int, str, str]]:
    matches: list[tuple[int, str, str]] = []
    for label, _, pattern in PII_PATTERNS:
        for m in pattern.finditer(content):
            line_num = content[: m.start()].count("\n") + 1
            matches.append((line_num, label, m.group()))
    return matches


def get_staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, check=True,
    )
    return [f for f in result.stdout.splitlines() if f.strip()]


def unstage_file(file_path: str) -> None:
    subprocess.run(
        ["git", "reset", "HEAD", "--", file_path],
        capture_output=True, check=True,
    )


def is_binary(file_path: str) -> bool:
    result = subprocess.run(
        ["git", "grep", "-c", "", "--", file_path],
        capture_output=True, text=True,
    )
    return result.returncode != 0


HOOK_SOURCE = """#!/bin/sh
# PII Pre-Commit Hook
exec python3 "$(git rev-parse --show-toplevel)/scripts/pii-check.py"
"""


def install_hook() -> None:
    git_dir = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    hook_path = Path(git_dir) / "hooks" / "pre-commit"
    hook_path.write_text(HOOK_SOURCE)
    hook_path.chmod(0o755)
    print(f"Installed pre-commit hook at {hook_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="PII pre-commit check")
    parser.add_argument("--install", action="store_true", help="Install the hook")
    args = parser.parse_args()

    if args.install:
        install_hook()
        return

    staged_files = get_staged_files()
    found_pii = False

    for file_path in staged_files:
        if is_binary(file_path):
            continue

        result = subprocess.run(
            ["git", "show", f":{file_path}"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            continue

        content = result.stdout
        matches = scan_content(file_path, content)
        if matches:
            found_pii = True
            print(f"\n[PII] {file_path}:")
            for line_num, label, matched in matches:
                print(f"  Line {line_num}: {label} detected")

            unstage_file(file_path)
            print(f"  -> Unstaged {file_path}")

    if found_pii:
        print(
            "\nPII detected and unstaged. Review the files above, "
            "remove sensitive data, then re-stage with `git add`."
        )
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
