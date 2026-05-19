# Depo-Pro Architecture

## Four-Layer Separation

Depo-Pro's data model strictly separates four layers. Mixing them is the single biggest cause of legacy transcript systems becoming unstable, and avoiding it is the most important architectural decision in this project.

### Layer 1: Intake Metadata
Who, what, when, where. Cases, parties, attorneys, sessions, reporters, reporting firms, form templates.

### Layer 2: Transcript Metadata
What happened on the record. Session events (start/break/recess), exhibits, time-on-record per attorney, interpreters, non-appearance events, transcript assets (paths to audio/video/JSON).

### Layer 3: Transcript Content (Canonical)
The words themselves, time-based and semantic. Transcript blocks → utterance segments → word objects. NEVER page-based — pagination is rendering, not truth.

### Layer 4: Export Formatting (Rendering)
How the canonical content is rendered for a target firm or format. Firm export templates, boilerplate blocks, transcript pages, transcript lines, generated outputs. This layer reads from Layers 1-3 and writes to itself — never the other way around.

## Hierarchical Data Model

Case → Sessions → Outcomes

A case can have multiple sessions (continuations, multiple witnesses, reschedules). Each session has exactly one outcome: transcript_proceeding, certified_non_appearance, cancelled, or rescheduled.

## Stack

- Frontend: HTML + CSS + JavaScript (no build step)
- Desktop shell: PyWebView
- Local HTTP server: stdlib http.server (so fetch() works for screen files)
- Backend (Phase B): FastAPI
- Database (Phase B): SQLite (json columns, not jsonb)
- AI (Phase C): Deepgram for ASR, Anthropic/OpenAI for cleanup

## Why Not Streamlit

Streamlit was the original direction. Rejected because:
- Rerun model fights stateful transcript editing
- Audio sync requires precise DOM control
- Word-style review layout is hard to achieve
- Component layout is restrictive
- Deployment friction outweighs the convenience

The HTML/PyWebView stack costs more upfront but pays for itself the first time a transcript editor needs to play audio while highlighting word-level timing.
