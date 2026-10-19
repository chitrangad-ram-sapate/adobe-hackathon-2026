# Round 4 video script — Delulu Devs

Hard cap 5:00. Part 1 ≤ 3:00, Part 2 ≤ 2:00. The narration below is roughly
355 + 160 words, which is about 2:25 + 1:05 of speech at a normal pace (the rest is tab switching and the live run). **Rehearse it
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

## PART 1 — Thought process (≤ 3:00, about 2:40 spoken)

### 0:00–0:20 · The model

**[SHOW `marketplace.json`]**
> "We're Delulu Devs. Our marketplace is eight skills behind one entrypoint, `audit-orchestrator`. Our research showed an AI assistant reaches a brand's facts through a fixed pipeline: it must *access* the page, *render* it, *extract* a quotable fact, and *trust* it. Then the visitor it sends must *engage*. Every check belongs to exactly one of those gates."

### 0:20–1:05 · How we discovered the findings

**[SHOW `render-gap-playbook.md` line 67]**
> "Each signal lives in a reference catalogue with its threshold and a 'do not flag when' clause. `check_consistency.py` fails the build if code and catalogue drift apart."

**[SHOW `check_render.py` lines 105–112]**
> "Our key lesson came from live sites. Our first render check compared whole-page text, and JavaScript menus made server-rendered python.org look 73% broken. Now we compare *main content only*, with the same extractor on both sides: line 105. Server-rendered sites score 99 to 100%, client-rendered ones 3% or less, so the 0.75 threshold sits in empty space. False positives went from 8 to 0 across 71 sites, and it started catching Notion."

**[SHOW `check_identity.py` line 454]**
> "Off-site, we verify the profiles a site claims in `sameAs`. A 404 is a dead claim. A 403 is only unverified: blocked is not dead."

### 1:05–1:50 · How we assign severity

**[SHOW `severity-rubric.md` section 2]**
> "Severity measures how much of the site's ability to be found or cited a defect removes. Critical means a whole gate closed, site-wide."

**[SHOW `findings.py` — `apply_blast_radius`]**
> "It's enforced in code: every detector emits through `findings.py`. Blast radius adjusts it: a defect on 80% of pages goes up a level, and one under 20% goes down, so one broken page is never reported as site-wide."

**[SHOW `compose_report.py` lines 70 and 126]**
> "Gates are sequential, so if the crawler is blocked, `apply_gate_precedence` demotes downstream findings. And a measured check always outranks an estimate: RND-001 supersedes RND-002."

### 1:50–2:40 · How we derive and prioritise fixes

**[SHOW an example finding in `examples/example-real-site.json`]**
> "Every finding carries its evidence, the *mechanism*, meaning why it stops an AI citing you, concrete steps, and a `verify` line naming the check to re-run. A fix with a mechanism can be checked."

**[SHOW `findings.py` `PRIORITY_MATRIX`]**
> "Priority is severity crossed with effort, so a cheap fix for a medium problem comes before an expensive fix for a high one."

**[SHOW `plan_remediation.py` line 236]**
> "The remediation planner rewrites each fix for the site's own CMS or framework."

**[SHOW `tests/sites.txt`]**
> "We validated on 71 live sites: all completed, all schema-valid, none over five minutes. Today's site isn't on this list."

---

## PART 2 — Trial run (≤ 2:00)

> **FINAL:** the take used in the video is `evidence/final clips/part_final_final.mp4`. Its voice-over script, matched to that run's report, is in **`VOICEOVER_PART2.md`**. The narration below is the earlier generic version.

**Setup (before hitting record):**
- Run `.\open_demo.ps1` from `d:\Adobe\round 4`: this gives a clean demo folder with every file open.
- Run Claude Code in a **separate PowerShell window** snapped to the right half, with VS Code (REPLAY) on the left. Never use the VS Code terminal: it links Claude to your editor. Close all other windows.
- Browser tab 1: `view-source:https://www.duolingo.com/`. Tab 2: `https://www.duolingo.com/`.
- Rehearse on a different site, **not** Duolingo.

### 0:00–0:15 · Identity and wiring
Run `claude --version`, then `Get-FileHash ..\..\brand-ai-readiness-audit.zip`.
> "Claude Code 2.1.281, driving Claude Opus 5.5. That hash is our exact Round 3 zip. Claude Code calls our real `audit-orchestrator` skill, which runs our Python engine. The findings come from the engine; the model just drives it."

### 0:15–0:40 · Enter the URL (one continuous take; trim idle only)
Copy the launch command from REPLAY on camera, paste it and run it. Then copy the step 2 prompt, paste it, pause for a second, and press Enter.
> "duolingo.com, not in our corpus. There's the skill call… crawling, rendering with Playwright, running the six detectors."
*(Cut the waiting time. Keep the Skill call, the `run_audit.py` command and the result all visible.)*

### 0:40–1:30 · Drill into the findings (matches take 1, 26 Sep)
The agent's table puts **ACC-018** first by fix priority and **RND-001** second. Name ACC-018 briefly and honestly, then drill into RND-001, the biggest site-wide defect.

Hover over row F-001 (ACC-018):
> "First by fix priority is ACC-018: one help page, englishtest-dot-duolingo-slash-faq, declares its canonical on zendesk.com, so credit for it goes to Zendesk. It's real and cheap to fix, though on one page of twenty-two it arguably shouldn't rate critical. We've noted that in REPLAY. The biggest site-wide problem is next: RND-001."

Hover over row F-002 (RND-001), then scroll to its evidence:
> "Three of three rendered pages ship zero words in their server HTML. The homepage has 0 against 163 after JavaScript, and the team page 0 against 1,327."

Switch to the view-source tab and scroll: nothing but scripts, no `<h1>`, no text.
> "This is what an AI crawler gets: scripts, nothing to quote. It's measured with a real browser, so confidence is high. Critical because 0% coverage is under our 0.30 line. Fix: server-render that content. Verify: re-run RND-001, and coverage should exceed 0.75."

### 1:30–1:50 · Prioritisation
Back in the terminal, scroll so rows F-002 and F-003 are both visible.
> "Priority is severity crossed with effort. That's why RND-001, critical but high effort, sits level with the missing Organization JSON-LD, which is high severity but medium effort. Cheap fixes aren't buried under expensive ones."

### 1:50–2:00 · Honest limitation
> "One caveat: the dead-end and no-action findings read the server HTML, and the render gap is their real cause. It's all in our REPLAY file. Thanks!"

*If a retake shows **RND-001 at the top** instead (the Zendesk page returned 403 that time), skip the ACC-018 paragraph and start at "Three of three rendered pages…".*

---

## Integrity checklist (tick before submitting)

- [ ] Part 2 is one real session: the URL is entered on camera and only waiting time is cut.
- [ ] The model, harness version, URL and prompt on screen match `REPLAY_DeluluDevs.txt` word for word.
- [ ] The uncut raw recording and that run's `audit-report.json` are archived in `d:/Adobe/round 4/evidence/`.
- [ ] Every Part 1 claim had its file on screen.
- [ ] Total ≤ 5:00, Part 1 ≤ 3:00, Part 2 ≤ 2:00.
- [ ] Claude Code hasn't auto-updated since REPLAY was written (`claude --version` = 2.1.281), otherwise update REPLAY.
- [ ] A teammate replayed REPLAY cold and got the same substance.
