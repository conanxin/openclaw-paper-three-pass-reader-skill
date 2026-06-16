# Phase P3PR-V0.2.17 — `p3pr finalize <run-dir>` Command

## STATUS

PASS

## PROJECT_DIR

`/home/conanxin/.openclaw/workspace/projects/paper-three-pass-reader-skill`

## BASE_VERSION

v0.2.15-alpha (also v0.2.16-alpha consumer run was already on main; v0.2.17 is the next skill release)

## TARGET_VERSION

v0.2.17-alpha

## PROBLEM

After a user (human or agent) fills `work/paper_reading.json` for a run, they still have to manually chain:

1. `p3pr.py run --audit-only <run-dir>` to validate the fill
2. zh-CN quality gate (separate command)
3. Render to `paper-reading-output/`
4. Publish via `publish_output_to_github.sh`
5. Published-pages audit

This is brittle, easy to skip a step, and the v0.2.15 hard guard (don't publish a missing `index.html`) is easy to forget. The fix is a single second-stage CLI command that runs the chain with the guards built in.

## FIX_SUMMARY

Added a new subcommand `p3pr finalize <run-dir>` to the existing `p3pr` CLI. It:

- Reads `<run-dir>/work/paper_reading.json` (hard-errors if missing)
- Runs the audit (`p3pr.py run --audit-only <run-dir>`), hard-errors if audit FAILED
- Detects zh-CN (from `--lang` flag or run-dir naming) and runs the quality gate; fails on quality-gate FAILED unless `--allow-draft-publish`, fails on WARN unless `--allow-warnings`
- Renders `<run-dir>/paper-reading-output/`
- Hard-checks `paper-reading-output/index.html` exists before any publish (v0.2.15 guard)
- Publishes to `conanxin/paper-reading-pages` on `gh-pages` via `publish_output_to_github.sh`
- Runs the published-pages audit after publish (unless `--skip-published-audit`)
- Prints a fixed-format `P3PR_FINALIZE_*` summary block on every exit

## FINALIZE_COMMAND

```
./p3pr finalize <run-dir> [--publish] [--repo X] [--branch Y] [--site-path Z]
                       [--page-title T] [--allow-warnings] [--allow-draft-publish]
                       [--skip-quality-gate] [--skip-published-audit]
                       [--published-audit|--no-published-audit]
                       [--dry-run] [--json-output PATH]
```

## FINALIZE_FLOW

1. Parse `<run-dir>` and verify `work/paper_reading.json` exists.
2. Run `p3pr.py run --audit-only <run-dir>` — BLOCK on FAILED.
3. If zh-CN: run the quality gate. Block on FAIL/WARN unless explicit allow flag.
4. Run `p3pr.py run --render-only <run-dir>` (or equivalent) → `<run-dir>/paper-reading-output/`.
5. Verify `paper-reading-output/index.html` exists. BLOCK if missing.
6. If `--publish`: call `publish_output_to_github.sh` with computed `--site-path` (explicit flag → `<run-dir>` basename) and `--page-title` (explicit flag → `paper_metadata.title` → run dir basename).
7. If `--published-audit` (default true after publish): run `audit_published_pages.py` and stash `work/published_pages_audit_after_finalize.json`.
8. Write `<run-dir>/work/audit_final.json`, `work/quality_gate_zh_cn.json`, and the summary JSON.
9. Print `P3PR_FINALIZE_*` summary.

## PUBLISH_GUARDS

- Missing `work/paper_reading.json` → `P3PR_FINALIZE_STATUS: BLOCKED` (no publish).
- Audit FAILED → `P3PR_FINALIZE_STATUS: BLOCKED_AUDIT_PARSE_FAILED` (no publish).
- Quality gate FAILED (zh-CN) → `P3PR_FINALIZE_STATUS: BLOCKED_VALIDATION_FAILED` unless `--allow-draft-publish`.
- Quality gate WARN (zh-CN) → `P3PR_FINALIZE_STATUS: WARN` unless `--allow-warnings`.
- Missing `paper-reading-output/index.html` after render → `P3PR_FINALIZE_STATUS: BLOCKED_RENDER_MISSING_INDEX` (v0.2.15 guard, carried into finalize).
- Publish step itself returns non-zero → `P3PR_FINALIZE_STATUS: BLOCKED_PUBLISH_FAILED`.

## SMOKE_RUNS

- Dry-run (no side effects): PASS — `P3PR_FINALIZE_DRY_RUN` block printed, `would_audit=true`, `would_render=true`, `would_publish=false`.
- `--no-publish` finalize on filled dogfood run: PASS — audit, quality gate, render all green; `P3PR_LOCAL_PAGE=<run-dir>/paper-reading-output/index.html`; `P3PR_PAGE_URL=` empty (no publish).
- `--publish` finalize on filled dogfood run: PASS — page published at <https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-dogfood-finalize-cn/>; published-pages audit returned 12/12 PASS.
- Block-path smoke (missing `work/paper_reading.json`): PASS — `P3PR_FINALIZE_STATUS: BLOCKED`, clear "work/paper_reading.json missing" message in stderr, no publish.

## PUBLISHED_PAGE

<https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-dogfood-finalize-cn/>

Verified live: HTTP 200, content rendered, footer present, no template leak, no raw dict, claims/evidence map present, resolver trail present, zh-CN glossary present, confidence values present, essay practice plan present.

## PUBLISHED_PAGES_AUDIT

Re-ran `audit_published_pages.py` after publishing the dogfood page:

- `pages_total: 12`
- `pages_checked: 12`
- `pages_pass: 12`
- `pages_warn: 0`
- `pages_fail: 0`

Stashed at `runs/p3pr-url-dogfood-filled-20260616/you-and-your-research-url-dogfood-cn/work/published_pages_audit_after_finalize.json`.

## VALIDATION

```
=================================================
 PASS: 279    FAIL: 0
=================================================
STATUS: PASS
```

New step [21] v0.2.17-alpha p3pr finalize subcommand (16 sub-checks, all green). Total validation now covers every subcommand, every published page, and every block path in the v0.2.15 / v0.2.17 release.

## FILES_CREATED

- `docs/RELEASE_NOTES_v0.2.17-alpha.md`
- `docs/PHASE_P3PR_V0_2_17_FINALIZE_COMMAND_REPORT.md`
- Smoke artifacts in `runs/p3pr-finalize-smoke-20260616/` (small, in scope).
- Dogfood finalize outputs in `runs/p3pr-url-dogfood-filled-20260616/you-and-your-research-url-dogfood-cn/`:
  - `work/audit_final.json`
  - `work/quality_gate_zh_cn.json`
  - `paper-reading-output/` (rendered page)
  - `work/published_pages_audit_after_finalize.json`
  - `work/resolver_source.json`

## FILES_MODIFIED

- `skills/paper-three-pass-reader/scripts/p3pr.py` — added `handle_finalize`, `_finalize_print_summary`, `build_finalize_parser`, finalize dispatch in `main()`, finalized stub subparser registration.
- `scripts/validate.sh` — new step [21] (16 sub-checks for finalize).
- `skills/paper-three-pass-reader/docs/USAGE.md` — new v0.2.17-alpha finalize section.
- `skills/paper-three-pass-reader/docs/ONE_LINE_CLI.md` — new finalize section.
- `skills/paper-three-pass-reader/docs/RUNNER.md` — new finalize section.
- `skills/paper-three-pass-reader/docs/ZH_CN_QUALITY_GATE.md` — new finalize section.
- `README.md` — Quick Start updated, version table updated.
- `README.zh-CN.md` — version table updated, version footer updated.
- `CHANGELOG.md` — full v0.2.17-alpha entry.

## COMMIT

`Add p3pr finalize command`

## PUSH

`git push origin main`

## TAG

`v0.2.17-alpha` (annotated)

## RELEASE

<https://github.com/conanxin/openclaw-paper-three-pass-reader-skill/releases/tag/v0.2.17-alpha>

## LIMITATIONS

- `finalize` does not auto-fill paper content. It assumes `work/paper_reading.json` has already been filled by human or agent.
- `--allow-warnings` and `--allow-draft-publish` should be used carefully — they exist to make low-CJK-coverage English papers publishable, but they bypass quality gates.
- `finalize` does not retry network failures during publish. If GitHub Pages is down or the push is rate-limited, it returns BLOCKED_PUBLISH_FAILED and the user must re-run.
- The v0.2.15 hard guard against empty `paper-reading-output/index.html` is enforced — pages that failed quality gate and were not allowed to draft-publish will not appear on the site.

## NEXT_USER_ACTION

- Spot-check the live dogfood page: <https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-dogfood-finalize-cn/>.
- If the page looks good, the v0.2.17 release is done and the next planned phase is v0.2.18 (no content scope defined yet — wait for user direction).
- If something on the dogfood page needs fixing, file a follow-up issue / phase before declaring v0.2.17 stable.
