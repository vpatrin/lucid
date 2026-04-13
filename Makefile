.PHONY: focus focus-dev lint format sync test clean install

# ── Pomodoro ───────────────────────────────────────────────
focus:
	cd pomodoro && uv run compos-mentis $(ARGS)

focus-dev:
	cd pomodoro && uv run compos-mentis -w 1 -b 1 $(ARGS)

lint:
	cd pomodoro && uv run ruff check src/ && uv run ruff format --check src/

format:
	cd pomodoro && uv run ruff format src/ && uv run ruff check --fix src/

sync:
	cd pomodoro && uv sync

test:
	cd pomodoro && uv run pytest

install:
	git config core.hooksPath .githooks
	cd pomodoro && uv sync

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .mypy_cache .ruff_cache dist *.egg-info
