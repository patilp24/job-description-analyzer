# Known issues / future improvements

## Fixed
- "Or" requirements were split into separate items (e.g., consulting / IB / PE),
  making jobs look harder and lowering match scores → now kept as one item
- Evidence quotes were sometimes paraphrased → prompt now requires exact quotes,
  and code verifies each quote appears in the resume

## Known issues
- Evidence verification confirms quotes exist, not that they prove the qualification
- Candidate years of experience varies between runs (2.3 to 3.8 for the same resume)
- Match scores vary between runs (Google: 43 → 28 → 50 → 56 → 67); consider temperature 0
- jd5 keeps adding an extra "early-career" key (caught by validation and retried)
- Red flags are the weakest extraction field (often generic)
- Years check only applies to items mentioning both "year" and "experience";
  skill-specific years (e.g., "2+ years SQL") are judged by the model
  - Extraction varies between runs (Google posting: company "Google" in earlier runs, "Not named" in this run)
  - "Or" rule isn't followed every run (Google: strategy OR cross-functional split again)
  - Qualifications got wordier after raising the limit to 10 words (trade-off for keeping named skills)
- Status column wraps awkwardly ("Missin g") in narrow layouts
- Match prompt sends qualifications as "- item"; model copies the "- " into its output (cosmetic)
- Red flags often repeat the checklist labels instead of specific evidence (jd2)
- Model sometimes uses the degree alone as evidence, despite the prompt rule (jd2)
- Extraction sometimes drops key requirements (jd3: "several years of production ML" missing; experience shown as "Not stated")
- Keywords can include the job title (jd3: "AI Engineer")
- Long "and" lists sometimes stay as one item and get full Met from partial evidence (jd4: 8 LLM concepts in one item)
- Experience field format varies ("5" vs "5 years" vs "2+ years")
- Degree sometimes appears in both the education field and the required list (jd5)
- Required list length varies a lot between runs (jd5: 6 items now vs 8 before)
- Meaning mismatches in judgments (jd5: "AI coding tools" met by Copilot Studio)

## Ideas
- Extract resume roles with dates once, and calculate total experience in code
- Run each job several times to measure score consistency