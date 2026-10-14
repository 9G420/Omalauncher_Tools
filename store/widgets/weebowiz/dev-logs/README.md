# DEV LOGS

Local development logs, Markdown notes and Linux diagnostics for Omalauncher. English and Traditional Chinese; language selection and agent logging instructions are in Settings at the top right.

## Features

- Browse logs by day; save them as one Markdown file per month with dated entries.
- Browse your home directory, create/view/edit Markdown, and move deleted notes to recoverable local trash after confirmation.
- Collect local diagnostics, filter Errors / Warnings / All, expand a record and copy only that report. Keeps 500 collected records.
- Copy a concise logging prompt for Codex or Claude. Your agent records meaningful changes, real verification results and unresolved problems; general replies are skipped.

DEV LOGS does not automatically capture conversations or call an AI API. Agent logging requires a local agent that saves and follows the copied project instructions. The refresh time is a display update, not an automatically generated entry.

## What Set up writes

Tap **Set up** to install the programs embedded in `widget.owl`:

- `~/.local/bin/oma-devlogs`: journal and Markdown commands.
- `~/.local/bin/oma-devlogs-terminal`: optional terminal diagnostics entry point.
- `~/.local/bin/oma-devdesk`: compatibility command for older agent rules.
- `~/.local/share/oma-devlogs/system_errors.py`: local error collector.

Creates empty `~/oma-devlogs/notes`, `journal` and `logs/terminals` folders. Existing notes and journal data are preserved; replaced programs are backed up under `~/.local/share/oma-devlogs/install-backups`. Setup does not download a script, seed sample data, change agent rules or replace the system terminal. Setup output is in `~/.cache/oma-devlogs/setup.log`.

Requires Python, bash, coreutils, gum, less, micro and foot, declared in the widget. **Update** installs new embedded helpers after a widget update.

## Data and diagnostics

Reads local widget/style errors, guest-shell stderr, existing terminal diagnostic logs and error contexts from the voice/dictation/pixel-console service logs. It does not read Android logcat, terminal screen contents or agent conversations. Diagnostics are collected on refresh while the widget is active; only the database is limited to 500 events, not the raw source logs.

Terminal logging is opt-in: run `~/.local/bin/oma-devlogs-terminal` to start `/usr/bin/foot` with stderr and abnormal-exit logging. Other terminals are not automatically recorded. Collection times may differ from event times. Severity filters are based on diagnostic text and do not establish crash causes. Nothing is uploaded automatically; inspect copied reports before sharing.

Deleted Markdown is recoverable from `~/.local/share/oma-devlogs/trash/`, with original paths saved in matching JSON files.

Source, screenshots, tests and installation instructions: [DEV LOGS](https://github.com/WeeboWIZ/Omalauncher_Tools/tree/dev-logs/dev-logs).
