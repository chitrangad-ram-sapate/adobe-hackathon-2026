# Round 4 video script — Delulu Devs

Hard cap 5:00. Part 1 ≤ 3:00, Part 2 ≤ 2:00. The narration below is roughly
420 + 230 words, which is about 2:50 + 1:45 at a normal pace. **Rehearse it
against a stopwatch.**

Rule for every sentence in Part 1: the file named in the **[SHOW]** cue must be
on screen when you say it. A claim without code on screen earns no credit.

Before recording, open these files in VS Code tabs, in order, from
`d:/Adobe/round 4/demo/brand-ai-readiness-audit/` (the fresh extract):

1. `marketplace.json`
2. `skills/render-extractability-audit/references/render-gap-playbook.md` (line 67)
3. `skills/render-extractability-audit/scripts/check_render.py` (lines 105–112)
4. `skills/audit-orchestrator/references/severity-rubric.md` (section 2, line 32)
5. `lib/auditlib/findings.py` (lines 17–60)
6. `skills/audit-orchestrator/scripts/compose_report.py` (lines 70, 126)
7. `skills/entity-corroboration-audit/scripts/check_identity.py` (line 454)
8. `skills/remediation-planner/scripts/plan_remediation.py` (line 236)
9. `tests/sites.txt`

---

## PART 1 — Thought process (≤ 3:00)

### 0:00–0:20 · The model

**[SHOW `marketplace.json`]**
> "We're Delulu Devs. Our marketplace is eight agentskills-format skills behind one entrypoint, `audit-orchestrator`. The idea came from field research: an AI assistant reaches a fact about a brand through a fixed pipeline. It has to *access* the page, *render* it, *extract* a quotable fact, and *trust* it enough to repeat it. Then the human it sends has to *engage*. Every check we built belongs to exactly one of those gates. That's the six detector skills you see here."

### 0:20–1:10 · How we discovered the findings

**[SHOW `render-gap-playbook.md` line 67]**
> "Every signal lives in a reference catalogue with its threshold *and* a 'do not flag when' clause. That's what keeps precision up on a site we've never seen. `tests/check_consistency.py` fails the build if code and catalogue drift apart."

**[SHOW `check_render.py` lines 105–112]**
> "Here's the non-obvious lesson. Our first render-gap check compared whole-page text, raw against rendered. On real sites JavaScript expands navigation menus, so python.org, a server-rendered site, scored 73% coverage and looked broken. We changed it to compare *main content* only, using the same extractor on both sides: `main_word_count`, line 105. Server-rendered sites now sit at 99 to 100%, client-rendered ones at 3% or less, and the 0.75 threshold falls in empty space between them. False positives dropped from 8 to 0 across our 71-site corpus, and it began catching Notion, which it had missed before."

**[SHOW `check_identity.py` line 454]**
> "The same discipline applies off-site. We verify the social profiles a site claims in `sameAs`. A 404 counts as a dead identity claim, but a 403 is only *unverified*. Blocked is not dead, and we never charge a site for it."

### 1:10–2:00 · How we assign severity

**[SHOW `severity-rubric.md` section 2]**
> "Severity answers one question: how much of the site's ability to be found or cited does this defect remove? `critical` means it closes a whole gate for the whole site."

**[SHOW `findings.py` — `apply_blast_radius`]**
> "The rubric is enforced in code, not by good intentions. Every detector emits through `findings.py`. Blast radius scales severity: a defect on 80% of sampled pages goes up one level, and one under 20% goes down one level. So one broken page never gets reported as site-wide."

**[SHOW `compose_report.py` lines 70 and 126]**
> "The gates are sequential, so precedence matters. If the crawler gets a 403, a missing Product schema isn't the real problem, and `apply_gate_precedence` demotes it. When two checks measure the same defect, the measured one wins over the estimate: RND-001 supersedes RND-002. Confidence stays separate from severity, so a guess is never presented as a measurement."

### 2:00–2:50 · How we derive and prioritise fixes

**[SHOW an example finding in `examples/example-real-site.json`]**
> "Every finding carries four things: the evidence, the *mechanism* explaining why this defect stops an AI citing you, concrete steps, and a `verify` line saying which check to re-run to prove the fix worked. A fix that states its mechanism can be checked. One that doesn't is just advice."

**[SHOW `findings.py` `PRIORITY_MATRIX`]**
> "Priority is severity crossed with effort. A cheap fix for a medium problem is scheduled before an expensive fix for a high one."

**[SHOW `plan_remediation.py` line 236]**
> "The remediation planner then fingerprints the CMS or framework and rewrites each fix into steps for that stack."

**[SHOW `tests/sites.txt`]**
> "We validated on 71 live sites across ten segments: all 71 completed and schema-valid, with no crashes and none over the five-minute budget. The site you're about to see isn't on this list."

---

## PART 2 — Trial run (≤ 2:00)

**Setup (before hitting record):**
- Terminal font of at least 18 pt, dark theme, maximised window. Close all other windows.
- Browser tab 1: `view-source:https://www.duolingo.com/`. Tab 2: `https://www.duolingo.com/`.
- A fresh extract in `d:/Adobe/round 4/demo/` with the `.claude/skills` junction, and no old `audit-report.*` files.
- Do a take-0 rehearsal **on a different site**, not duolingo, so the demo run is the audit's first contact with it.

### 0:00–0:15 · Identity and wiring (camera on terminal)
Type and run `claude --version`, then `Get-FileHash ..\..\brand-ai-readiness-audit.zip`.
> "This is Claude Code 2.1.281 driving Claude Opus 5.5. This hash is the exact Round 3 zip we submitted, freshly extracted. Claude Code will invoke our real entrypoint, the `audit-orchestrator` skill, which runs our Python engine. Every finding comes from that engine. The model only drives the run and explains the result."

### 0:15–0:45 · Enter the URL (one continuous take; trim idle only)
Run the `claude --model claude-opus-5-5 --allowedTools ...` command from REPLAY, then type the prompt **exactly** as written in REPLAY step 2.
> "duolingo.com isn't in our corpus. Watch it call the skill… it's crawling, rendering pages with Playwright, and running the six detectors."
*(Cut the waiting time. Keep the Skill call, the `run_audit.py` command and the result all visible.)*

### 0:45–1:35 · Drill into one finding
When the sorted list appears:
> "The top finding is critical: RND-001, content assembled by JavaScript. The evidence: the homepage's server response has 0 words of main content, and after JavaScript runs it has 163."

Switch to the view-source tab and scroll: nothing but scripts, no `<h1>`, no text.
> "Here's the raw HTML an AI crawler gets: script tags and nothing to quote. The engine measured this with the same extractor on both sides, which is why the method says `rendered` and the confidence is high. It's critical because coverage is 0%, below the 0.30 critical line in our playbook, and it holds on three of three rendered pages, so the render gate is closed site-wide. The fix is to server-render or pre-render that content. It carries a verify step: re-run RND-001 and coverage should exceed 0.75."

### 1:35–1:55 · Prioritisation
Scroll the agent's table, sorted by fix priority.
> "And these are the fixes sorted by priority, which is severity crossed with effort. Look at where a cheap fix like the homepage Organization JSON-LD lands compared with the expensive server-rendering work."
*(Read the actual priority and effort values off the screen. Don't recite these words if the table shows something else.)*

### 1:55–2:00 · Honest limitation (one line)
> "One caveat you'll see in the report: two engagement findings read the server HTML, and the render gap is their real cause. It's all in our REPLAY file. Thanks!"

---

## Integrity checklist (tick before submitting)

- [ ] Part 2 is one real session: the URL is typed on camera and only waiting time is cut.
- [ ] The model, harness version, URL and prompt on screen match `REPLAY_DeluluDevs.txt` word for word.
- [ ] The uncut raw recording and that run's `audit-report.json` are archived in `d:/Adobe/round 4/evidence/`.
- [ ] Every Part 1 claim had its file on screen.
- [ ] Total ≤ 5:00, Part 1 ≤ 3:00, Part 2 ≤ 2:00.
- [ ] Claude Code hasn't auto-updated since REPLAY was written (`claude --version` = 2.1.281), otherwise update REPLAY.
- [ ] A teammate replayed REPLAY cold and got the same substance.
