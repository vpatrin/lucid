# Lucid — Project Context

Monorepo for personal productivity tools.

## Hard Rules

### Git
- NEVER mention Claude, AI, or any attribution in code, comments, or any artifact

### Deployment
- Victor handles all deployments and packaging
- Do not run build/package commands without explicit instruction

## Repo Structure

```
lucid/
  Makefile            ← root, delegates to subprojects
  pomodoro/           ← focus timer (compos mentis)
    pyproject.toml
    src/compos_mentis/
    SPEC.md
```

## Design Philosophy

**Compos mentis** — "of sound mind." This is a mental discipline instrument, not a productivity gamification tool.

- **Aesthetic**: Minimal Stoic — clean, spacious, breathing room
- **Colors**: Amber/gold for work sessions, cool blue/teal for breaks
- **Tone**: Latin aphorisms with English translations
- **Feel**: Calm authority — the tool helps the user stay lucid, present, in control

## Architecture

### Pomodoro (`pomodoro/`)

Single-file TUI app (`app.py`) using Python + Textual.

- **State machine**: IDLE → WORKING → NOTE_INPUT → ENERGY_INPUT → FOCUS_INPUT → ON_BREAK → WORKING ...
- **Timer**: 50/10 default (configurable via CLI args `-w` and `-b`)
- **Logging**: Markdown daily files via `--log-dir` (default `./logs/`)
- **Package manager**: uv

## Working Style

- Show the plan before executing
- One step at a time, wait for confirmation
- Prefer simple over clever
- If unsure between approaches, ask instead of deciding alone
- Keep diffs tight
- Don't add features beyond what was asked

## Code Style

- Python: type hints, clear variable names
- No unnecessary abstractions — single file is fine until it isn't
