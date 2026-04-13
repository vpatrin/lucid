"""Compos Mentis — Pomodoro Timer TUI."""

from __future__ import annotations

import argparse
import contextlib
import random
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Digits, Footer, Input, Label, Static

if TYPE_CHECKING:
    from textual import events

MIN_WIDTH = 80
MIN_HEIGHT = 24


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Constants
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
DEFAULT_WORK_MINUTES = 50
DEFAULT_BREAK_MINUTES = 10

WORK_COLOR = "#a3be8c"
BREAK_COLOR = "#88c0d0"
DIM_COLOR = "#4c566a"
AMBER_COLOR = "#ebcb8b"
BORDER_CYAN = "#5ccfe6"
LABEL_TEAL = "#5c7a7a"
TEXT_PRIMARY = "#d8dee9"
TEXT_SECONDARY = "#9aa5b4"
TEXT_TERTIARY = "#7b88a1"
EMPTY_BAR = "#2d3a3a"
SEPARATOR = "#2a4444"


class PomodoroState(Enum):
    IDLE = auto()
    WORKING = auto()
    ON_BREAK = auto()
    PAUSED = auto()
    NOTE_INPUT = auto()
    ENERGY_INPUT = auto()
    FOCUS_INPUT = auto()


APHORISMS = [
    ("Labor omnia vincit", "Work conquers all."),
    ("Nunc aut numquam", "Now or never."),
    ("Dum spiro, spero", "While I breathe, I hope."),
    ("Carpe diem", "Seize the day."),
    ("Per aspera ad astra", "Through hardship to the stars."),
    ("Vincit qui se vincit", "He conquers who conquers himself."),
    ("Sapere aude", "Dare to know."),
    ("Waste no more time arguing about what a good man should be. Be one.", "Marcus Aurelius"),
    ("The impediment to action advances action. What stands in the way becomes the way.", "Marcus Aurelius"),
    ("You have power over your mind, not outside events. Realize this, and you will find strength.", "Marcus Aurelius"),
    ("It is not death that a man should fear, but he should fear never beginning to live.", "Marcus Aurelius"),
    ("It is not that we have a short time to live, but that we waste a great deal of it.", "Seneca"),
    ("Luck is what happens when preparation meets opportunity.", "Seneca"),
    ("Difficulties strengthen the mind, as labor does the body.", "Seneca"),
    ("First say to yourself what you would be; and then do what you have to do.", "Epictetus"),
    ("No man is free who is not master of himself.", "Epictetus"),
    ("He who has a why to live can bear almost any how.", "Nietzsche"),
    ("One must still have chaos in oneself to give birth to a dancing star.", "Nietzsche"),
    ("That which does not kill us makes us stronger.", "Nietzsche"),
    ("Amor fati", "Love of fate."),
    ("Memento mori", "Remember you will die."),
    ("Festina lente", "Make haste slowly."),
    ("Nihil nimis", "Nothing in excess."),
]


def _fmt_session_num(n: int) -> str:
    return "\u2014" if n <= 0 else str(n)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# App
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class PomodoroApp(App):
    TITLE = "COMPOS MENTIS"
    CSS_PATH = "btop.tcss"

    BINDINGS = [
        Binding("s", "start", "start", show=True),
        Binding("p", "pause", "pause", show=True),
        Binding("k", "skip", "skip", show=True),
        Binding("q", "quit", "quit", show=True),
    ]

    def __init__(
        self,
        work_minutes: int = DEFAULT_WORK_MINUTES,
        break_minutes: int = DEFAULT_BREAK_MINUTES,
        log_dir: Path = DEFAULT_LOG_DIR,
    ):
        super().__init__()
        self.work_seconds = work_minutes * 60
        self.break_seconds = break_minutes * 60
        self.log_dir = log_dir
        self.state = PomodoroState.IDLE
        self.paused_from: PomodoroState | None = None
        self.elapsed = 0
        self.total = self.work_seconds
        self.pomodoro_count = 0
        self.session_start: datetime | None = None
        self.total_work_seconds = 0
        self._completed_session_start: datetime | None = None
        self._completed_elapsed: int = 0
        self._pending_note: str = ""
        self._pending_energy: int = 0
        self._pending_focus: int = 0
        self._today_log: list[dict] = []
        self._aphorism = random.choice(APHORISMS)

    # ── Layout ──────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Label(
            f"Terminal too small. Minimum: {MIN_WIDTH}x{MIN_HEIGHT}",
            id="size-warning",
        )
        with Vertical(id="root"):
            with Horizontal(id="top-row"):
                with Vertical(id="timer-panel"):
                    yield Label("", id="clock")
                    mm, ss = divmod(self.work_seconds, 60)
                    yield Digits(f"{mm:02d}:{ss:02d}", id="timer")
                    yield Static("", id="progress")
                with Vertical(id="session-panel"):
                    yield Static("", id="session-info")
            with Horizontal(id="bottom-row"):
                with Vertical(id="pulse-panel"):
                    yield Static("", id="pulse-chart")
                with Vertical(id="log-panel"):
                    yield Static("", id="log-content")
            with Vertical(id="reflect-panel"):
                with Horizontal(id="reflect-input-row"):
                    yield Label("note", id="reflect-input-label")
                    yield Input(id="note-input", placeholder="...")
                yield Static("", id="reflect-display")
            yield Label("", id="aphorism-text")
            yield Label("", id="aphorism-attr")
        yield Footer()

    def on_mount(self) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._load_today_log()
        self._restore_from_log()

        # Set border titles
        self.query_one("#timer-panel").border_title = "timer"
        self.query_one("#session-panel").border_title = "session"
        self.query_one("#pulse-panel").border_title = "pulse"
        self.query_one("#log-panel").border_title = "log"
        self.query_one("#reflect-panel").border_title = "reflect"

        # Prevent Input from stealing focus on mount
        self.query_one("#note-input", Input).can_focus = False
        self.set_focus(None)

        # Initial display
        self._update_clock()
        self._update_display()
        self._update_chrome()
        self._update_panels()
        self._set_aphorism()

        # Single timer for clock + countdown
        self.set_interval(1, self._on_tick)

        # Check initial size
        self._check_size()

    def on_resize(self) -> None:
        self._check_size()

    def _check_size(self) -> None:
        too_small = self.size.width < MIN_WIDTH or self.size.height < MIN_HEIGHT
        self.query_one("#size-warning").styles.display = "block" if too_small else "none"
        self.query_one("#root").styles.display = "none" if too_small else "block"
        if not too_small:
            self._update_display()
            self._update_panels()

    # ── Tick ────────────────────────────────────────────────────────

    def _on_tick(self) -> None:
        self._update_clock()
        if self.state in (PomodoroState.WORKING, PomodoroState.ON_BREAK):
            self.elapsed += 1
            self._update_display()
            if self.elapsed >= self.total:
                self._transition()

    def _update_clock(self) -> None:
        self.query_one("#clock", Label).update(datetime.now().strftime("%H:%M"))

    # ── Display ─────────────────────────────────────────────────────

    def _update_display(self) -> None:
        remaining = max(0, self.total - self.elapsed)
        mm, ss = divmod(remaining, 60)

        timer = self.query_one("#timer", Digits)
        timer.update(f"{mm:02d}:{ss:02d}")
        timer.remove_class("work", "on-break", "paused")
        cls = {
            PomodoroState.WORKING: "work",
            PomodoroState.ON_BREAK: "on-break",
            PomodoroState.PAUSED: "paused",
        }.get(self.state)
        if cls:
            timer.add_class(cls)

        self.query_one("#progress", Static).update(self._render_progress())

    def _update_chrome(self) -> None:
        title_map = {
            PomodoroState.IDLE: "timer",
            PomodoroState.WORKING: "timer \u00b7 work",
            PomodoroState.ON_BREAK: "timer \u00b7 break",
            PomodoroState.PAUSED: "timer \u00b7 paused",
            PomodoroState.NOTE_INPUT: "timer \u00b7 done",
            PomodoroState.ENERGY_INPUT: "timer \u00b7 done",
            PomodoroState.FOCUS_INPUT: "timer \u00b7 done",
        }
        panel = self.query_one("#timer-panel")
        panel.border_title = title_map.get(self.state, "timer")

        color_map = {
            PomodoroState.WORKING: WORK_COLOR,
            PomodoroState.ON_BREAK: BREAK_COLOR,
            PomodoroState.PAUSED: DIM_COLOR,
        }
        panel.styles.border_title_color = color_map.get(self.state, BORDER_CYAN)

        self.query_one("#session-info", Static).update(self._render_session_info())

    def _update_panels(self) -> None:
        self.query_one("#pulse-chart", Static).update(self._render_pulse_chart())
        self.query_one("#log-content", Static).update(self._render_log_content())

    def _set_aphorism(self) -> None:
        self._aphorism = random.choice(APHORISMS)
        self.query_one("#aphorism-text", Label).update(self._aphorism[0])
        self.query_one("#aphorism-attr", Label).update(self._aphorism[1])

    # ── Renderers ───────────────────────────────────────────────────

    def _render_progress(self) -> str:
        if self.total == 0:
            return ""

        if self.state == PomodoroState.ON_BREAK:
            progress = (self.total - self.elapsed) / self.total
        elif self.state == PomodoroState.IDLE:
            progress = 0.0
        else:
            progress = self.elapsed / self.total

        progress = max(0.0, min(1.0, progress))
        pct = int(progress * 100)
        # Dynamic: panel width minus padding (2+2), prefix (2), suffix (6 for "  XXX%")
        progress_widget = self.query_one("#progress", Static)
        bar_width = max(10, progress_widget.size.width - 8) if progress_widget.size.width > 0 else 36
        filled = int(bar_width * progress)
        empty = bar_width - filled

        bar = ""
        if filled > 0:
            if self.state == PomodoroState.WORKING:
                bar += f"[{WORK_COLOR}]" + "\u2588" * filled + "[/]"
            elif self.state == PomodoroState.ON_BREAK:
                bar += f"[{BREAK_COLOR}]" + "\u2588" * filled + "[/]"
            else:
                bar += f"[{DIM_COLOR}]" + "\u2588" * filled + "[/]"

        bar += f"[{EMPTY_BAR}]" + "\u2591" * empty + "[/]"

        return f"  {bar}  [{TEXT_PRIMARY}]{pct:>3}%[/]"

    def _render_session_info(self) -> str:
        if self.state == PomodoroState.IDLE:
            numeral = _fmt_session_num(self.pomodoro_count + 1)
            started = "\u2014"
        elif self.state in (PomodoroState.NOTE_INPUT, PomodoroState.ENERGY_INPUT, PomodoroState.FOCUS_INPUT):
            numeral = _fmt_session_num(self.pomodoro_count)
            started = self._completed_session_start.strftime("%H:%M") if self._completed_session_start else "\u2014"
        else:
            if self.state == PomodoroState.WORKING:
                numeral = _fmt_session_num(self.pomodoro_count + 1)
            else:
                numeral = _fmt_session_num(self.pomodoro_count)
            started = self.session_start.strftime("%H:%M") if self.session_start else "\u2014"

        wm, bm = self.work_seconds // 60, self.break_seconds // 60
        log_str = str(self.log_dir)
        if len(log_str) > 15:
            log_str = "\u2026" + log_str[-14:]

        return (
            f"[{LABEL_TEAL}]#        [/][{TEXT_PRIMARY}]{numeral}[/]\n"
            f"[{LABEL_TEAL}]started  [/][{TEXT_PRIMARY}]{started}[/]\n"
            f"[{LABEL_TEAL}]config   [/][{TEXT_PRIMARY}]{wm}m / {bm}m[/]\n"
            f"[{LABEL_TEAL}]log_dir  [/][{TEXT_PRIMARY}]{log_str}[/]"
        )

    def _render_pulse_chart(self) -> str:
        sessions: list[tuple[int, int, int]] = []
        for entry in self._today_log:
            if entry["type"] == "work" and entry.get("energy") and entry.get("focus"):
                try:
                    num = int(entry["num"])
                    sessions.append((num, int(entry["energy"]), int(entry["focus"])))
                except ValueError:
                    pass

        if not sessions:
            return ""

        # Dynamic: fit as many sessions as the panel height allows
        # Each session = 2 lines (energy bar + focus bar), plus 1 legend line
        pulse_widget = self.query_one("#pulse-chart", Static)
        panel_height = pulse_widget.size.height if pulse_widget.size.height > 0 else 12
        max_sessions = max(1, (panel_height - 1) // 2)
        sessions = sessions[-max_sessions:]

        # Bar width scales to panel width
        panel_width = pulse_widget.size.width if pulse_widget.size.width > 0 else 40
        max_bar = max(5, panel_width - 16)

        lines: list[str] = []
        for num, energy, focus in sessions:
            e_bar = "\u2588" * int(energy / 5 * max_bar)
            e_empty = "\u2591" * (max_bar - len(e_bar))
            f_bar = "\u2588" * int(focus / 5 * max_bar)
            f_empty = "\u2591" * (max_bar - len(f_bar))
            e_line = (
                f"[{LABEL_TEAL}]{num:>3}[/] [{AMBER_COLOR}]e[/] "
                f"[{AMBER_COLOR}]{e_bar}[/][{EMPTY_BAR}]{e_empty}[/] [{TEXT_TERTIARY}]{energy}[/]"
            )
            lines.append(e_line)
            lines.append(
                f"    [{WORK_COLOR}]f[/] [{WORK_COLOR}]{f_bar}[/][{EMPTY_BAR}]{f_empty}[/] [{TEXT_TERTIARY}]{focus}[/]"
            )

        return "\n".join(lines)

    def _render_log_content(self) -> str:
        work_entries = [e for e in self._today_log if e["type"] == "work"]
        hours = self.total_work_seconds // 3600
        mins = (self.total_work_seconds % 3600) // 60
        time_str = f"{hours}h {mins:02d}m" if hours else f"{mins}m"

        summary = f"[{TEXT_PRIMARY}]{time_str} \u00b7 {self.pomodoro_count} sessions[/]"
        sep_line = "\u2576" + "\u2500" * 21 + "\u2574"
        sep = f"[{SEPARATOR}]{sep_line}[/]"

        if not work_entries:
            return f"{summary}\n{sep}\n[{LABEL_TEAL}]no sessions yet[/]"

        # Dynamic: fit as many entries as the panel height allows
        log_widget = self.query_one("#log-content", Static)
        panel_height = log_widget.size.height if log_widget.size.height > 0 else 8
        max_entries = max(1, panel_height - 2)

        lines = [summary, sep]
        for entry in reversed(work_entries[-max_entries:]):
            note = entry.get("note", "")
            if len(note) > 16:
                note = note[:15] + "\u2026"
            lines.append(f"[{TEXT_SECONDARY}]{entry['start']}  {entry['duration']:>4}  {note}[/]")

        return "\n".join(lines)

    def _render_reflect_display(self) -> str:
        lines: list[str] = []

        # Note (locked)
        lines.append(f"[{LABEL_TEAL}]note     [/][{TEXT_TERTIARY}]{self._pending_note}[/]")

        if self.state in (PomodoroState.ENERGY_INPUT, PomodoroState.FOCUS_INPUT):
            if self.state == PomodoroState.ENERGY_INPUT:
                dots = f"[{EMPTY_BAR}]\u2591\u2591\u2591\u2591\u2591[/]"
                hint = f"[{DIM_COLOR}](1-5)[/]"
            else:
                filled = "\u2588" * self._pending_energy
                empty = "\u2591" * (5 - self._pending_energy)
                dots = f"[{AMBER_COLOR}]{filled}[/][{EMPTY_BAR}]{empty}[/]"
                hint = f"[{TEXT_TERTIARY}]{self._pending_energy}/5[/]"
            lines.append(f"[{LABEL_TEAL}]energy   [/]{dots}  {hint}")

        if self.state == PomodoroState.FOCUS_INPUT:
            dots = f"[{EMPTY_BAR}]\u2591\u2591\u2591\u2591\u2591[/]"
            hint = f"[{DIM_COLOR}](1-5)[/]"
            lines.append(f"[{LABEL_TEAL}]focus    [/]{dots}  {hint}")

        return "\n".join(lines)

    # ── State transitions ───────────────────────────────────────────

    def _transition(self) -> None:
        self.bell()
        if self.state == PomodoroState.WORKING:
            self._completed_session_start = self.session_start
            self._completed_elapsed = self.elapsed
            self.total_work_seconds += self.elapsed
            self.pomodoro_count += 1
            self._show_reflect()
        elif self.state == PomodoroState.ON_BREAK:
            self._log_session("break", self.session_start, self.elapsed, "", 0, 0)
            self._start_work()

    def _begin_session(self, state: PomodoroState, total: int) -> None:
        self.state = state
        self.total = total
        self.elapsed = 0
        self.session_start = datetime.now()
        self._set_aphorism()
        self._update_display()
        self._update_chrome()
        self._update_panels()

    def _start_work(self) -> None:
        self._begin_session(PomodoroState.WORKING, self.work_seconds)

    def _start_break(self) -> None:
        self._begin_session(PomodoroState.ON_BREAK, self.break_seconds)

    def _show_reflect(self) -> None:
        self.state = PomodoroState.NOTE_INPUT
        self._update_display()
        self._update_chrome()
        self._update_panels()

        panel = self.query_one("#reflect-panel")
        panel.styles.display = "block"

        # Show input row, hide display
        self.query_one("#reflect-input-row").styles.display = "block"
        self.query_one("#reflect-display", Static).update("")
        self.query_one("#reflect-display").styles.display = "none"

        note_input = self.query_one("#note-input", Input)
        note_input.can_focus = True
        note_input.value = ""
        note_input.focus()

    def _show_energy_input(self) -> None:
        self.state = PomodoroState.ENERGY_INPUT
        self._update_display()
        self._update_chrome()

        # Hide input row, show display
        self.query_one("#reflect-input-row").styles.display = "none"
        display = self.query_one("#reflect-display", Static)
        display.styles.display = "block"
        display.update(self._render_reflect_display())

    def _show_focus_input(self) -> None:
        self.state = PomodoroState.FOCUS_INPUT
        self._update_display()
        self._update_chrome()
        self.query_one("#reflect-display", Static).update(self._render_reflect_display())

    def _hide_reflect(self) -> None:
        self.query_one("#note-input", Input).can_focus = False
        self.set_focus(None)
        self.query_one("#reflect-panel").styles.display = "none"

    def _finalize_session(self) -> None:
        self._log_session(
            "work",
            self._completed_session_start,
            self._completed_elapsed,
            self._pending_note,
            self._pending_energy,
            self._pending_focus,
        )
        self._pending_note = ""
        self._pending_energy = 0
        self._pending_focus = 0
        self._hide_reflect()
        self._start_break()

    # ── Actions ─────────────────────────────────────────────────────

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        if action == "quit":
            return True
        if action == "start":
            return True if self.state == PomodoroState.IDLE else None
        if action == "pause":
            if self.state in (PomodoroState.WORKING, PomodoroState.ON_BREAK, PomodoroState.PAUSED):
                return True
            return None
        if action == "skip":
            if self.state in (PomodoroState.WORKING, PomodoroState.ON_BREAK, PomodoroState.PAUSED):
                return True
            return None
        return True

    def action_start(self) -> None:
        if self.state == PomodoroState.IDLE:
            self._start_work()

    def action_pause(self) -> None:
        if self.state in (PomodoroState.WORKING, PomodoroState.ON_BREAK):
            self.paused_from = self.state
            self.state = PomodoroState.PAUSED
            self._update_display()
            self._update_chrome()
        elif self.state == PomodoroState.PAUSED:
            self.state = self.paused_from or PomodoroState.WORKING
            self.paused_from = None
            self._update_display()
            self._update_chrome()

    def action_skip(self) -> None:
        if self.state == PomodoroState.PAUSED:
            self.state = self.paused_from or PomodoroState.WORKING
            self.paused_from = None
        if self.state in (PomodoroState.WORKING, PomodoroState.ON_BREAK):
            self.elapsed = self.total
            self._transition()

    # ── Input handling ──────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self.state != PomodoroState.NOTE_INPUT:
            return
        self._pending_note = event.value.strip()
        self._show_energy_input()

    def on_key(self, event: events.Key) -> None:
        if self.state == PomodoroState.ENERGY_INPUT:
            if event.character in "12345":
                self._pending_energy = int(event.character)
                self._show_focus_input()
                event.prevent_default()
                event.stop()
            elif event.key != "q":
                event.prevent_default()
                event.stop()
        elif self.state == PomodoroState.FOCUS_INPUT:
            if event.character in "12345":
                self._pending_focus = int(event.character)
                self._finalize_session()
                event.prevent_default()
                event.stop()
            elif event.key != "q":
                event.prevent_default()
                event.stop()

    # ── Logging ─────────────────────────────────────────────────────

    def _load_today_log(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = self.log_dir / f"{today}.md"
        self._today_log = []
        if not log_path.exists():
            return
        in_frontmatter = False
        for line in log_path.read_text().splitlines():
            if line.strip() == "---":
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                continue
            if line.startswith("|") and not line.startswith("| #") and not line.startswith("|--"):
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 8:
                    self._today_log.append(
                        {
                            "num": parts[0],
                            "start": parts[1],
                            "end": parts[2],
                            "duration": parts[3],
                            "type": parts[4],
                            "energy": parts[5],
                            "focus": parts[6],
                            "note": parts[7],
                        }
                    )
                elif len(parts) >= 6:
                    self._today_log.append(
                        {
                            "num": parts[0],
                            "start": parts[1],
                            "end": parts[2],
                            "duration": parts[3],
                            "type": parts[4],
                            "energy": "",
                            "focus": "",
                            "note": parts[5],
                        }
                    )

    def _restore_from_log(self) -> None:
        work_sessions = [e for e in self._today_log if e["type"] == "work"]
        self.pomodoro_count = len(work_sessions)
        total = 0
        for entry in work_sessions:
            dur = entry["duration"].rstrip("m")
            with contextlib.suppress(ValueError):
                total += int(dur) * 60
        self.total_work_seconds = total

    def _log_session(
        self,
        session_type: str,
        start: datetime | None,
        elapsed: int,
        note: str,
        energy: int,
        focus: int,
    ) -> None:
        start_str = start.strftime("%H:%M") if start else "??:??"
        end_str = datetime.now().strftime("%H:%M")
        duration_min = elapsed // 60
        energy_str = str(energy) if energy else ""
        focus_str = str(focus) if focus else ""

        self._today_log.append(
            {
                "num": str(self.pomodoro_count),
                "start": start_str,
                "end": end_str,
                "duration": f"{duration_min}m",
                "type": session_type,
                "energy": energy_str,
                "focus": focus_str,
                "note": note,
            }
        )
        self._write_daily_log()

    def _write_daily_log(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        log_path = self.log_dir / f"{today}.md"

        work_entries = [e for e in self._today_log if e["type"] == "work"]
        total_minutes = self.total_work_seconds // 60
        hours = total_minutes // 60
        mins = total_minutes % 60

        lines = [
            "---",
            f"date: {today}",
            "type: pomodoro-log",
            f"sessions: {len(work_entries)}",
            f"total_focus: {hours}h {mins:02d}m",
            "---",
            "",
            f"# {today}",
            "",
            "| # | Start | End | Duration | Type | Energy | Focus | Notes |",
            "|---|-------|-----|----------|------|--------|-------|-------|",
        ]

        for entry in self._today_log:
            lines.append(
                f"| {entry['num']} | {entry['start']} | {entry['end']} "
                f"| {entry['duration']} | {entry['type']} "
                f"| {entry.get('energy', '')} | {entry.get('focus', '')} "
                f"| {entry.get('note', '')} |"
            )

        log_path.write_text("\n".join(lines) + "\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def main():
    parser = argparse.ArgumentParser(description="Compos Mentis \u2014 Pomodoro Timer TUI")
    parser.add_argument(
        "-w", "--work", type=int, default=DEFAULT_WORK_MINUTES, help="Work duration in minutes (default: 50)"
    )
    parser.add_argument(
        "-b", "--break-time", type=int, default=DEFAULT_BREAK_MINUTES, help="Break duration in minutes (default: 10)"
    )
    parser.add_argument(
        "--log-dir", type=Path, default=DEFAULT_LOG_DIR, help="Directory for daily log files (default: ./logs)"
    )
    args = parser.parse_args()

    app = PomodoroApp(
        work_minutes=args.work,
        break_minutes=args.break_time,
        log_dir=args.log_dir,
    )
    app.run()
