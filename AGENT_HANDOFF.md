# AGENT HANDOFF

This file is for other AI/code assistants that will work on this repository.

## What this project is

This is a **sentence evidence writing support console**.
It is not a whole-document automatic writer.

The main purpose is to help a human improve writing by reviewing one sentence at a time.

## What you should optimize for

Prioritize:
- sentence-local evidence correctness
- transparent validation
- human-in-the-loop writing support
- deterministic or schema-bound behavior
- safe bounded rewrite suggestions
- sentence-targeted deepening

## What you should NOT optimize for

Do NOT drift into:
- automatic full manuscript regeneration
- donor sentence grafting
- hidden whole-document rewriting
- replacing human authorship with opaque AI rewrite behavior
- claim-level pool becoming UI truth source again

## Most important rule

### UI truth source
Use the sentence-level artifacts in `state/` as the UI truth source.

Do not use upstream claim-level shared pools as direct display truth.
Those are reference/debug sources only.

## Files you should read first

1. `README.md`
2. `ARCHITECTURE.md`
3. `server.py`
4. `public/app.js`
5. relevant `state/*.json` artifacts

## Current known limitations

1. Async retrieval worker is still simple and should be strengthened.
2. LexoRank-like inserted sentence ordering is a first pass, not a complete implementation.
3. Negative feedback contract exists, but richer reason-tag UI may still need polish.
4. Some sentence-level evidence scoring remains heuristic and may need tuning.
5. Desktop/mobile UI works, but presentation can still be refined.

## Safe next priorities

Recommended next priorities:
1. strengthen real retrieval worker quality
2. improve inserted sentence ordering edge cases
3. improve negative feedback UI reason-tag flow
4. refine sentence-local evidence scoring
5. improve recommendation/citation/transition presentation

## Testing discipline

Before claiming success:
- regenerate state artifacts if needed
- run the full pytest set
- confirm no regression in existing tests
- confirm sentence IDs remain stable
- confirm negative feedback still enforces reason-tag contract

## State files that matter most

High-value artifacts:
- `state/sentence_level_binding_deepevidence_v1.json`
- `state/sentence_level_binding_validation_v1.json`
- `state/sentence_zero_evidence_salvage_v1.json`
- `state/sentence_targeted_deepening_v1.json`
- `state/sentence_rewrite_recommendations_v1.json`
- `state/sentence_evidence_strength_labels_v1.json`
- `state/updated_sentence_level_binding_v1.json`
- `state/console_state_index.json`

## If you change a contract

If you change any sentence-level contract or state file shape:
- update tests
- update README/ARCHITECTURE if meaning changed
- preserve sentence_id stability
- keep behavior deterministic where possible
