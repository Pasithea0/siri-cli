---
name: siri-cli
description: Use the siri CLI to access macOS apps via Siri (notes, calendar, messages, weather, reminders, timers).
version: 1.0.0
author: Pasithea0
license: MIT
metadata:
  openclaw:
    homepage: https://github.com/Pasithea0/siri-cli
    requires:
      bins:
        - siri
    install:
      - kind: brew
        tap: Pasithea0/homebrew-siri-cli
        formula: siri-cli
        bins: [siri]
  hermes:
    tags: [macos, siri, automation, system-apps, notes, calendar, messages, weather, reminders]
    related_skills: [apple-notes, apple-reminders, macos-computer-use, macos-ax-ui-automation]
---

# Siri CLI (`siri "query"`)

Drives the **real** macOS Siri app (com.apple.campo on macOS 27) from the command line via the `siri` CLI. This lets you interact with real system apps — Notes, Calendar, Messages, Weather, Reminders, Timers/Alarms/Clock, Settings, etc. — with no third-party layers or API keys. Best replacement for tools like Notes/Calendar/Reminders CLIs when you want Siri's natural-language interface to the OS.

## When to Use

Reach for this skill whenever the user asks you to access or act on their macOS system data via natural language: **Notes, Calendar/events, Messages, Weather, Reminders, Timers/Alarms, Clock, contacts**, or Siri-style OS actions (e.g. "add a reminder", "what's on my calendar tomorrow", "set a timer"). Prefer Siri here over installing dedicated third-party CLIs (AppleScript, shortcuts hacks, etc.) — Siri gives one natural-language path to all of them at once.

## Install / verify

The dependency is the `siri-cli` Homebrew formula (official tap `Pasithea0/homebrew-siri-cli`):

```bash
brew tap Pasithea0/homebrew-siri-cli
brew trust --formula pasithea0/siri-cli   # one-time (Homebrew 6+ third-party tap)
brew install siri-cli
siri --version            # e.g. "siri, version 1.1.0"
siri status               # health check — all lines should read OK
```

`status` reports: os, siri present, accessibility, screen recording, type to siri. All must be OK. If `type to siri` or accessibility is NOT OK, the tool is missing macOS permissions — grant Accessibility (and optionally Screen Recording) to the terminal/app running `siri`, then fully quit and relaunch it.

## Usage

```bash
siri "query text here"            # single message, background by default
siri "what's the weather" --timeout 45
siri "set a 10 minute timer" --foreground   # bring Siri to front (rarely needed)
siri "..." --backend typetosiri  # fallback for macOS26 overlay (legacy; prefer default siriai on 27)
```

Default backend `siriai` is for macOS 27 (Siri AI app, full AX tree). `typetosiri` is the legacy macOS 26 overlay — mostly empty AX, avoid unless on an older OS.

## Key behavior

- **One-shot only.** Can send a single message and read the response. NO follow-ups / multi-turn / follow-on questions in the same call. (Not yet supported.)
- **Short responses only.** The CLI reads the Siri response via AX-tree text capture, so long content gets truncated (e.g. "Show More" for lists/reminders). Optimized for short answers — a time, a one-line summary, a yes/no, a count. NOT for extracting large details.
- **Background by default.** Siri stays behind the user's work; input routes without stealing focus. Use `--foreground` only if a task needs Siri visible (rare).
- Output includes the echoed query line, Siri's spoken/displayed answer, and a compact summary line.

## Pitfalls

- **Can't follow up.** If a first answer needs a follow-up question, call `siri` again with a new fully-self-contained query. Never assume Siri remembers context between calls.
- **Truncation.** Large lists (many reminders, long notes) come back cut off at "Show More". For big-content extraction, ask a narrower question, or fall back to direct app CLIs (Notes/Reminders/Calendar) instead.
- **One query per call.** Batch independent questions as separate `siri` invocations; don't chain in one string.
- **Timing.** Siri needs a few seconds to open and process. Default 30s timeout is usually fine; raise with `--timeout` for slow/network queries (weather, web lookups).
