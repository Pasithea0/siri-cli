# siribridge

Bidirectional **C**omputer-**U**se-**A**utomation bridge to the real macOS Siri.

Ask the actual Siri (the `SiriNCService` overlay on macOS 26, the new Siri AI
app on macOS 27) from a **CLI** or an **MCP server**, and **capture the
response** — not just fire-and-forget commands.

## Why

Siri has no AppleScript dictionary, no CLI, and no stable API. The only way to
reach the *real* assistant surface is UI automation (Accessibility / CUA).
Prior art (`SiriSays.spoon`, `TypeToSiri`) proved the **send** half but never
the **response-capture** loop. This project ships the missing half: send a
query, wait for the response to settle, extract the rendered text (AX tree,
with Vision OCR fallback for rich cards).

## Status

Phase 0 — scaffolding & permissions. Not functional yet.

## Architecture

```
Agent (Hermes/Claude/etc.)
  -> siri CLI | MCP server  (ask(query) -> {text, images, backend, ms})
       -> driver backend (AX + CGEvent / CuaDriver)
            -> Siri / Spotlight UI -> Siri brain
```

- **Type-to-Siri backend** (`driver/typetosiri.py`): proven path, works on macOS 26 today.
- **Spotlight backend** (`driver/spotlight.py`): future path for macOS 27 Siri AI integration.

Both feed the same settle-detection + AX-extraction + OCR-fallback pipeline.

## Install (dev)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Dependencies

- `pyobjc-framework-ApplicationServices` — AX tree + CGEvent + Quartz
- `pyobjc-framework-Vision` — OCR fallback for rich cards
- `mcp` — MCP server SDK
- `click` — CLI
- `pytest` — tests (TDD against fixture AX trees/screenshots)

## License

MIT. See `LICENSE`.
