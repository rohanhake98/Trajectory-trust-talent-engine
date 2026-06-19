# PRD: Trajectory & Trust Talent Intelligence Engine
**Codename:** Counterfactual Talent Trajectory Graph + Honeypot Shield
**Track:** AI Hiring Intelligence Hackathon — Candidate Ranking Challenge
**Build window:** 24–48 hrs, small team, CPU-only

---

## 1. Problem Reframe (the slide that wins the room)

The brief looks like a resume-matching problem. It is not. With 100,000 candidates, only a handful holding the literal target title, 23 behavioral signals, and explicit honeypot/keyword-stuffing traps baked into the data, the challenge is actually testing:

> **Can you rank candidates by who will become the best real hire — not who looks best on paper right now?**

We are explicitly **not** building a resume-matcher, embedding-similarity search, or title classifier. Those are the 20 obvious submissions every other team will ship. We are building a system that scores three things no naive ranker captures:

1. **Trajectory** — is this candidate's career *moving toward* this role, even if they're not there yet?
2. **Trust** — is this profile real, consistent, and not a keyword-stuffed or synthetic trap?
3. **Convertibility** — if shortlisted, will this person actually respond, interview, and accept?

**One-line pitch:** *"We rank candidates by where they're going and whether we can trust the map — not by where they already are."*

---

## 2. Goals & Non-Goals

### Goals
- Produce a CSV of exactly 100 ranked candidates with non-increasing scores and per-candidate reasoning text.
- Demonstrably catch and demote honeypot / synthetic / keyword-stuffed profiles.
- Surface at least a few "underrated" candidates — strong trajectory, weak title-literal match — as the demo's signature moment.
- Keep the entire pipeline CPU-only, deterministic, and reproducible in under ~10 minutes end-to-end on the full 100K pool.

### Non-Goals (say this out loud to judges)
- Not predicting actual on-the-job performance, coding ability, or team fit.
- Not a fairness/legal-compliance audit tool (though calibration helps avoid obvious bias traps).
- Not using an LLM to *generate* scores or hallucinate reasoning — only to template/phrase reasoning from already-computed features.
- Not building a GNN or deep graph embedding model — out of scope for the time budget; a feature-engineered graph + calibrated ranker beats an undercooked GNN in a 48hr window.

---

## 3. Users & Judging Lens

- **Primary user (in-story):** A technical recruiter / hiring manager at the target company sourcing for one specific senior AI engineering role.
- **Primary user (real):** Hackathon judges scoring originality, technical depth, business relevance, and trap-resistance.
- **What judges will actually do:** open the CSV, skim reasoning text, ask "why is #1 ranked above the literal title-match candidate," and check if a keyword-stuffed profile got demoted. Design the demo around answering that exact question live.

---

## 4. System Architecture

```
┌─────────────┐   ┌──────────────────┐   ┌───────────────┐   ┌────────────┐   ┌──────────────┐   ┌──────────┐
│   Ingest    │ → │  Feature Builder  │ → │  Graph Layer  │ → │   Shield   │ → │    Ranker    │ → │ Exporter │
│ JSONL→records│   │ static/dynamic/   │   │ candidate-    │   │ honeypot/  │   │ fit+traj+    │   │ CSV top  │
│ normalize    │   │ trajectory/trust  │   │ skill-title-  │   │ stuffing/  │   │ trust+avail  │   │ 100,     │
│ skills/titles │   │ features          │   │ company graph │   │ impossible │   │ calibrated   │   │ reasons  │
└─────────────┘   └──────────────────┘   └───────────────┘   └────────────┘   └──────────────┘   └──────────┘
```

### 4.1 Ingest
- Parse JSONL pool, validate against schema, fail loudly on malformed records (don't silently drop — log and report count).
- **Skill/title canonicalization**: build a lookup table collapsing the 133 skill names and 47 title variants into normalized buckets (e.g., "ML Engineer" / "Machine Learning Engineer" / "AI/ML Engineer" → one canonical node). This single step is what makes the graph layer actually work — skip it and every downstream feature is noisy.

### 4.2 Feature Builder — four feature families

**A. Static Fit** (the "obvious" layer, kept deliberately thin)
- Title-to-role text similarity (cheap embedding or TF-IDF cosine — not the differentiator, just table stakes)
- Skill overlap with JD-required skills, weighted by proficiency + endorsements
- Education tier, years of experience banding

**B. Trajectory Features** (the differentiator)
- `career_velocity`: title-seniority delta per year across `career_history` (does seniority level increase faster than peers at the same starting point?)
- `transition_relevance`: for each job change, does `industry`/`title` move *toward* AI/ML/senior-eng, or sideways/away?
- `skill_acquisition_rate`: new skills gained per year, weighted toward skills relevant to the target role (proxy: `skills[*].duration_months` vs candidate tenure)
- `time_to_role_estimate`: simple monotonic projection — at current trajectory slope, how many months until this candidate's profile resembles a true senior-AI-engineer profile? Lower is better.

**C. Trust / Anomaly Features** (the shield's raw inputs)
- `timeline_consistency`: overlapping or impossible `career_history` date ranges → flag
- `skill_count_vs_depth_ratio`: candidates with very high skill counts but near-zero endorsements/duration on most of them → keyword-stuffing signal
- `title_capability_gap`: claimed title/seniority vs. skill proficiency + assessment scores mismatch
- `synthetic_pattern_score`: improbable combinations (e.g., 2 years experience + 15 certifications + "Senior" title) flagged via simple rule thresholds, not ML — rules are more explainable to judges and easier to defend live

**D. Behavioral / Convertibility Features** (from the 23 `redrob_signals`)
- `last_active_recency`, `open_to_work`, `recruiter_response_rate`, `avg_response_time`, `search_appearances`, `saved_by_recruiters_count`, `interview_completion_rate`, `offer_acceptance_rate`, `notice_period_days`, `relocation_willingness`, `work_mode_match`, `salary_band_overlap`
- Combine into a single `convertibility_score` (see formula §6)

### 4.3 Graph Layer
Lightweight, not a GNN — this is the right scope call for 48 hours.
- **Nodes:** candidate, canonical_title, canonical_skill, company, industry
- **Edges:** `worked_at`, `has_skill(weight=proficiency)`, `moved_to(title_a→title_b, timestamp)`, `assessed_in`
- **Use:** compute `role_adjacency_distance` — graph-shortest-path from candidate's current title node to the target title node through the `moved_to` transition graph built from the *whole population's* observed career moves. This answers "how many realistic hops away is this person, based on what similar people have actually done?" — far more defensible than a vibes-based seniority guess.
- Implementation: adjacency list + BFS in plain Python/NumPy. No graph DB needed at this scale within the time budget.

### 4.4 Shield Layer (Honeypot Defense)
Runs *before* final ranking, not as a bolt-on filter:
1. Hard-disqualify or heavily penalize records that fail `timeline_consistency` (impossible dates).
2. Apply a continuous penalty (not a binary cut) for `skill_count_vs_depth_ratio` and `synthetic_pattern_score` — penalize proportionally so borderline real profiles aren't wrongly nuked.
3. Output a `trust_score ∈ [0,1]` per candidate that multiplies into final rank rather than being a separate gate — this avoids the failure mode of "trust score correct but candidate still placed wrong" and is easy to explain in one sentence to judges.

### 4.5 Ranker
- Combine four pillars into one calibrated score (§6).
- Calibration step: rescale raw scores so the score distribution across the top 100 is smooth, strictly non-increasing, and ties break deterministically by `candidate_id` (required by spec).

### 4.6 Reason Generator
- **No generative hallucination.** Build a small template engine: for each candidate, pull their top 2–3 contributing features by magnitude (e.g., "high career velocity," "strong skill-depth, low stuffing risk," "fast historical response rate") and slot them into a 1–2 sentence template.
- Optionally pass the *extracted, already-true* feature bullets through an LLM call purely for prose smoothing — never for fact generation. This distinction is worth stating explicitly to judges since it directly addresses the "no hallucination" rule in the spec.

### 4.7 Exporter
- CSV: `rank, candidate_id, score, reasoning` — exactly 100 rows, score strictly non-increasing, deterministic.

---

## 5. Dataset Fields Used

```
profile.{anonymized_name, headline, summary, location, country, years_of_experience,
         current_title, current_company, current_company_size, current_industry}
career_history[*].{company, title, start_date, end_date, duration_months, is_current, industry, company_size, description}
education[*].{institution, degree, field_of_study, tier}
skills[*].{name, proficiency, endorsements, duration_months}
certifications[*]
languages[*]
redrob_signals.* (all 23 — see §4.2.D for which roll into convertibility_score)
```

---

## 6. Scoring Formula

### 6.1 Framework

```
final_score = w1·StaticFit + w2·TrajectoryScore + w3·Convertibility + w4·TrustScore
```

Where each sub-score is normalized to `[0, 1]` before weighting, and `TrustScore` is applied as a **multiplicative gate on the trajectory+behavioral portion**, not just an additive term — this is what actually demotes honeypots instead of just slightly lowering their rank.

```
final_score = TrustScore × ( w1·StaticFit + w2·TrajectoryScore + w3·Convertibility )
```

**Suggested starting weights** (tune during the hackathon, but defend these in the demo):

| Component | Weight | Why |
|---|---|---|
| StaticFit | 0.25 | Table stakes — needs to matter, but shouldn't dominate (that's the "obvious" trap) |
| TrajectoryScore | 0.40 | The core differentiator — this is the thesis of the project |
| Convertibility | 0.35 | A perfect-fit candidate who won't respond is worthless to the recruiter persona |
| TrustScore | multiplicative gate, range 0.0–1.0 | Zeroes out or heavily discounts everything else for honeypots |

### 6.2 Sub-score composition

```
StaticFit = 0.5·title_skill_similarity + 0.3·skill_overlap_weighted + 0.2·education_experience_band

TrajectoryScore = 0.35·career_velocity + 0.25·transition_relevance
                + 0.20·skill_acquisition_rate + 0.20·(1 − normalized_time_to_role_estimate)

Convertibility = 0.20·recency_factor + 0.15·open_to_work + 0.15·recruiter_response_rate
               + 0.15·interview_completion_rate + 0.15·offer_acceptance_rate
               + 0.10·notice_period_factor + 0.10·work_mode_and_relocation_match

TrustScore = 1 − clip(0.4·timeline_inconsistency + 0.3·skill_stuffing_ratio
               + 0.3·synthetic_pattern_score, 0, 1)
```

### 6.3 Worked Example (illustrative — plug in real extracted values at build time)

**Candidate A — "the obvious pick"**
- Title: *Senior AI Engineer* (exact match) | 4 years experience | 22 skills, low avg. endorsements | flat career history, no upward title movement | `recruiter_response_rate`: 0.31 | `last_active`: 90 days ago

```
StaticFit          = 0.5(0.95) + 0.3(0.70) + 0.2(0.55) = 0.79
TrajectoryScore     = 0.35(0.20) + 0.25(0.15) + 0.20(0.25) + 0.20(0.30) = 0.215
Convertibility      = 0.20(0.10) + 0.15(0)   + 0.15(0.31) + 0.15(0.40) + 0.15(0.35) + 0.10(0.20) + 0.10(0.50) = 0.225
TrustScore          = 1 − clip(0.4(0.1) + 0.3(0.6) + 0.3(0.2), 0,1) = 1 − 0.26 = 0.74

final_score = 0.74 × (0.25·0.79 + 0.40·0.215 + 0.35·0.225)
            = 0.74 × (0.1975 + 0.086 + 0.07875)
            = 0.74 × 0.36225 ≈ 0.268
```

**Candidate B — "the underrated pick"**
- Title: *ML Engineer II* (not exact title match) | 3 years experience | 11 skills, high endorsements + duration | two promotions in 3 years, each toward more senior AI-adjacent scope | `recruiter_response_rate`: 0.88 | `last_active`: 2 days ago | high GitHub activity

```
StaticFit          = 0.5(0.65) + 0.3(0.80) + 0.2(0.60) = 0.685
TrajectoryScore     = 0.35(0.85) + 0.25(0.90) + 0.20(0.75) + 0.20(0.80) = 0.8275
Convertibility      = 0.20(0.95) + 0.15(1)   + 0.15(0.88) + 0.15(0.90) + 0.15(0.70) + 0.10(0.60) + 0.10(0.80) = 0.8615
TrustScore          = 1 − clip(0.4(0) + 0.3(0.05) + 0.3(0.05), 0,1) = 1 − 0.03 = 0.97

final_score = 0.97 × (0.25·0.685 + 0.40·0.8275 + 0.35·0.8615)
            = 0.97 × (0.17125 + 0.331 + 0.301525)
            = 0.97 × 0.803775 ≈ 0.780
```

**Candidate C — "the honeypot"**
- Title: *Senior AI Engineer* (exact match, suspiciously perfect) | 2 years experience | 41 skills, near-zero endorsements on most | 6 certifications obtained in 8 months | overlapping employment dates in `career_history`

```
StaticFit          = 0.5(0.97) + 0.3(0.85) + 0.2(0.40) = 0.825   ← looks amazing on paper
TrajectoryScore     = 0.35(0.10) + 0.25(0.05) + 0.20(0.60) + 0.20(0.15) = 0.2
Convertibility      = (mid-range, ~0.40)
TrustScore          = 1 − clip(0.4(0.9) + 0.3(0.9) + 0.3(0.85), 0,1) = 1 − 1.0 → clipped to 1 − 1.0 = 0 (capped)

final_score = 0.0 × (anything) = 0.0   ← correctly demoted to the bottom
```

**Result: B (0.780) > A (0.268) > C (0.0).** This three-candidate contrast *is the demo.* It directly proves the thesis: the literal title-match (A) loses to the trajectory-strong candidate (B), and the keyword-stuffed honeypot (C) gets zeroed out despite the best-looking resume on paper.

---

## 7. Output Spec

CSV, exactly 100 rows:

| Column | Type | Rule |
|---|---|---|
| `rank` | int | 1–100, unique, sequential |
| `candidate_id` | string | from source pool |
| `score` | float | strictly non-increasing down the list |
| `reasoning` | string | 1–2 sentences, template-built from real extracted features, no invented facts |

Tie-break: deterministic by `candidate_id` ascending.

---

## 8. Build Plan (24–48 hr scope, CPU-only)

| Phase | Hours | Deliverable |
|---|---|---|
| 1. Ingest + canonicalization | 0–4 | Clean normalized records, skill/title lookup table |
| 2. Feature builder (A–D) | 4–12 | Per-candidate feature vector for all 100K |
| 3. Graph layer (BFS adjacency only) | 12–18 | `role_adjacency_distance` feature merged in |
| 4. Shield layer | 18–24 | `TrustScore` validated against known synthetic patterns in sample data |
| 5. Ranker + calibration | 24–30 | Top 100 CSV draft, score monotonicity verified |
| 6. Reason generator | 30–36 | Reasoning text attached, spot-checked for hallucination |
| 7. Demo prep | 36–44 | 3-candidate contrast slide, judge script, backup static screenshots |
| 8. Buffer / polish | 44–48 | Bug fixes, re-run on full pool, final export |

**Cut list if time runs short (in order):** graph layer first (fall back to title-similarity only), then convertibility sub-features (keep top 4 of 7), then reasoning template sophistication (fall back to simpler bullet format). **Never cut:** the Shield layer or the three-candidate demo contrast — those are what wins.

---

## 9. Demo & Judge Script

**Opening line:** *"We rejected candidate matching as the core framing. This is a trajectory-and-trust problem, not a search problem."*

1. State the 20 obvious approaches considered and rejected, in one breath — signals rigor without dwelling.
2. Show the dataset's hidden structure: handful of literal title matches, 23 behavioral signals, explicit traps.
3. Walk the three-candidate contrast (§6.3) live — this is the moment judges remember.
4. Show the architecture diagram (§4) in under 60 seconds — system thinking, not just a model.
5. Close: *"This isn't a better ranker. It's a talent intelligence engine for finding overlooked people, filtering out fake ones, and predicting who actually converts."*

---

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Feature builder too slow on 100K rows | Vectorize with pandas/NumPy; avoid per-row Python loops where possible |
| Graph BFS too slow / graph too sparse to be useful | Cap to 2-hop adjacency; fall back to title-similarity if it underperforms by phase 3 checkpoint |
| Trust rules too aggressive, demote real candidates | Use continuous penalty, not hard cutoff; validate against sample candidates with known labels before running full pool |
| Reasoning text drifts into hallucination if LLM-assisted | Keep LLM strictly to prose-smoothing of pre-extracted facts; unit-test a sample of outputs against source data |
| Running out of time | Follow the cut list in §8 — Shield layer and demo contrast are non-negotiable; everything else is gradeable |
