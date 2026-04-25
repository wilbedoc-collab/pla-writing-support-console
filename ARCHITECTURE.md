# Architecture

## 1. Source layers

There are two different layers in this project.

### A. Upstream PLA artifacts
These come from thesis_foundry and are treated as source/reference material.
Examples:
- claim queue
- claim-level evidence binding
- key passage bank

### B. Review UI state artifacts
These are the sentence-local artifacts used by the writing support console.
Examples:
- `state/sentence_level_binding_deepevidence_v1.json`
- `state/sentence_level_binding_validation_v1.json`
- `state/sentence_zero_evidence_salvage_v1.json`
- `state/sentence_targeted_deepening_v1.json`
- `state/sentence_rewrite_recommendations_v1.json`
- `state/sentence_evidence_strength_labels_v1.json`

## 2. Truth source rule

### Primary UI truth source
The UI should use the `review_ui_v2/state/` sentence-level artifacts as the truth source.

### Secondary / debug only
Claim-level shared pools from upstream PLA are reference/debug sources only.
They should not become the primary display source again.

## 3. Processing stages

### Stage 1. Sentence cleanup / normalization
Implemented in `server.py`.
This stage fixes:
- split fragments
- section tails
- outline/table residue
- malformed sentence boundaries

### Stage 2. Sentence-level binding
Implemented by:
- `build_sentence_level_binding.py`

Produces:
- `state/sentence_level_binding_deepevidence_v1.json`

### Stage 3. Validation and strength labeling
Implemented by:
- `validate_sentence_level_binding.py`

Produces:
- `state/sentence_level_binding_validation_v1.json`
- `state/sentence_evidence_strength_labels_v1.json`

### Stage 4. Zero-evidence salvage
Implemented by:
- `salvage_zero_evidence_sentences.py`

Produces:
- `state/sentence_zero_evidence_salvage_v1.json`

### Stage 5. Targeted deepening
Implemented by:
- `deepen_sentence_evidence.py`

Produces:
- `state/sentence_targeted_deepening_v1.json`

### Stage 6. Rewrite recommendation
Implemented by:
- `build_sentence_rewrite_recommendations.py`
- `build_sentence_rewrite_options.py`

Produces:
- `state/sentence_rewrite_recommendations_v1.json`
- `state/sentence_rewrite_options_v1.json`
- `state/recommended_sentence_options_v1.json`

### Stage 7. Async refresh / candidate refresh
Implemented by:
- `build_sentence_targeted_queries.py`
- `run_sentence_targeted_retrieval.py`
- `background_sentence_retrieval_worker.py`
- `refresh_sentence_binding_candidates.py`
- `job_store.py`

Produces:
- `state/refresh_jobs_status.json`
- `state/sentence_targeted_retrieval_v1.json`
- `state/sentence_targeted_candidate_refresh_v1.json`
- `state/updated_sentence_level_binding_v1.json`

### Stage 8. Transition / citation / feedback tuning
Implemented by:
- `validate_sentence_transition_logic.py`
- `build_sentence_citation_slots.py`
- `build_validator_feedback_patch.py`
- `build_console_state_index.py`

Produces:
- `state/sentence_transition_validation_v1.json`
- `state/sentence_citation_slots_v1.json`
- `state/validator_feedback_tuning_v1.json`
- `state/scoring_patch_suggestions_v1.json`
- `state/console_state_index.json`

## 4. UI structure

### Desktop
- left pane: sentence list
- center pane: sentence detail
- right pane: evidence / recommendations / citation / transition / feedback / refutation / pending tabs

### Mobile
- sentence card list
- detail page with replaced content
- limited sheet/modal depth

## 5. Inserted sentence overlay

Inserted user sentences must remain overlay-only.
Do not renumber original sentence IDs.
Store inserted sentences separately in:
- `state/user_inserted_sentences.json`

## 6. Safety / design constraints

- no whole-manuscript auto rewrite
- no automatic sentence insertion without validation context
- no raw JSON as default UI content
- no synchronous long-running retrieval that blocks UI request/response
