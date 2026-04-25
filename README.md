# PLA Writing Support Console

PLA Writing Support Console is a sentence-level evidence review and writing support system.

It is **not** an automatic lecture writer.
It is a console that helps a human improve writing by:
- reviewing sentences one by one
- validating whether attached evidence is appropriate
- showing warnings, salvage actions, and rewrite directions
- supporting sentence-targeted evidence deepening
- proposing citation placement and local flow checks

## Core idea

The system treats each sentence as a unit of:
- evidence binding
- validation
- salvage
- deepening
- rewrite recommendation
- feedback

The UI is designed so a human can inspect one sentence, see why it passes or fails, and decide what to do next.

## Current capabilities

- sentence-level evidence binding artifact
- sentence-level validation contract
- zero-evidence salvage routing
- sentence-targeted deepening packet
- rewrite recommendation generation
- sentence-targeted retrieval job contract
- inserted sentence overlay storage
- transition validation
- citation slot suggestion
- validator feedback tuning artifacts
- desktop/mobile review UI

## Important philosophy

This project should stay a **writing support console**, not drift back into an automatic whole-document rewriting system.

### Non-goals
- whole manuscript auto rewrite
- donor sentence grafting
- unvalidated automatic insertion
- hidden raw JSON as primary UI
- synchronous long-running UI blocking actions

## Run

### Local server
```bash
python3 server.py
```

### Open in browser
- local network: `http://10.0.0.2:8765/index.html?v=20260423b`
- tailscale/private if available: `http://100.87.32.74:8765/index.html?v=20260423b`

## Tests

Run with:
```bash
python3 -m pytest -q ../tests/
```

## Main entry points

- `server.py` — API + static server
- `public/app.js` — UI behavior
- `public/index.html` — UI shell
- `state/` — generated artifacts used by the UI

## For other AI/code assistants

Before modifying code, read:
- `ARCHITECTURE.md`
- `AGENT_HANDOFF.md`
