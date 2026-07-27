#!/usr/bin/env python3
"""PreToolUse guard: deny Bash commands that would destroy .mas/.

.mas holds unrecoverable bench history and failure forensics; it was wiped
once (2026-07-26, runs 1-8 lost). This guard tokenizes the command with
shlex — quotes and heredoc bodies are DATA, not commands — so prose that
merely mentions the dangerous strings passes, while the real thing is
denied at any command position (start, after ;/&&/|/newline, inside a
one-level bash -c payload).
"""
import json
import re
import shlex
import sys

RM_MSG = (
    "Blocked: recursive rm targeting .mas — unrecoverable bench history and "
    "failure forensics live there (see autoproduct/CLAUDE.md)."
)
CLEAN_MSG = (
    "Blocked: git clean with -x/-X deletes gitignored files — it wiped "
    "autoproduct/.mas once. Plain git clean -fd spares ignored files."
)
OPERATORS = {";", "|", "&", "&&", "||", ";;", "|&", ";&", ";;&"}
WRAPPERS = {"sudo", "env", "command", "nohup", "timeout", "xargs"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}


def strip_heredocs(text: str) -> str:
    out, delim = [], None
    for line in text.split("\n"):
        if delim is not None:
            if line.strip() == delim:
                delim = None
            continue
        match = re.search(r"<<-?\s*(['\"]?)(\w+)\1", line)
        out.append(line)
        if match:
            delim = match.group(2)
    return "\n".join(out)


def simple_commands(text: str):
    """Yield argv lists for each simple command; None on unparseable."""
    try:
        lex = shlex.shlex(text, posix=True, punctuation_chars=";|&")
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        return None
    segments, current = [], []
    for token in tokens:
        if token in OPERATORS or all(c in ";|&" for c in token):
            if current:
                segments.append(current)
            current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return segments


def check(text: str, depth: int = 0) -> str | None:
    text = strip_heredocs(text).replace("\n", ";")
    segments = simple_commands(text)
    if segments is None:
        # Unparseable (unbalanced quotes): conservative raw-regex fallback.
        if re.search(r"(?:^|[;&|]\s*)git\s+clean\b[^|;&]*\s-\w*[xX]", text, re.M):
            return CLEAN_MSG
        if ".mas" in text and re.search(
            r"(?:^|[;&|]\s*)rm\s+-\w*[rR][^|;&]*\.mas", text, re.M
        ):
            return RM_MSG
        return None
    for argv in segments:
        i = 0
        while i < len(argv) and re.match(r"^\w+=", argv[i]):
            i += 1  # leading VAR=... assignments
        while i < len(argv) and argv[i].rsplit("/", 1)[-1] in WRAPPERS:
            i += 1
        if i >= len(argv):
            continue
        prog = argv[i].rsplit("/", 1)[-1]
        rest = argv[i + 1:]
        if prog == "rm":
            recursive = any(
                a.startswith("-") and not a.startswith("--") and
                any(c in "rR" for c in a[1:]) for a in rest
            ) or "--recursive" in rest
            hits_mas = any(".mas" in a for a in rest if not a.startswith("-"))
            if recursive and hits_mas:
                return RM_MSG
        elif prog == "git" and rest[:1] == ["clean"]:
            if any(
                a.startswith("-") and not a.startswith("--") and
                any(c in "xX" for c in a[1:]) for a in rest[1:]
            ):
                return CLEAN_MSG
        elif prog in SHELLS and depth < 1 and "-c" in rest:
            payload_index = rest.index("-c") + 1
            if payload_index < len(rest):
                verdict = check(rest[payload_index], depth + 1)
                if verdict:
                    return verdict
    return None


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = (data.get("tool_input") or {}).get("command") or ""
    verdict = check(command)
    if verdict:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": verdict,
            }
        }))


if __name__ == "__main__":
    main()
