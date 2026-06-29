<!-- Single source of truth for the Kaggle "5-Day AI Agents" Capstone project. -->

# Kaggle Capstone — "AP Copilot" Specification & Plan
_**Hard Deadline: July 6, 2026, 11:59 PM PT**_
_Track: Agents for Business | Framework: ADK 2.0 & Antigravity_

---

## LOCKED DECISIONS (the quick-reference list)

| # | Decision | Call |
|---|----------|------|
| 1 | **Build it?** | **Yes** — high impact Kaggle capstone entry. |
| 2 | **Scope** | **Throwaway demo, certificate-grade.** Fast build focused on Kaggle rubric. |
| 3 | **Team** | **Solo (Hector only).** No registered teammate. |
| 4 | **Advisor** | **Optional finance review** of GL-coding rules + approval thresholds before submit. |
| 5 | **Track** | **Agents for Business** (Kaggle literally names "expense management" as an example). |
| 6 | **Concept** | **"AP Copilot"** — autonomous accounts-payable agent for NetSuite. |
| 7 | **Data** | **Synthetic invoices + NetSuite sandbox/mock ONLY.** Makes the submission publicly shippable. |

**Why solo (the researched answer):** the cert/badge go to every submitter regardless of team — zero upside; adding teammates is pure friction (Kaggle account, phone verify, rules acceptance, team-merge cutoff).

---

## THE CONCEPT — "AP Copilot"

Invoice lands → agent **extracts** it → **codes** it to the right GL account → **validates** against policy → routes anything risky to a **human** → **posts** the approved entry to NetSuite.

**ROI narrative (baked into the demo):** manual AP = **$12.88–$19.83/invoice**, agent-automated = **~$2.36/invoice**. That single line is the core Kaggle pitch hook.

**Why it wins:** real enterprise pain (judges reward business impact), and the **Unit 4 codelab is literally "expense-approval agent with human-in-the-loop triage"** — so it's a re-skin of a Google-provided scaffold, not a from-scratch build. Low risk, high relevance.

---

## ARCHITECTURE — maps to 5 of the 6 OFFICIAL concepts (only need 3)

> ⚠️ **Correction (2026-06-24, official rubric):** the 6 NAMED concepts are **ADK agent/multi-agent · MCP Server · Antigravity · Security features · Deployability · Agent skills (Agents CLI)**. **"Eval" is NOT one of them** — earlier drafts miscounted it. Eval still earns its keep under Technical Implementation (50 pts) and powers the ROI story, but it does not tick a named-concept box.

- **ADK / multi-agent** ✅ [Code] — graph: `Intake → Extractor → GL-Coder → Policy-Validator → Poster`.
- **MCP Server** ✅ [Code] — NetSuite MCP for ERP read/write (vendors, GL accounts, POs) + email/Drive MCP for invoice intake.
- **Agent skills (Agents CLI / SKILL.md)** ✅ [Code/Video] — GL-mapping rules, vendor matching, approval thresholds as one portable skill.
- **Security features** ✅ [Code/Video] — human-in-the-loop gate, sandboxed execution, hard "no auto-post above $X" rule, slopsquatting-safe deps. **Strongest selling point for Agents-for-Business** (money on the line).
- **Antigravity** ✅ [Video] — show the build done in Antigravity (the easy 4th box).
- **Deployability** ⬜ [Video] — optional 6th; deploy is NOT required for judging, but a documented cheap deploy path scores here.
- **(Eval** — build it for the ROI proof + Technical-Implementation points, but it is not a named concept.)

---

## 13-DAY TIMELINE (rough cut)

| Window | Dates | Work |
|--------|-------|------|
| Days 1–2 | Jun 23–25 | Synthetic invoice set + sample GL/vendor tables. Stand up Antigravity + ADK. |
| Days 3–6 | Jun 26–29 | Build the agent graph end-to-end with the human-in-loop gate. |
| Days 7–9 | Jun 30–Jul 2 | Wire MCP (NetSuite sandbox or mock). Package the SKILL.md. |
| Days 10–11 | Jul 3–4 | Eval harness → accuracy/ROI numbers. |
| Days 12–13 | Jul 5–6 | Writeup (≤2,500 words) + cover image + **≤5-min YouTube demo video** + public repo/README. **Submit before 11:59 PM PT Jul 6.** |

---

## THE OBJECTIVE

One build → Kaggle submission + Google/Kaggle badge + certificate (all submitters, by end of July) + shot at top-3 social feature.

---

## SUBMISSION REQUIREMENTS (AUTHORITATIVE — official rules + overview, reviewed 2026-06-24)

All required for a valid submission:
- **Kaggle Writeup** — ≤ **2,500 words** (over = penalty); title + subtitle + analysis; **must select the track** (Agents for Business). Draft/un-submitted Writeups are NOT judged — hit "Submit."
- **Cover image** (required) + **Media Gallery**.
- **YouTube video** ≤ **5 minutes**, published to YouTube. (Earlier "2-min" notes were wrong — you get up to 5; use them for problem → why-agents → architecture → demo → the build.)
- **Public project link** — a live demo URL OR a **public GitHub repo with setup instructions**. ⚠️ **Deploy is NOT required**; a clean repo + README satisfies it. Must be public, no login/paywall.
- **README.md** — problem, solution, architecture, setup instructions, diagrams (worth a full **20 pts**).
- Demonstrate **≥3 of the 6 named concepts** (we map 5 — see Architecture).
- **One submission only** (hackathon rule). Solo, so no team-merge concerns; any pre-merge submissions get unsubmitted.
- ⚠️ A **private Kaggle resource** attached to the public Writeup **auto-publishes after the deadline** — treat everything attached as public.
- Account prereqs: Kaggle account w/ verified phone + Google AI Studio account (set from the course).
- Canonical page: `kaggle.com/competitions/vibecoding-agents-capstone-project`

## SCORING — where the points (and effort) live

| Category | Pts | Breakdown |
|---|---|---|
| **The Pitch** (why/what) | 30 | Core concept & value **10** · YouTube video **10** · Writeup **10** |
| **The Implementation** (how) | 70 | Technical implementation — architecture, code quality, clever tool use, commented code **50** · Documentation / README **20** |

**Effort follows the rubric:** 70% is code + docs, so commented well-architected code and a tight README ARE the game. The 5-min video still carries a full 10 pts (+ the demo) — don't phone it in. **It's a hackathon: human-judged against this rubric by a Google/Kaggle DevRel + DeepMind panel — no leaderboard metric.**

## RULES & TOOLING (locked, from the official rules text §2.5–2.8)

- ✅ **Claude Code is allowed.** §2.6: "the use of external data and models is acceptable unless specifically prohibited by the Host," subject to a Reasonableness Standard (reasonably accessible, minimal cost — they cite a "Gemini Advanced" subscription as acceptable). **No Gemini mandate even for the agent runtime** — Gemini/ADK is *scoring-optimal* (demonstrates course tech), not required.
- **Build with Claude Code, run on ADK/Gemini** — confirmed as a *choice*, not an obligation.
- **Win-only obligations** (prizes are swag / non-monetary — 12 pieces across 4 tracks — so low-stakes, but):
  - Winning submission + its source code licensed **CC-BY 4.0** (open). Fine — throwaway + synthetic data.
  - Any open-source code baked **into the agent** must use an **OSI-approved, commercial-use-OK license** (avoid non-commercial / GPL-incompatible deps inside the agent).
  - **Commercial tools you used** (Claude Code, Gemini API) — don't open-source them; just **identify them + how to procure**.
  - Ship **reproducible code + an environment description**.
- 🚨 **NO API keys / passwords in the code** — the repo goes public. Scrub before submit (matches our security posture).
- **Eligibility:** 18+, US resident ✓, not under US export controls / sanctions ✓.

---

## OPEN ITEMS / RISKS

- [ ] **Antigravity quota** — wrap-up email noted some users hit quota limits; it resets weekly. Don't leave the build to the final 48h.
- [ ] **NetSuite MCP** — confirm a real NetSuite sandbox MCP exists, or build a lightweight mock. (Mock is fine for a throwaway demo.)
- [ ] **GCP billing** — Unit 5 cloud-deploy codelabs need a billing account. Capstone can run local/Colab; skip cloud deploy unless trivially free.
- [ ] **Final finance logic pass** — review GL-logic and approval thresholds before Jul 5.
- [x] ~~Verify the exact submission format~~ — DONE 2026-06-24: full rules + overview reviewed, Submission/Scoring/Rules sections above are authoritative.

---

## STUDY PRIORITY (from the course, in service of this build)
🎯 Unit 3 (Skills/SKILL.md) · Unit 4 (Security + Eval — your real gap) · the Antigravity codelabs (Units 1–3, the only hands-on novelty).
👀 Skim Unit 1–2 whitepapers + 1–2 podcasts. ⏭️ Skip livestream replays + Unit 5 cloud-deploy codelabs.
