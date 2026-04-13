.PHONY: focus focus-dev focus-btop sync test clean

# ── Pomodoro ───────────────────────────────────────────────
focus:
	cd pomodoro && uv run compos-mentis $(ARGS)

focus-dev:
	cd pomodoro && uv run compos-mentis -w 1 -b 1 $(ARGS)

focus-btop:
	cd pomodoro && uv run compos-mentis -w 1 -b 1 $(ARGS)

sync:
	cd pomodoro && uv sync

test:
	cd pomodoro && uv run pytest

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .mypy_cache .ruff_cache dist *.egg-info
