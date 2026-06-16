# paper-three-pass-reader v0.2.18-alpha

## Summary

This release polishes the `p3pr finalize` workflow so the two-stage flow

```bash
./p3pr url <url> --zh --full --no-publish
# fill work/paper_reading.json
./p3pr finalize <run-dir> --publish
```

works with no extra flags. `finalize` now auto-infers the gh-pages site-path and the published page title from `paper_reading.json`, and the summary block is much easier to act on.

## Included

- Automatic site-path inference from `paper_reading.json` (precedence: explicit flag → `page_slug` / `slug` / `default_slug` → slugified `paper_metadata.title` → run-dir basename)
- Automatic page-title inference (precedence: explicit flag → `page_title` → `title_zh` for zh-CN runs → `paper_metadata.title` → run-dir basename)
- New `P3PR_SITE_PATH` / `P3PR_PAGE_TITLE` / `P3PR_READING_MODE` / `P3PR_LANGUAGE` / `P3PR_AUDIT_STATUS` / `P3PR_QUALITY_GATE_STATUS` / `P3PR_WARNING_COUNT` / `P3PR_WARNING_SUMMARY` lines in the finalize summary
- `P3PR_WARNING_SUMMARY` now lists up to 3 actual warning messages instead of a generic "warnings exist" line
- `P3PR_NEXT_ACTION` is now state-aware (BLOCKED audit / BLOCKED quality gate / WARN / PASS / not-published), telling the operator exactly what to do next
- Improved dry-run: emits `inferred_site_path` / `inferred_page_title` with source attribution ("auto from paper_reading.json" vs "explicit --site-path")
- All v0.2.15 / v0.2.17 publish guards preserved: missing `work/paper_reading.json` → BLOCK, audit FAILED → BLOCK, quality-gate FAILED → BLOCK unless `--allow-draft-publish`, missing `paper-reading-output/index.html` → BLOCK
- Validation: 14 new sub-checks in step 22 (293/0 PASS total)

## Compatibility

- All existing finalize flags remain supported.
- Explicit `--site-path` and `--page-title` still override the inferred values.
- Existing run directories remain compatible — inference reads the same `paper_reading.json` that the runner writes.
- Existing pages remain published.
- No old tags moved.
- No old releases deleted.

## Dogfood

- Live dogfood page: <https://conanxin.github.io/paper-reading-pages/you-and-your-research-url-finalize-ux-cn/> (HTTP 200).
- Live published-pages audit: 13/13 PASS, 0 warn, 0 fail (the new finalize-ux page brings the total from 12 to 13).

## When to use explicit `--site-path` / `--page-title`

In most cases inference is fine. Override when:

- The auto-inferred site-path collides with a previous page (re-publish under a new slug).
- The paper has a Chinese title that doesn't slugify well; set `--site-path` manually.
- The publisher page title needs to differ from the paper's own title (e.g. add a series prefix).

## When to use `--allow-warnings`

`--allow-warnings` should be used when the quality gate flags long English blobs in an English-paper dogfood run. The warnings are real but expected for English-source papers translated into zh-CN output.
