# cph-compile-stuck - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST, after the detailed plan below is written, so it summarizes the REAL plan. -->
<!-- Plain English for a non-engineer: NO file paths, NO todo numbers, NO wave/agent/tool names. -->

**What you'll get:** The plugin's compile process no longer hangs indefinitely at "COMPILING"; settings conflicts between compile_cmd, run_cmd, and std version are resolved; ProcessManager compile deadlock risks and broken run guards are fixed; status labels are consistent.

**Why this approach:** Direct file-level fixes with minimal scope (only settings + ProcessManager + test_manager flow lines), agent-executed verification of syntax/settings, and explicit no-deepseek subagent constraint.

**What it will NOT do:** Change external build systems (g++ installation), modify phantom/display logic, add new languages, commit git changes without explicit request, or use deepseek subagents.

**Effort:** Short
**Risk:** Low — localized file edits; no external dependency changes; all changes are reversible.
**Decisions to sanity-check:** (1) Changing `-std=c++23` back to `-std=c++11` in settings (aligns with README); (2) Changing `compile_cmd` output to include `.exe` explicitly; (3) Changing `compile()` stdin from PIPE to None/DEVNULL to prevent hang.

Your next move: Execute the todos below (or delegate to a worker session via `$start-work cph-compile-stuck`).

---

> TL;DR (machine): Short / Low risk / Fix settings mismatch (compile_cmd/run_cmd/std) + ProcessManager compile hang/deadlock + test_manager status label consistency. Agent-executed syntax/settings QA only; no deepseek; no git commit.

## Scope
### Must have
- Fix `cph-by-chenkx (Windows).sublime-settings`: `compile_cmd` output alignment with `run_cmd`, `-std=c++11` alignment.
- Fix `ProcessManager.py`: `compile()` stdin hang risk, `run_file()` broken `is_run` guard (`and False`), robust `compile()` return for `cmd == -1`.
- Fix `test_manager.py`: `COMPILE` -> `COMPILING` status consistency; verify `cmp_data` None handling in compile callback.
- Agent-executed QA for edited files (syntax check, settings JSON validity, no `deepseek` subagent).

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No external build system changes.
- No phantom/display logic changes beyond status label strings.
- No new languages or settings structure changes.
- No git commit without explicit user request.
- No `deepseek` subagent (user explicitly requested `minimax M3/free` or `lnkling/free` only).

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after + agent-executed syntax/settings validation (no human QA required for syntax; manual verification only for functional behavior which requires Sublime runtime).
- Evidence: `.omo/evidence/` artifacts for syntax checks (`python -c` or `python -m py_compile`) and JSON parse (`python -c` with `json.load`).
- Each todo has happy + failure QA with exact command invocation recorded.

## Execution strategy
### Parallel execution waves
> Wave 1: Settings fix (independent, quick edit + syntax validation). Wave 2: ProcessManager flow fix (depends on settings alignment for compile output reference, but code fix is independent). Wave 3: test_manager status fix + final integration QA. Waves can overlap partially but QA for each depends on the file edit being done.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. Settings fix | None | 2 (compile output reference) | 2 |
| 2. ProcessManager compile/run fix | 1 (output reference for verification) | 3 (integration test) | 1 |
| 3. test_manager status/fix + final QA | 2 | None (final) | 1, 2 (after their edits) | --- |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [ ] 1. Fix `cph-by-chenkx (Windows).sublime-settings` compile/run alignment and std version.
  What to do / Must NOT do: Update `compile_cmd` to `-o "{file_name}.exe"` (explicit `.exe`), change `-std=c++23` to `-std=c++11`, keep `-DLOCAL`. Do NOT change settings structure or add new languages. Do NOT use `deepseek` subagent for this or any verification.
  Parallelization: Wave 1 | Blocked by: None | Blocks: 2
  References (executor has NO interview context - be exhaustive): `cph-by-chenkx (Windows).sublime-settings`:31-39 (`compile_cmd`, `run_cmd`), README.md:158 (`-std=c++11` reference).
  Acceptance criteria (agent-executable): `python -c "import json; json.load(open('cph-by-chenkx (Windows).sublime-settings'))"` exits 0. `compile_cmd` contains `.exe` in output and `-std=c++11`.
  QA scenarios (name the exact tool + invocation): happy: `python -c "..."` passes with exit 0. failure: JSON syntax error caught by parse exception; evidence `.omo/evidence/task-1-cph-compile-stuck.json`
  Commit: N

- [ ] 2. Fix `ProcessManager.py` compile deadlock, broken is_run guard, and compile return handling.
  What to do / Must NOT do: Change `compile()` `stdin=PIPE` to `stdin=None` (or `subprocess.DEVNULL`) to prevent hang; fix line 155 `if self.is_run and False:` to `if self.is_run:`; handle `cmd == -1` explicitly in compile (return error immediately, not pass to Popen). Do NOT change phantom/display logic. Do NOT commit.
  Parallelization: Wave 2 | Blocked by: 1 (for output reference verification) | Blocks: 3
  References: `Modules/ProcessManager.py`:106-152 (`get_compile_cmd`, `compile`), 154-192 (`run_file`, `is_run` guard broken at 155).
  Acceptance criteria: `python -m py_compile Modules/ProcessManager.py` exits 0. `compile()` has `stdin` not equal to `PIPE`; line 155 does not contain `and False`.
  QA scenarios: happy: `python -m py_compile` passes. failure: syntax error reported by py_compile; evidence `.omo/evidence/task-2-cph-compile-stuck.py`
  Commit: N

- [ ] 3. Fix `test_manager.py` COMPILE -> COMPILING status consistency and compile callback robustness.
  What to do / Must NOT do: Change `self.on_status_change('COMPILE')` at line 446 to `'COMPILING'`; verify `cmp_data` is handled safely when `None` in compile callback (line 1143). Do NOT change phantom/display logic beyond status string. No `deepseek` subagent.
  Parallelization: Wave 3 | Blocked by: 2 | Blocks: None
  References: `test_manager.py`:443-461 (`run_test` with `'COMPILE'`), 1011-1155 (`make_opd`, compile callback with `COMPILING` / `COMPILED`), 1019-1024 (`compiling_since` guard).
  Acceptance criteria: `python -m py_compile test_manager.py` exits 0. Line 446 contains `'COMPILING'`. Line 1143 handles `cmp_data` safely (e.g., `if cmp_data is not None and cmp_data[0] == 0:` rather than bare `cmp_data[0] == 0`).
  QA scenarios: happy: syntax passes, string search confirms `'COMPILING'`. failure: syntax error or incorrect status label; evidence `.omo/evidence/task-3-cph-compile-stuck.py`
  Commit: N

- [ ] F1. Plan compliance audit
  Acceptance: Every todo has references with file paths and lines, agent-executable criteria, happy+failure QA, and no `deepseek` usage. Plan headers match template order. No missing `TL;DR` content.

- [ ] F2. Code quality review (agent-executed)
  Acceptance: Edited Python files pass `python -m py_compile`; settings JSON is valid; no `and False` anti-pattern remains; `stdin` is not `PIPE` in compile; `compile_cmd` aligns with `run_cmd`.

- [ ] F3. Settings / syntax verification
  Acceptance: Settings file loads without error; compile command produces `.exe`; `run_cmd` can reference `.exe` without mismatch.

- [ ] F4. Scope fidelity
  Acceptance: Only `ProcessManager.py`, `test_manager.py`, and settings file edited. No phantom/display logic changes. No external build system changes. No deepseek subagent used.

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.
- [ ] F1. Plan compliance audit (see todo above)
- [ ] F2. Code quality review (agent-executed)
- [ ] F3. Settings / syntax verification (agent-executed)
- [ ] F4. Scope fidelity (agent-executed)

## Commit strategy
No automatic git commit included. Each edit is reversible (file-level). User must explicitly request commit (`git commit`) if they want the changes tracked. Evidence artifacts (`.omo/evidence/`) are not committed by this plan.

## Success criteria
- Settings file is valid JSON; `compile_cmd` produces `.exe`; `run_cmd` references `.exe` without mismatch; `-std=c++11` is used.
- `ProcessManager.py` passes `python -m py_compile`; `compile()` has `stdin` not `PIPE`; `run_file()` line 155 does not contain `and False`.
- `test_manager.py` passes `python -m py_compile`; `run_test()` line 446 uses `'COMPILING'`; compile callback handles `None` return safely.
- No `deepseek` subagent was invoked for any verification (confirmed by agent session logs or user verification).
- Scope fidelity verified: only the three files above edited; no display/phantom logic changed; no external build system changed.
