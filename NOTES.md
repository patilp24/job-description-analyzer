# Known issues / future improvements

## Fixed
- "Or" requirements were split into separate items (e.g., consulting / IB / PE),
  making jobs look harder → prompt now keeps "or" alternatives as one item (not every run, see below)
- Evidence quotes were sometimes paraphrased → prompt requires exact quotes,
  and code verifies each quote appears in the resume
- Candidate experience varied between runs (2.3 to 3.8 yrs for the same resume) because the model
  doesn't know today's date → model now only lists roles with dates; Python calculates the total
  using today's date, merges overlapping roles, and caches the result per resume (now 4.0 yrs every run)
- Years check matched on the words "year" + "experience", so field-specific experience
  (e.g., "2 years in consulting") was wrongly counted as total experience → the model now labels
  general-experience items, and Python only applies the years arithmetic to those
- Named skills were replaced by generic categories ("Analytical tools and techniques" instead of
  SQL, statistics...) → prompt now requires keeping named tools
- Added exact keywords: extracted by the model, verified against the posting in code,
  and compared exactly with the resume (shows missing keywords in the posting's own wording)
- Hugging Face free tier only offers ZeroGPU for Gradio Spaces, which requires a @spaces.GPU
  function at startup → added a placeholder function (never called; the AI runs on Gemini's servers)

## Known issues

### Consistency (biggest weakness)
- Match scores vary widely for the same input (Google posting: 12 to 78 across 8 runs).
  Likely fixes: temperature 0, smaller judgment calls, or averaging several runs.
- Extraction varies between runs: company found / not found, required list length
  (jd5: 6 vs 8 items), "or" rule not always followed, key requirements sometimes dropped
  (jd3: "several years of production ML" missing)

### Judgment quality
- Evidence verification confirms quotes exist, not that they prove the qualification
- Meaning mismatches (jd5: "AI coding tools" met by Copilot Studio)
- Degree sometimes used alone as evidence, despite the prompt rule (jd2)
- Long "and" lists sometimes stay as one item and get full Met from partial evidence
  (jd4: 8 LLM concepts in one item)

### Extraction quality
- Red flags are the weakest field: often repeat the checklist labels instead of specific evidence
- jd5 keeps adding an extra "early-career" key (caught by validation and retried)
- Degree sometimes appears in both the education field and the required list (jd5)
- Keywords can include the job title (jd3: "AI Engineer")
- Experience field format varies ("5" vs "5 years" vs "2+ years")
- Qualifications got wordier after raising the limit to 10 words (trade-off for keeping named skills)

### Display
- Status column wraps awkwardly ("Missin g") in narrow layouts
- Model copies the "- " bullet prefix into qualification names (cosmetic)

### Untested
- Rate-limit (429) handling not tested directly; same code path as the tested 404 handling

## Ideas
- Run each job several times and report the score range, to measure consistency
- Show a "Partial — worth strengthening" list next to Missing skills
- Strip the "- " prefix from qualification names in code