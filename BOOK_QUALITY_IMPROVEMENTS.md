# Book Quality Improvement Plan

## Current Pain Points
- **[Tag mismatch breaks gating]** `book_generator.generate_chapter()` instructs agents to use `SCENE`/`SCENE FINAL`, while `_verify_chapter_complete()` still looks for `PLAN`, `SETTING`, and a confirmation message that no agent emits. This causes false "incomplete" flags and lets short drafts through.
- **[Length requirement unenforced]** `agents.py` tells the writer/editor to hit 5000 words, but `_verify_chapter_content()` only checks for a header plus two lines, so chapters end ~400 words.
- **[Premature endings slip in]** `book_output/chapter_01.txt` already ends with "The End" despite being chapter 1, violating the guardrails in `book_generator.generate_chapter()`.
- **[Outline parsing fragility]** `_process_outline_results()` in `outline_generator.py` hunts for `Title:` even though `outline_creator` writes `Chapter Title:`, leading to emergency placeholders and weak chapter prompts.
- **[Uniform LLM config]** All agents share one temperature/time-out in `config.py`, so planners are too random and editors too lenient.
- **[Duplicate helper]** `model_presets.py` defines `get_model_by_preset_key()` twice, making maintenance error-prone.

## High-Impact Fixes (Skippable Refactors Later)
- **[Align chapter tags]** Update `book_generator.generate_chapter()` instructions and `_verify_chapter_complete()` to expect `SCENE`, `FEEDBACK`, `EDITED_SCENE`, `SCENE FINAL`, and drop the unused `SETTING`/confirmation gates.
- **[Enforce minimum length]** Add a configurable `MIN_CHAPTER_WORDS` check in `_verify_chapter_content()`; bounce short drafts back to the `editor` with an "EXPAND" instruction.
- **[Block early endings]** Fail `_verify_chapter_content()` when a non-final chapter contains `The End`, `Epilogue`, etc., and instruct the writer to continue.
- **[Improve outline parsing]** Accept `Chapter Title:` and ensure ≥3 bullet `-` events per chapter before approving the outline.
- **[Increase collaboration rounds]** Raise `max_round` to 6–8 for both outline and chapter chats so agents can iterate without falling back to placeholder logic.
- **[Remove duplicate preset helper]** Keep a single `get_model_by_preset_key()` in `model_presets.py`.

## Structural Enhancements for Richer Chapters
- **[Scene-driven workflow]** Require each chapter outline to list ≥3 scenes. Have `writer` produce scene stubs, flesh them out to ~900 words, then concatenate for editing.
- **[Story bible memory]** Extend `BookAgents` to persist structured `MEMORY UPDATE` blocks (characters, continuity, timeline) and feed them into `writer` prompts via `_prepare_chapter_context()`.
- **[Style anchoring]** Add a reusable "style card" (voice, POV, pacing, taboo phrases) injected into `writer` and `editor` system prompts across `agents.py`.
- **[Editor gatekeeper]** Force `editor` to output `FEEDBACK:` plus a full `EDITED_SCENE:` and only allow `writer_final` to emit `SCENE FINAL:` after feedback items are addressed.
- **[Act & tension cues]** Expand outline prompts so every chapter includes act placement, stakes, and target tension level; have the editor verify scene beats against these cues.

## Reliability & Workflow Improvements
- **[Per-agent configs]** Let `run_generation()` build phase-specific configs: outline agents at temperature ≤0.4, writer around 0.7, editor ≤0.3, with longer timeouts for chapter drafting.
- **[Retry strategy]** When generation fails, retry with a single high-quality prompt that includes outline + previous context, instead of reducing to a minimalist fallback.
- **[Long output chunking]** For models with context limits, generate `Part 1/3`, `Part 2/3`, etc., each reviewed by the editor before merging.
- **[UI quality modes]** Add a "Quality mode" toggle in `pages/1_Generate.py` (Fast, Standard, Deluxe) that adjusts min words, step count, and per-agent configs.
- **[Progress visibility]** Surface per-chapter status (Drafting, Editing, Expanding) in the Streamlit logs so users can monitor loops.

## Outline Quality Upgrades
- **[Outline rubric]** Update `outline_creator` instructions to record stakes, conflicts, turning points, named characters, and cliffhangers per chapter.
- **[Verification hook]** After outline generation, run a quick validator that checks for missing headings, insufficient bullets, or placeholders before saving.

## Suggested Implementation Order

1. **[Stabilize chapter gating]** Align tags, length checks, and premature-ending guards in `book_generator.py` and `agents.py`.
2. **[Strengthen outline parsing]** Improve `_process_outline_results()` and raise chat rounds.
3. **[Introduce story bible]** Persist memory updates and feed them back into chapter context building.
4. **[Scene-by-scene drafting]** Enforce scene counts and editor gating.
5. **[Quality modes & configs]** Add per-phase temperature/timeouts and expose toggles in the UI.
6. **[Advanced polish]** Layer on chunked drafting, retry upgrades, and expanded outlines once the core pipeline is stable.

## Notes for Future Work
- **[Testing]** Add targeted pytest cases to cover outline parsing, chapter length validation, and detection of premature endings.
- **[Documentation]** Update `README.md` to explain new quality modes and minimum-length behavior.
- **[Model selection UI]** Consider surfacing the per-agent temperature/timeouts in an advanced settings accordion for power users.
