# Compos Mentis — btop Theme Spec

## Panels

5 panels + footer. Minimum 80x24. Dynamic resize.

### 1. Timer (top-left, 3fr)

- Pure countdown, centered, large Digits widget
- Clock top-right, soft white `#7b88a1`, ticks every second
- Progress bar bottom: `██████░░░░░░ 22%` inline, btop style
- Bar uses gradient: green `#a3be8c` → yellow `#ebcb8b` as session progresses
- Percentage text bright white `#d8dee9`
- Border title reflects state: `timer`, `timer · work`, `timer · break`, `timer · paused`, `timer · done`
- Title color matches state accent
- Colors: green `#a3be8c` work, blue `#88c0d0` break, dim `#4c566a` idle/paused

### 2. Session (top-right, 2fr)

- Key-value pairs, labels col 3, values col 12
- Fields: `#` (roman numeral), `started` (HH:MM or `—`), `config` (50m / 10m), `log` (log dir path)
- Labels teal `#5c7a7a`, values white `#d8dee9`

### 3. Pulse (bottom-left, 3fr)

- Paired vertical bar histogram, one pair per session
- Left bar = energy (amber `#ebcb8b`), right bar = focus (green `#a3be8c`)
- Block characters: `░ ▁ ▂ ▃ ▄ ▅ ▆ ▇ █`
- Roman numeral x-axis labels below bars, teal `#5c7a7a`
- Legend bottom: `░ energy  ░ focus` in respective colors
- Bars grow taller when panel has vertical room
- Shows last 8 sessions max, most recent on right
- Empty state: panel empty (no placeholder text needed — pulse only appears after first session)

### 4. Log (bottom-right, 2fr)

- Summary line: `2h 30m · 3 sessions` — bright white `#d8dee9`
- Thin separator: `╶─────────────────────╴` in dark teal `#2a4444`
- Session entries: `HH:MM  XXm  note` — soft white `#9aa5b4`
- Notes truncate with `…` when panel is narrow
- Most recent first, max 6 at 80x24, more when taller
- Empty state: `no sessions yet` in teal `#5c7a7a`

### 5. Reflect (full width, appears on session end)

- Warm amber border `#d08770`, title: `reflect` in amber
- Three progressive steps within one panel:
  1. `note     > text input█` — text input, white `#d8dee9`
  2. `energy   ░░░░░  (1-5)` — single keypress, blocks fill in amber `#ebcb8b`
  3. `focus    ░░░░░  (1-5)` — single keypress, blocks fill in green `#a3be8c`
- Completed lines dim to `#7b88a1`, locked values show `4/5` right-aligned
- Empty blocks `#1a2a2a`
- Panel vanishes after focus entered, break starts

### 6. Aphorism

- Centered below all panels, above footer
- Latin line italic, soft teal `#5c7a7a`
- Attribution/translation dimmer teal `#3d5656`
- Refreshes on each work/break start
- Long text wraps to second line, stays centered

### 7. Footer

- Context-sensitive keybindings:
  - IDLE: `s start  q quit`
  - WORKING/BREAK: `p pause  k skip  q quit`
  - PAUSED: `p resume  k skip  q quit`
  - NOTE_INPUT: `enter submit  q quit`
  - ENERGY/FOCUS: `(1-5)  q quit`
- Key letters: cyan `#5ccfe6`, label text: soft white `#7b88a1`

## Color palette

Base: dark teal undertone throughout. Nord-meets-btop.

| Element                      | Hex       | Role              |
|------------------------------|-----------|-------------------|
| Panel borders                | `#2a5c5c` | dark teal         |
| Border titles                | `#5ccfe6` | bright cyan       |
| Work (timer, bar, title)     | `#a3be8c` | bright green      |
| Break (timer, bar, title)    | `#88c0d0` | bright blue       |
| Reflect border               | `#d08770` | warm amber        |
| Energy bars / dots           | `#ebcb8b` | amber/yellow      |
| Focus bars / dots            | `#a3be8c` | green             |
| Progress bar gradient end    | `#ebcb8b` | yellow            |
| Idle / paused                | `#4c566a` | dark gray         |
| Primary text (values, data)  | `#d8dee9` | bright white      |
| Secondary text (log entries) | `#9aa5b4` | soft white        |
| Tertiary text (clock, dims)  | `#7b88a1` | muted white       |
| Labels (session, x-axis)     | `#5c7a7a` | teal              |
| Aphorism latin               | `#5c7a7a` | soft teal italic  |
| Aphorism attribution         | `#3d5656` | dim teal          |
| Separator                    | `#2a4444` | dark teal         |
| Empty bar blocks             | `#1a2a2a` | near-black teal   |
| Footer keys                  | `#5ccfe6` | cyan              |
| Footer labels                | `#7b88a1` | muted white       |

Three accent colors: **green** (working), **blue** (resting), **amber** (reflecting).
Teal undertone unifies everything — the app feels like it belongs next to btop.

## Resize behavior

- Minimum: 80x24
- Top row: timer 3fr, session 2fr
- Bottom row: pulse 3fr, log 2fr
- Reflect: full width, spans both columns
- Panels grow with terminal. Digits always centered. Clock always right-aligned.
- Log notes truncate with `…` on narrow, expand on wide
- Pulse bars get taller vertically, more spacing horizontally
- Log shows more entries when taller
- Aphorism + footer pinned to bottom

## State machine

IDLE → WORKING → NOTE_INPUT → ENERGY_INPUT → FOCUS_INPUT → ON_BREAK → WORKING ...

Pause available during WORKING and ON_BREAK. Skip available during WORKING, ON_BREAK, and PAUSED.

## Log format

Daily markdown files with YAML frontmatter in `--log-dir` (default `./logs/`):

```markdown
---
date: 2026-04-12
type: pomodoro-log
sessions: 3
total_focus: 2h 30m
---

# 2026-04-12

| # | Start | End | Duration | Type | Energy | Focus | Notes |
|---|-------|-----|----------|------|--------|-------|-------|
| 1 | 10:00 | 10:50 | 50m | work | 3 | 3 | planning |
| 1 | 10:50 | 11:00 | 10m | break |  |  |  |
| 2 | 11:00 | 11:50 | 50m | work | 5 | 4 | deep work |
```

## CLI

```
compos-mentis [-w MINUTES] [-b MINUTES] [--log-dir PATH]
```

Single theme (btop). No `-v` flag for now.

## Future inspiration

- **pomo** (github.com/Bahaaio/pomo): ASCII art timer fonts (mono12, rebel, ansi, ansiShadow), `pomo stats` with weekly bar chart + 4-month GitHub-style heatmap. Worth revisiting for a `compos-mentis stats` command later.
