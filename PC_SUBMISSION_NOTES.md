# cph-by-chenkx — Package Control Submission Notes

Package version: v1.4.9
Repository: https://github.com/chenmoulaile/cph-by-chenkx
Channel entry file: `repository/c/cph-by-chenkx.json` (see snippet at the bottom)

## v1.4.9 notes

- **Run modes fixed**: `cph_run_all_tests` / `cph_run_failed_tests` /
  `cph_run_force_recompile` sent `run_all` / `run_failed` / `force_compile` to
  `cph_view_tester`, whose `run()` did not accept them -> `TypeError`, so the
  three commands were dead outside the run panel. They are now accepted and
  forwarded to `create_opd()`.
- **Runtime errors are located**: when a crashed program's output names a
  position (Python traceback, Java stack trace, gcc/clang `-fsanitize`
  diagnostic) the card/detail and the status bar show `file:line`. A bare C++
  segfault carries no line - the README documents adding
  `-fsanitize=address,undefined -g`.
- **`ProcessManager`**: the stdin-closed handler called `t()` without importing
  it (`NameError`); `cph_stress` leaked the `except ... as e` variable into a
  deferred lambda (same class of bug); a stress run whose every round timed out
  no longer reports success.
- **Test chain**: `run_failed` mode now continues past a failing test; running
  a not-yet-materialised test from the test menu no longer raises `IndexError`
  (new `Tester.output_at()`); deleting a test no longer rewinds `test_iter`.
- **`tests_relative_dir`** is now probed by `get_tests_paths()` (previously the
  data was written but never loaded or cleared); single-file import now uses the
  shared `merge_into_file()` policy; `_read_text()` detects a UTF-16 BOM first.
- **Cards**: the status class emitted by `get_test_class()` matched no CSS rule
  (`test-AC` / `test-wrong-answer` vs the shipped `.test-accept` /
  `.test-decline`), so the green/red tint was dead - fixed; missing verdict
  badge colours added; the card now surfaces a captured stderr.
- Regression checks: 66 -> 86.

## v1.4.8 notes

- **doctor was unusable**: `cph_doctor.py` ran its placeholder check without
  importing `re`, so opening "Check environment (doctor)" raised `NameError` on
  the first language entry and the report view was never created. The import is
  restored; `tests/run_tests.py` now both checks `_unknown_placeholders` and
  executes the full `run()` path, so a "feature totally dead" regression of this
  kind is caught locally.
- **Memory chip no longer wraps**: `get_nice_memory()` used a plain space, which
  minihtml broke onto two lines on a narrow panel; it now uses `&nbsp;` (the
  plain-text detail view converts it back).
- Trailing newline added to `repository-cph-by-chenkx.json` and
  `Main.sublime-menu`; regression checks 62 -> 66.

## v1.4.7 notes (Package Control review round)

Reviewer feedback addressed:

- **Root level plugin imports** - `cph_doctor.py` imported `.cph_companion`; the
  listener state now lives in `core/cph_state.py` and doctor reads it from there.
- **Key bindings without a context** - the panel collapse/restore, stress stop,
  Companion stop and doctor bindings now carry contexts. A new listener
  (`cph_context.py`) answers four custom context keys (`cph_run_view`,
  `cph_has_run_panel`, `cph_stress_running`, `cph_listener_running`), so keys
  only fire when they actually apply.
- **Platform settings variant** - `cph-by-chenkx (Windows).sublime-settings` was
  removed; the shipped default command is already platform neutral.
- **Channel entry** - the `name` key was dropped (derivable from `details`).
- `tests/run_tests.py` now enforces these four rules (62 checks in total).

## v1.4.6 notes

- Fixed a stale run-view check in `cph_tests_io._refresh_panel`: the panel marker
  became a view setting in v1.4.5, so the refresh silently did nothing when the
  command ran from the panel itself.
- One shared merge policy (`core/cph_tests_merge.py`) for tests from files, the
  clipboard, the Companion listener and stress counterexamples: keyed by input,
  answers are only filled in - a re-sent sample can no longer overwrite an answer
  the user accepted by hand.
- `insert()` stops retrying a closed stdin pipe; unknown command placeholders are
  surfaced in the compile panel and checked by doctor.
- New `regard_pe_as_ac` setting, a copy-pasteable doctor Markdown report, and
  `cph_test_menu` (Ctrl+Alt+M) for mouse-free test operations.
- New static regression checks in `tests/run_tests.py`: every `self.x()` call must
  be defined in its class, and the retired `opd_info` marker must not be compared
  anywhere. Both are the kind of defect that unit tests alone cannot reach.

## v1.4.5 notes

- Fixed the shipped default C++ `compile_cmd` raising `KeyError: 'extra_sources'`
  on every fresh install: `${extra_sources}` / `{include_dirs}` are expanded
  before formatting now, and unknown placeholders only warn (`_LenientFormat`).
- macOS memory now comes from `libproc.proc_pid_rusage(pid, RUSAGE_INFO_V2)` for
  the measured process instead of the cumulative `RUSAGE_CHILDREN` peak.
- `Test.rtcode` is initialized, doctor recognises template commands, cards refresh
  after a swap, shifted detail tabs are closed, a broken stdin pipe is survivable,
  edit tabs are reused, truncation is visible, the process group is cached for the
  SIGKILL escalation, Companion samples dedupe by input, clipboard pastes are
  inserted in one go.
- CI now runs on Windows and macOS as well as Linux; 47 regression checks.

## v1.4.4 notes

- Newlines are normalized (CRLF and lone CR to LF) on every text path: program
  stdout, stderr, compiler diagnostics and stored test data. The binary pipe
  introduced for Python 3.3 compatibility had dropped universal-newline
  translation, so Windows CRs were rendered as `<0x0d>` in the run panel.
  A CRLF split across two reads still yields exactly one newline.
- Peak memory is sampled synchronously right after `Popen` as well as by the
  polling thread, so very short runs (tens of milliseconds) still report it.
- `tests/run_tests.py` grew to 36 checks (newline handling included).

## v1.4.2 notes

- Fixed three regressions from the previous round: the "re-run failed tests"
  chain raised `IndexError` when it skipped accepted tests (the iterator was
  padded a single slot), the `sync_output` setting was unreachable because
  the command signature defaulted to `sync_out=True`, and the run summary
  phantom ended up inside a test after expanding a folded AC test.
- The edit/answer panel bar is now split over two lines (`test N` as a
  heading, buttons below it).
- `#include "..."` headers (depth 3) are part of the compile cache key, so
  editing a header triggers a rebuild instead of running a stale binary.
- POSIX only spawns through a shell when the command really needs one
  (pipes/globs/`&&`); otherwise `shlex.split` + `shell=False`, so the memory
  sampler measures the program and `killpg` reaches it.
- Compiler diagnostics decode as UTF-8 and fall back to the locale encoding
  (Chinese g++ messages were garbled).
- i18n: the HTML templates now use the `next_label` / `stop_label` /
  `test_label` / `time_label` / `type_label` placeholders the code always
  passed; the Chinese UI no longer shows those words in English.
- Dead code removed: `LayoutListener.move_syncer`, empty `isEnabled`,
  unused `REGION_*_PROP` tables, `BEGIN/OUT/END_TEST_STRING`, the obsolete
  `Test N {` / `} rtcode` highlight rules, the whole `use_debugger` plumbing,
  `ProcessManager.get_path/has_var_view_api/new_test/communicate`.
- `CphViewTesterCommand` state is per view instead of class attributes.
- **Added `tests/` and CI**: `tests/run_tests.py` (26 checks, fake `sublime`
  module, no third-party deps) and `tests/check_py33.py` (Python 3.3 guard
  that already proved it catches the `Popen(encoding=...)` regression), both
  run by `.github/workflows/tests.yml` on push/PR. `tests/`, `.github/`,
  `.workbuddy/` and the dev documents are `export-ignore`d, so they stay out
  of the `.sublime-package`.

## v1.4.1 notes (packaging-relevant)

- Sublime's plugin host is **Python 3.3**: `Popen(encoding=..., errors=...)`
  (3.6/3.7+) crashed every run. Subprocesses now use binary pipes with an
  incremental UTF-8 decoder, and `subprocess.run` was removed from the stress
  test (it does not exist before 3.5).
- Process state self-heals after a failed `Popen`
  (`is_run` / `is_stopped` / `terminate` / `insert`).
- No background writes to the user's settings file: the limits received from
  Competitive Companion are kept in memory.

## v1.4.0 notes (packaging-critical)

- **Resources are now loaded with `sublime.load_resource()`** through the new
  `core/cph_resources.py`. Previously every `Highlight/*.html` / `*.css` was read
  with a real filesystem `open()`, which raises `FileNotFoundError` once the
  package is installed as a `.sublime-package` (zip) — every card, detail view
  and compile panel would have failed to render. Reads are cached per process.
- `Modules/__init__.py` and `Highlight/__init__.py` added so all subpackages
  load reliably from a zip (no reliance on implicit namespace packages).
- `messages.json` + `messages/install.txt` added (PC install message with the
  key bindings).
- `.gitattributes` added: dev-only files are `export-ignore`d.
- Channel metadata uses `"sublime_text": ">=4095"`: the minihtml CSS uses ST4
  CSS variables (`var(--foreground)`, `color(... alpha(...))`).
- Root `__init__.py` remains comment-only; `plugin_init.py` is the entry point;
  no `package-metadata.json`, no `.no-sublime-package`.
- Memory limit verdicts are real: peak memory is sampled per platform
  (`Modules/memprobe.py`) instead of being dead configuration.
- Process termination kills the whole process tree on POSIX (`killpg`, SIGTERM
  → SIGKILL) and on Windows (`taskkill /F /T`).

## v1.2.0 notes

- Import commands moved from `core/` subpackage back to root-level
  `cph_import.py` — Sublime does not auto-load commands defined inside
  subpackages, which left the menu items greyed out.
- Imports append/merge with existing tests (dedup by input+answer) instead of
  overwriting the session.
- Re-run kills a still-running process before starting a new one (epoch-based
  stale callback drop); fixes the "next test" hang.
- New `detail_style` setting (`view` default / `phantom` legacy), sample input
  section in detail, lone `\r` cleanup.
- Edit view top bar reordered (save/delete before hint) so buttons stay
  clickable at default sidebar width; stale edit/answer views closed on re-run.
- Verdict badge CSS: plain inline element so the colored background hugs the text.

## v1.1.0 notes

- Shared modules live in the `core/` subpackage (`cph_settings`, `cph_i18n`,
  `cph_verdict`); import commands restored after being accidentally dropped.
- All root-level plugins import only from subpackages (`.core.*`, `.Modules.*`,
  `.Highlight.*`); root `__init__.py` stays comment-only.
- New commands: `cph_companion_listener` (idempotent, persistent),
  `cph_companion_stop_listener`, `cph_test_detail_view`.
- No `package-metadata.json`, no `.no-sublime-package` in the repository.

## v1.0.7 notes — 16 Failure Fixes (all verified)

1. Root `__init__.py` empty/comment-only — no root-level plugin imports.
2. `core/` subpackage created for settings / i18n / verdict modules.
3. `core/__init__.py` subpackage entry.
4. Root `__init__.py` kept comment-only; entry point deferred to `plugin_init.py`.
5. `plugin_init.py` entry point (`plugin_loaded()`).
6. `package-metadata.json` removed — not allowed by PC review rules.
7. `.no-sublime-package` removed — not allowed by PC review rules.
8. Contextual keymaps — every binding carries a `context` array.
9. `Main.sublime-menu` contains a `Key Bindings` item.
10. `CppVarHighlight.py` raw regex fix (file now removed as dead code).
11. Hidden console window fix (`cph_stress.py`) via `STARTUPINFO`.
12. Hidden console window fix (`Modules/ProcessManager.py`) via `STARTUPINFO`.
13. Syntax-specific settings (`TestSyntax.sublime-settings`).
14. Settings file is valid JSON with per-language `run_settings`.
15. Status consistency (`COMPILING`) in `test_manager.py`.
16. `ProcessManager.run_file` `is_run` guard fixed; `compile()` `stdin=None`
    (deadlock removed).

## Package Control Review Checklist (verified for v1.4.2)

- [x] No root-level plugin imports (`__init__.py` comment-only; `plugin_init.py` entry point).
- [x] Key bindings carry `context` arrays.
- [x] Empty/comment-only `__init__.py` at package root.
- [x] No `package-metadata.json`, no `.no-sublime-package`.
- [x] All subpackages have `__init__.py` (`core/`, `Modules/`, `Highlight/`).
- [x] Resources load from inside a `.sublime-package` (`sublime.load_resource`).
- [x] `messages.json` + `messages/install.txt` present.
- [x] `.gitattributes` excludes dev-only files from the package.
- [x] Commands and key bindings are listed in the menu and the command palette,
      and open settings in a split view.
- [x] No package reload required for settings changes (`Settings.add_on_change`).
- [x] Plugin code runs on the default Python 3.3 host (guarded by
      `tests/check_py33.py`).
- [x] No writes to the user's settings file from background callbacks.
- [x] `tests/`, `.github/` and dev documents are `export-ignore`d.
- [x] `README.md` and `LICENSE` included for users.

## Channel entry (repository/c/cph-by-chenkx.json)

```json
{
	"name": "cph-by-chenkx",
	"details": "https://github.com/chenmoulaile/cph-by-chenkx",
	"labels": ["c", "c++", "competitive programming", "testing"],
	"releases": [
		{
			"sublime_text": ">=4095",
			"tags": true
		}
	]
}
```

## Additional notes for reviewers

- `test_manager.py` compile callback handles `cmp_data` safely (`None` check
  before indexing).
- Memory limit verdicts are real: peak memory is sampled per platform
  (`Modules/memprobe.py`) instead of being dead configuration.
- Process termination kills the whole process tree on POSIX (`killpg`, SIGTERM
  → SIGKILL) and on Windows (`taskkill /F /T`).
- `Modules/` must stay inside the package: `test_edit.py` and `test_manager.py`
  import `ProcessManager` from it.
