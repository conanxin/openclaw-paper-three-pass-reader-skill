# Minimal input — screenshot only

What you can do when all you have is a screenshot of the paper (title page,
abstract, a figure, or a slide). Stage 0 records `input_kind = paper_screenshot`,
`reading_mode = screenshot_only`, and surfaces every claim as `[Needs verification]`
until you provide text.

```bash
# 1. Skeleton
python3 skills/paper-three-pass-reader/scripts/create_output_skeleton.py \
  --output paper-reading-output \
  --title "(from screenshot — see data/intake_quality.json)"

# 2. Edit data/paper_reading.json:
#    paper_metadata.title        = "(best-effort from image)"
#    paper_metadata.source_kind  = "paper_screenshot"
#    paper_metadata.reading_mode = "screenshot_only"
#    intake_quality.input_kind   = "paper_screenshot"
#    intake_quality.reading_mode = "screenshot_only"
#    intake_quality.confidence   = "low"
#    intake_quality.warnings     = [
#      "OCR / VLM not run; only visual inspection so far.",
#      "Title, authors and year were inferred from the screenshot."
#    ]
#    intake_quality.needs_confirmation = true

# 3. Render
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input paper-reading-output/data/paper_reading.json \
  --output paper-reading-output

# 4. Open the page. The hero badge says "screenshot_only" in red.
#    Every claim in claims_evidence_map should be evidence_label = "[Needs verification]".
```

### Upgrading out of screenshot_only

Once you run OCR or a vision-language model on the screenshot and have text:

1. Paste the extracted text into `paper_reading.json` (fill summaries, five_cs, claims).
2. Update `paper_metadata.reading_mode` to `partial_text` (or `full_text` if you got it all).
3. Update `intake_quality.reading_mode` to match.
4. Re-run `render_page.py`.

The page will re-render with the new reading mode badge and the claims' evidence
labels will start to switch from `[Needs verification]` to `[Paper evidence]` /
`[Author claim]` as appropriate.
