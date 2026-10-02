# cph-by-chenkx — Package Control Submission Notes

Package version: v1.4.0
Repository: https://github.com/chenmoulaile/cph-by-chenkx
Channel entry file: `repository/c/cph-by-chenkx.json` (see snippet at the bottom)

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
- `.gitattributes` added: dev-only files (`PC_SUBMISSION_NOTES.md`,
  `RELEASE_NOTES_CN.md`, `.workbuddy`, `TestSyntax.sublime-settings`, …) are
  `export-ignore`d and stay out of the package.
- Channel metadata uses `"sublime_text": ">=4095"`: the minihtml CSS uses ST4
  CSS variables (`var(--foreground)`, `color(... alpha(...))`).
- Root `__init__.py` remains comment-only; `plugin_init.py` is the entry point;
  no `package-metadata.json`, no `.no-sublime-package`.
- Dead code removed: `olympic_funcs` key binding (command never existed),
  `set_tests_status` calls, `Tester.del_test/del_tests`, the whole debugger
  leftovers (`show_frames` with `eval()`, non-existent `redirect_frames` /
  `select_frame` actions), and the unreferenced `Highlight/CppVarHighlight.py`.
- Default `run_cmd` now uses forward slashes (works on all three platforms) and
  no longer passes the meaningless `-debug` argument; a
  `cph-by-chenkx (Windows).sublime-settings` platform override is provided for
  users who prefer backslash paths.

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

## Package Control Review Checklist (verified for v1.4.0)

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
