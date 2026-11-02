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

## Ideas
- Extract resume roles with dates once, and calculate total experience in code
- Run each job several times to measure score consistency