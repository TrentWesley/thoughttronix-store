# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry — the
  log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-09-20 — Featured products, plus session log

### Prompts
Prompts 1–3 were given in earlier Claude sessions today; prompts 4–5 were given in this session.

1. "Add an is_featured Boolean field to the Product model with a default value of false."
2. "Run the migration."
3. "Show a \"Featured\" badge on featured products on both the catalog listing page and the product detail page."
4. "Append a session log to PROMPTS.md at the repo root, under today's date, newest entry at the top. Record every prompt I gave you this session, in order, including any corrections. End the entry with a short summary: the outcome, any places where I deviated from a recommended answer or asked follow-up questions, and anything that went sideways."
5. "Update today's PROMPTS.md entry to include the Featured Products prompts I gave you in the earlier Claude sessions today: [prompts 1–3]. Keep the logging prompt that is already recorded. Do not change any code."

### Summary
- **Outcome:** Prompts 1–3 correspond to the commits `67d9ba9` (add featured product field) and `0437171` (add featured product badges) on `main`. Prompts 4–5 changed only this file; no code was touched in this session.
- **Deviations:** None recorded for this session. The earlier sessions' transcripts were not available when this entry was written, so whether any recommendations were overridden or follow-up questions were asked in them is not captured here.
- **Sideways:** Nothing failed in this session. Prompts 1–3 were supplied by the user from memory of the earlier sessions, not read from a transcript. Prompt 4 was first logged on its own, and prompt 5 corrected that by adding the earlier prompts.
