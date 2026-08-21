# siribridge

Ask the **real macOS Siri** from your terminal and read back its actual
response. This is not a wrapper for Apple Intelligence like Apfel or a Shortcut.

```console
$ siri "what is 12 times 12"
what is 12 times 12
That would be 144.
12 × 12 =
144
```

Siri has no AppleScript dictionary, no CLI, and no stable API. The only way
to reach the *real* assistant surface is UI automation over the macOS
Accessibility (AX) framework. Prior art (`SiriSays.spoon`, `TypeToSiri`)
proved the **send** half but never the **response-capture** half. siribridge
ships the missing half: send a query, wait for the response to finish
rendering, and extract the answer text.

---

## Status

**Working today (macOS 27):** the new **Siri AI** app is a real, AX-accessible
chat application. siribridge drives it — starts a conversation, types your
query, and reads the rendered answer back from the accessibility tree.

**Not tested on macOS 26:** the old **Siri** works under the control center surface, which is not a reliable surface for accessibility control or OCR reading. 

---

## Requirements

- **macOS 27** (Tahoe+ with the new "Siri AI" app)
- Apple Silicon or Intel
- Python 3.11+

---

## Install

From source:

```bash
git clone https://github.com/you/siribridge.git
cd siribridge
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

This installs the `siri` command into your virtualenv. To use it anywhere,
keep the venv active or add it to your `PATH`:

```bash
# optional: make `siri` available globally
ln -s "$(pwd)/.venv/bin/siri" /usr/local/bin/siri
```

---

## Configure permissions (required once)

siribridge needs macOS permissions to read and drive the Siri AI app. You
must grant these **to the terminal/app that runs `siri`** (Terminal, iTerm,
your IDE, or the shell you invoke it from).

1. **Accessibility** (required) — lets the tool read and control the Siri AI
   app's UI.
   `System Settings → Privacy & Security → Accessibility →` enable your terminal/app.

2. **Screen Recording** (required for `siri status` and OCR fallback) —
   `System Settings → Privacy & Security → Screen Recording →` enable your terminal/app.

3. **Siri enabled** — the Siri AI app must be installed and signed in
   (`System Settings → Apple Intelligence & Siri`).

> Permissions are cached by macOS. After granting, fully quit and relaunch
> your terminal so the grant takes effect.

Verify everything is ready:

```console
$ siri status
os: 27.0
siri present: True
accessibility: OK
screen recording: OK
type to siri: OK
```

`exit 0` means you're good to go:

```console
$ siri health
ok
```

---

## Usage

### Ask Siri (primary)

Pass a query as bare words or in quotes:

```bash
siri "what time is it"
siri what time is it
siri "what is the capital of Japan"
```

**Background by default.** Siri AI stays behind whatever you're working in —
it never steals focus, so you can keep typing in your terminal/editor while
Siri answers in the background. The captured response is printed to stdout.
The command exits `0` on success, non-zero on a permissions/surface/capture
error.

### Options

```bash
siri --foreground "query"       # bring Siri to the front (default is background)
siri --background "query"       # explicit: keep Siri behind your work (default)
siri --backend siriai "query"   # default: siriai (macOS 27 Siri AI app)
siri --backend typetosiri "query"   # macOS 26 overlay (best-effort - untested)
siri --timeout 45 "query"       # max seconds to wait (default 30)
```

### Diagnostics

```bash
siri status      # permission + environment check
siri health      # exit 0 if ready
siri --version   # version
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0`  | Success (or health ok / status all-green) |
| `1`  | Missing permission, surface not available, or capture timed out |

---

## How it works

```
siri "query"
  -> SiriAiBackend  (foreground=False by default)
       -> find Siri AI app (pid); launch if needed, never front it
       -> press "New Conversation"  (AXButton via AXPress — focus-free)
       -> set composer AXTextField value + AXConfirm  (no focus dependency)
       -> poll the AX tree until the response stops changing
       -> filter app chrome / menu noise, print the answer
```

Key design choices:

- **Background by default** — Siri AI is never brought to the front unless
  you pass `--foreground`. New conversation, typing, and reading all go
  through Accessibility, so they work while your terminal/editor is the
  frontmost app.
- **AXPress "New Conversation"** (not the Cmd+N keystroke) — the keystroke
  only lands if the app is frontmost; AXPress works regardless of focus.
- **No `osascript activate`** — activating the app steals focus from your
  work and is unnecessary since everything is AX-driven.
- **AX-composer input** — we set the composer's `AXValue` and call its
  `AXConfirm` action directly, which works no matter which app is frontmost.
- **Window-scoped AX extraction** — we read only the Siri AI window's AX
  tree, not the process-wide tree (which includes the macOS menu bar and
  Finder submenus), then filter out known UI chrome.
- **Settle detection** — we poll until the response text is stable across
  consecutive reads, so we capture the finished answer, not a partial one.

### Project layout

```
src/siribridge/
  cli.py              CLI entrypoint (bare query + status/health)
  config.py           permission + environment checks
  state.py            settle-detection state machine
  capture/
    ax.py             AX tree walking + text extraction
    ocr.py            Vision OCR fallback (macOS 26)
  driver/
    base.py           backend interface + SiriResponse
    siriai.py         macOS 27 Siri AI backend (recommended)
    typetosiri.py     macOS 26 overlay backend (best-effort)
tests/                pytest suite
```

---

## Development

```bash
# run tests
source .venv/bin/activate
pytest -q

# run a live query
siri "what time is it"
```

### Roadmap

- [x] macOS 27 Siri AI backend with response capture
- [x] Bare `siri "query"` CLI
- [ ] macOS 27 rich-card image capture (OCR / screenshot region)
- [ ] `brew` formula / `.app` packaging

---

## License

MIT. See `LICENSE`.
