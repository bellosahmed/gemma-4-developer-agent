# Ideas and workflow improvements

Written 2026-10-15 while GPU quota was exhausted (refills 2026-10-17 00:00 UTC). Everything below is grounded in recorded runs
(`EXPERIMENT_LOG.md`, `findings/`). "Status" says whether it is built, queued or only an idea.

## 1. What the data says (these shape every choice)

1. **The measuring stick is weak.** Of the 19 valid sample tasks, **12 were never solved in 9 runs, 2 always were, only 5 ever change outcome**
   (`scripts/task_stats.py`). No experiment is statistically significant (best paired sign-test p = 0.25: Exp 7 and combo02, 3 gained / 0 lost).
2. **Time, not context or reasoning quality, is the binding limit.** 8-11 of 20 tasks end by timeout at ~60 tokens/s; many end with an empty patch.
3. **The graph tools were ignored** (0.5% of calls) until Exp 7 forced them (5.7%, used in 18/20 tasks) - the best single change so far.
4. **The agent rarely verifies:** 2 `pytest` calls in 40 runs. `read_file` is 51% of calls and 37% of time; `edit_file` waits average 32 s.
5. **Gains so far are all prompt-level and consistent in direction** (Exp 4, 6, 7 and combo02 all gain `fastapi_14372`, `rich_2725`/`rich_3718`).
6. **12 of 19 sample tasks are currently unsolved**: 9 fastapi, 2 rich, 2 requests. Most upside is there, and it is invisible at n=19.

## 2. Workflow improvements

| Improvement | Why | Status |
|---|---|---|
| **Concurrency inside one Kaggle session** (`"concurrency": N` in a spec; N tasks share one model server) | Decode is memory-bound, so batching N streams should give ~N x throughput: a 20-task run drops from ~3.4 GPU-h to ~1.2 and validation from ~9 to ~3. Verified safe locally (`scripts/test_concurrency.py`); fidelity on the model side unverified. | Built; **pilot queued** (`pilot_conc3`) |
| **Save every agent patch** (`patches/<id>.patch`) + test-output tail | Lets us measure localization (did it edit the right file/function?), a far finer signal than pass/fail; also debugging. | Built (new runs) |
| **Paired significance test + per-task pass-rate table** | Stops us over-claiming from 1-3 flipped tasks. | Built (`compare.py`, `task_stats.py`) |
| **Spec-driven experiments** (`experiments/*.json` merged onto a base) | One change per experiment, reproducible, no hand-edited notebooks. | Built (`make_exp.py`) |
| **Build the submission from the notebook's own code** (`build_submission.py`) | What we submit is exactly what we measured. | Built |
| **Robust output fetch** (`fetch_output.sh`) | Kaggle sometimes returns 502 HTML saved under real names. | Built |
| **Informative-task evaluation set** | After the 51-task validation, re-use only mixed-outcome tasks (+ a few never-solved) for fast iteration; confirm on a held-out remainder to avoid winner's-curse bias. | Idea (needs validation data) |
| **Repeat the best config** to measure run-to-run noise | Tells us what a 1-task difference means. Cheap if concurrency works. | Idea |
| **Use the daily leaderboard submission as an experiment** | It scores the real hidden set; ~45 days x 1 submission = the most reliable signal we have. Alternate candidates; keep 2 finals. | In use |

## 3. Agent ideas (backlog, ordered by expected value / cost)

| # | Idea | Evidence / reasoning | Spec | Cost (20 tasks) |
|---|---|---|---|---|
| A | **31B model** instead of 12B | Never tested. Model card: 31B beats 12B on coding/agentic benchmarks (LiveCodeBench v6 80.0 vs 72.0, Tau2 76.9 vs 69.0). Risk: slower per token under a 5-minute cap. The sample submission itself defaults to 31B. | `exp08_model31b` | ~3.5-4 GPU-h |
| B | **Deadline awareness**: use the free `get_status` to switch to "apply best fix and submit" when <100 s or <8 calls remain | 8-10 of 20 tasks time out, many with empty patches; any attempt beats none. | `exp09_deadline` | ~1.2 (conc 3) |
| C | **Gemma's recommended sampling** (temp 1.0, top_p 0.95, top_k 64) vs the sample's 0.2 | Model card recommends it; our traces show repetitive "Wait" loops at 0.2. Risk: noisier tool calls. | `exp11_temp` | ~1.2 |
| D | **Strip past thoughts from history** (`include_thoughts: false`) | Smaller prompts: less prefill, fewer context errors; thoughts are re-derived anyway. Risk: loses plan continuity. | `exp10_nothoughts` | ~1.2 |
| E | **Edit from search results** instead of re-reading | `read_file` = 51% of calls / 37% of time; graph tools already return exact source. | `exp12_editfromsearch` | ~1.2 |
| F | Require **one verification run** of the target test when it can run | 2 pytest calls in 40 runs. Conflicts with the sandbox-gap prompt; test as a variant. | idea | ~1.2 |
| G | **Fewer, larger reads** (use the full 150-line window) | Each read costs a model round trip. | idea | ~1.2 |
| H | **Task-type prompts** (tutorial `docs_src/` tasks, rich exact-output tests) | Cheat sheets alone were neutral (Exp 5) but targeted rules may differ. | idea | ~1.2 |
| I | `thinking_budget` higher (6144) for the edit step only | Exp 2 showed less thinking hurts; more might help. Output cap is 8192 so the room is limited. | idea | ~1.2 |
| J | Multi-agent chain (Localize -> Fix -> Verify sub-agents) | Clean contexts per stage. Risk: the harness re-prompts and may restart the chain; not tried. | idea | higher |
| K | Best-of-N with test-based selection | Not feasible at 5 min/task and ~60 tok/s. Revisit only if A (31B) or concurrency changes the time picture. | rejected for now | - |
| L | LoRA fine-tune | Only 6 distinct solved tasks, all in the eval sample; quantized base mismatch. | rejected (see log) | - |

## 4. Run plan after the quota refill (30 GPU-h)

Two GPU sessions at a time. Costs are estimates: concurrency fidelity is unproven.

1. **Session 1: `pilot_conc3`** (best prompt, 20 tasks, 3 at once, ~1.5 h). Compare per-task seconds/tool calls with `exp07` (sequential). If similar, use concurrency from here on.
   **Session 2: `exp08_model31b`** (~4 h, sequential): the biggest untested lever.
2. If concurrency holds: run B, C, D, E (~1.2 h each, ~5 h total), two at a time.
3. Validate the best 1-2 candidates on the 51 valid sound tasks (`val51_exp07`, `val51_combo02`, plus any new winner): ~3 h each with concurrency, ~9 h without.
4. Submit the best by leaderboard + validation; keep 2 finals.
Budget check (no concurrency): 4 + 3.4 + 4 x 3.4 + 2 x 9 = ~39 h > 30 h, so concurrency (or dropping experiments) is needed. Priority if it fails: A, B, validation of Exp 7.

## 5. Competition-level options (user decisions, not done)

- **Paper track** (separate competition, $35k, deadline 2026-11-12): our findings are paper-sized and original - the vacuous/unsound task audit (52/129 sound, 1 vacuous), the graph-tool non-use finding (0.5% -> 5.7% with a one-paragraph prompt), the time-bound analysis, and the experiment methodology. Requires joining that competition and accepting its rules; shared code must go on Kaggle, not GitHub.
- **Team merger** (deadline 2026-11-25, max 5): merging pools GPU quota. Rules: no private sharing outside a team; combined submission count must fit the daily limit. Only worth it with someone who can contribute runs.
- Watch the competition forum for host announcements about the scoring environment (Python 3.12 vs 3.13, missing wheels such as `inline_snapshot`/`dirty_equals`).
