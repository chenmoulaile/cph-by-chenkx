---
slug: cph-compile-stuck
status: awaiting-approval
intent: clear
review_required: false
pending-action: write .omo/plans/cph-compile-stuck.md
approval_granted: true
approval_timestamp: 2026-09-05T13:14:00
approach: Fix settings conflicts + ProcessManager compile flow defects + test_manager COMPILE/COMPILING inconsistency. No external dependency changes; agent-executed QA included; no deepseek subagent allowed (user request: use minimax M3/free or lnkling/free only).
---

# Draft: cph-compile-stuck

## Components (topology ledger)
- C1 | Compile/get-stuck fix: ProcessManager compile timeout/deadlock + settings fix | active | ProcessManager.py:128-152, test_manager.py:1011-1155
- C2 | Settings mismatch fix: compile_cmd/run_cmd output name + std version | active | cph-by-chenkx (Windows).sublime-settings:31-33
- C3 | Flow/status consistency: COMPILE vs COMPILING, is_run guard, stdin=PIPE | active | ProcessManager.py:154-192, test_manager.py:443-461, 1014-1155

## Findings (cited - path:lines)
- ProcessManager.compile() line 128: uses `subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT, ...)`. `stdin=PIPE` can hang if compiler tries to read stdin (low probability but present). Timeout at 30s (line 143) kills via `p.kill()`; exception handled (line 151). Returns `(returncode, output)`.
- ProcessManager.compile() line 106-115: `get_compile_cmd()` returns `-1` if no matching extension found; `compile()` treats `cmd is not None` so `-1` passes through to Popen, which will throw exception (line 152 returns error) — not a hang but incorrect behavior.
- ProcessManager.run_file() line 154-191: `self.is_run = False` (line 159) resets before running; line 155 `if self.is_run and False:` is always False — the guard is broken and never prevents double-run.
- ProcessManager.compile() output: settings file uses `-o "{file_name}"` (line 31), but `run_cmd` expects `"{source_file_dir}\\{file_name}.exe"` (line 33). On Windows `g++ -o filename` produces `filename.exe`, so `run_cmd` referencing `.exe` is actually correct; however the compile command does not include `-O2` or any optimization, and uses `-std=c++23` which may conflict with user code expecting `c++11` per README.
- test_manager.py line 1014: `self.change_process_status('COMPILING')`. Line 1143: `self.change_process_status('COMPILED')`. But `run_test()` line 446 uses `'COMPILE'` instead of `'COMPILING'`, creating status inconsistency.
- test_manager.py line 1019-1024: stale `COMPILING` guard uses `compiling_since` attribute; clears after 30s — this is a partial fix added previously but does not solve the underlying hang.
- test_manager.py line 1132-1155: compile runs in `compile()` callback via `sublime.set_timeout_async(compile, 10)`; finally block always sets `self.compiling_since = None` and `self.change_process_status('COMPILED')`, which is correct, but if `cmp_data` is `None` (Python, no compile needed) line 1143 tries `cmp_data[0] == 0`, which evaluates correctly since `None == 0` is False, but the code structure is fragile.
- cph-by-chenkx (Windows).sublime-settings line 8: `lint_enabled: true`; if `lint_compile_cmd` is called and conflicts with `compile_cmd`, could cause double compilation or conflicting commands. `lint_compile_cmd` uses `-I` and `-DLOCAL` but no `-o`, so it doesn't produce an executable — safe but could add time.
- cph-by-chenkx (Windows).sublime-settings line 31: `compile_cmd` uses `-std=c++23` and `-DLOCAL`; README line 158 shows `-std=c++11` and no `-DLOCAL`. This mismatch is a potential source of compilation errors for older code.

## Decisions (with rationale)
- Fix `compile_cmd` to match `run_cmd`: add `.exe` explicitly in `-o` to avoid ambiguity (`-o "{file_name}.exe"`), or adjust `run_cmd` — but user wants C option (both settings + flow), so we fix `compile_cmd` to explicitly output `.exe` and align std version.
- Fix `is_run` guard in `run_file()` line 155: remove `and False` so the guard works (`if self.is_run:`).
- Fix `compile()` deadlock risk: keep timeout but add `p.communicate()` with input='' or avoid `stdin=PIPE` for compile (compilers don't need stdin). Change `stdin` to `subprocess.PIPE` but don't write to it — actually `Popen` with `stdin=PIPE` without writing can hang if compiler reads; better to use `stdin=None` or `subprocess.DEVNULL` for compile. This is a safety improvement.
- Fix `run_test()` line 446: change `'COMPILE'` to `'COMPILING'` to match `make_opd()` line 1014.
- Fix `compile_cmd` standard: change `-std=c++23` back to `-std=c++11` (or match README recommendation) to prevent CE on code written for c++11.
- Fix settings: `lint_compile_cmd` should not conflict; verify it does not override compile behavior. Since `lint_enabled` is separate, no change needed unless user reports lint conflicts.

## Scope IN
- Modify `ProcessManager.py`: compile() stdin/deadlock guard, is_run guard, return value handling.
- Modify `test_manager.py`: `COMPILE` -> `COMPILING` status consistency; verify `cmp_data` None handling is robust.
- Modify `cph-by-chenkx (Windows).sublime-settings`: `compile_cmd` output name alignment (`.exe`), `-std=c++11` alignment.
- Agent-executed QA: run compile simulation (if possible) or verify syntax of edited Python; verify settings JSON validity.

## Scope OUT (Must NOT have)
- Do NOT change external build systems (no `g++` installation changes).
- Do NOT modify `run_settings` structure or add new languages (only fix existing C++ entry).
- Do NOT change `test_manager.py` phantom/display logic (only status/compile flow).
- Do NOT use `deepseek` subagent (user explicitly requested `minimax M3/free` or `lnkling/free`).
- Do NOT commit git changes unless user explicitly requests (not requested).

## Open questions (resolved)
- None remaining — user confirmed A (stuck >30s at COMPILING), C (fix settings + flow + status inconsistency), and subagent model preference.

## Approval gate
status: awaiting-approval -> user granted approval at 2026-09-05. Proceeding to write `.omo/plans/cph-compile-stuck.md`.
