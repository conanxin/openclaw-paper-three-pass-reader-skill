# Minimal input — title only

The smallest input the skill can accept: just a title. Stage 0 will record
`input_kind = paper_title`, `reading_mode = abstract_only` until you find the abstract.

```bash
# 1. Create skeleton
python3 skills/paper-three-pass-reader/scripts/create_output_skeleton.py \
  --output paper-reading-output \
  --title "How to Read a Paper"

# 2. Edit data/paper_reading.json — minimum fields to fill:
#    paper_metadata.title           = "How to Read a Paper"
#    paper_metadata.source_kind     = "paper_title"
#    paper_metadata.reading_mode    = "abstract_only"
#    intake_quality.input_kind      = "paper_title"
#    intake_quality.reading_mode    = "abstract_only"
#    intake_quality.confidence      = "low"
#    intake_quality.warnings        = ["Title only — abstract not yet fetched"]
#    intake_quality.needs_confirmation = true
#    summaries.one_sentence         = "(fill after reading)"
#    summaries.three_sentence       = ["", "", ""]
#    summaries.ten_sentence         = [""] * 10
#    pass1.decision                 = "SEEK_REFERENCES_FIRST"
#    pass1.decision_rationale       = "Need abstract / PDF before deeper pass."

# 3. Render
python3 skills/paper-three-pass-reader/scripts/render_page.py \
  --input paper-reading-output/data/paper_reading.json \
  --output paper-reading-output

# 4. Open paper-reading-output/index.html
```

The page will render with mostly empty sections and a clear "intake quality: low
confidence, title-only" badge in the hero. That is the correct output — it tells
you (and anyone reading the page) that you have not actually read the paper yet.
