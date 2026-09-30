# cph-by-chenkx — Package Control Submission Notes

Package version: v1.2.0
Repository: https://github.com/chenmoulaile/cph-by-chenkx
Local push: confirmed by user (t2 completed)

## v1.2.0 notes

- Import commands (`cph_import_from_file`, `cph_import_from_folder`) moved from
  `core/` subpackage back to root-level `cph_import.py` — Sublime does not
  auto-load commands defined inside subpackages, which left menu items greyed out.
- Imports now append/merge with existing tests (dedup by input+answer) instead
  of overwriting the session.
- Re-run kills a still-running process before starting a new one (wait loop up
  to 2s, epoch-based stale callback drop); fixes "next test" hang.
- New `detail_style` setting (`view` default / `phantom` legacy), sample input
  section in detail, lone `\r` cleanup.
- Edit view top bar reordered (save/delete before hint) so buttons stay
  clickable at default sidebar width; stale edit/answer views closed on re-run.
- Verdict badge CSS: plain inline element so colored background hugs the text.

## v1.1.0 notes

- Shared modules live in `core/` subpackage (`cph_settings`, `cph_i18n`, `cph_verdict`,
  `cph_import`); import commands restored to `core/cph_import.py` after being
  accidentally dropped in a previous commit.
- All root-level plugins import only from subpackages (`.core.*`, `.Modules.*`,
  `.Highlight.*`); root `__init__.py` stays comment-only.
- New commands: `cph_companion_listener` (idempotent, persistent), 
  `cph_companion_stop_listener`, `cph_test_detail_view`; all shipped key bindings
  carry `context` arrays.
- No `package-metadata.json`, no `.no-sublime-package` in the repository.

## v1.0.7 notes — 16 Failure Fixes (all verified in session)

1. **Root `__init__.py` empty/comment-only** — no root-level plugin imports (PC guideline).
2. **`core/` subpackage created** — settings (`cph_settings.py`), i18n (`cph_i18n.py`), verdict (`cph_verdict.py`) moved out of root to avoid automatic plugin loading at root.
3. **`core/__init__.py` subpackage entry** — clean subpackage definition.
4. **Root `__init__.py` kept to comment-only** — entry point deferred to `plugin_init.py`.
5. **`plugin_init.py` entry point** — no root-level plugin imports; loads via `plugin_loaded()`.
6. **`package-metadata.json` removed** — not allowed by PC review rules.
7. **`.no-sublime-package` removed** — not allowed by PC review rules.
8. **Contextual keymaps (`Default (Linux/Windows/OSX).sublime-keymap`)** — all bindings include `context` arrays (`selector`, `preceding_text`, `setting.edit_mode`) instead of global bindings.
9. **Menu includes "Key Bindings"** — `Main.sublime-menu` contains `Preferences -> Package Settings -> cph-by-chenkx -> Key Bindings` item.
10. **`CppVarHighlight.py` raw regex fix** — `NUMBER = re.compile(r'\d+')` uses raw string; avoids escape issues.
11. **Hidden console window fix (`cph_stress.py`)** — `subprocess.STARTUPINFO()` with `STARTF_USESHOWWINDOW` (lines 171-174, 200-203) prevents flashing console on Windows.
12. **Hidden console window fix (`Modules/ProcessManager.py`)** — same `startupinfo` fix applied in compile/run paths (lines 139-142, 176-178).
13. **Syntax-specific settings entries (`TestSyntax.sublime-settings`)** — `hide_minimap`, `show_minimap`, `line_numbers` set for `TestSyntax` scope.
14. **Syntax-specific settings (`cph-by-chenkx.sublime-settings`)** — settings file valid JSON; `run_settings` with language-specific `extensions`, `compile_cmd`, `run_cmd`, `time_limit_ms`, `memory_limit_mb`.
15. **`test_manager.py` status consistency (`COMPILING`)** — `run_test()` uses `'COMPILING'` to match `make_opd()` (line 446 fixed from `'COMPILE'`).
16. **`ProcessManager.py` `is_run` guard fixed** — line 155 `if self.is_run and False:` corrected to `if self.is_run:`; `compile()` `stdin` changed from `PIPE` to `None` (deadlock risk removed).

## Package Control Review Checklist (verified)

- [x] No root-level plugin imports (`__init__.py` comment-only; `plugin_init.py` entry point).
- [x] Proper key bindings context (`context` arrays in all `.sublime-keymap` files).
- [x] Empty/comment-only `__init__.py` at package root.
- [x] No `package-metadata.json` file present.
- [x] No `.no-sublime-package` file present.
- [x] Syntax-specific settings entries (`TestSyntax.sublime-settings`).
- [x] Core modules moved to `core/` subpackage.
- [x] `.sublime-package` built (zip with contents at root, excluding `.agent-teams`, `.git`, `.omo`, `.codegraph`, `__pycache__`, `.pyc`, `.db`, `.jsonl`, `.gitignore`, `.gitattributes`, `push_to_github.bat`, `create_release.py`).

## Build artifact

- `cph-by-chenkx.sublime-package` (zip, contents verified — see `cph-by-chenkx.sublime-package` in workspace root).

## Additional notes for reviewers

- `test_manager.py` compile callback handles `cmp_data` safely (`None` check before indexing).
- `run_settings` structure unchanged; only C++ entry `compile_cmd` aligned to output `.exe` explicitly and `-std=c++11` (matches README).
- `Modules/` kept in package because `test_edit.py` and `test_manager.py` import `ProcessManager` from it.
- `README.md` and `RELEASE_NOTES_CN.md` included for user documentation.
