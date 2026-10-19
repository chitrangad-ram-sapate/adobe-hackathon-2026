# Part 2 voice-over — FINAL take (26 Sep, 19:05)

Recording: `evidence/final clips/part_final_final.mp4` (4:14 raw; trim to ≤ 2:00)
Report: `evidence/final/audit-report.json` (audited 13:37 UTC = 19:07 local)

What that run found:
- **23 findings, overall 50.2/100**, 27 pages read in **51 seconds**, JavaScript rendering on
- Gate scores: access 54, render 38, extract 53, trust 73, engagement 38
- Top of the fix-priority table:
  - **F-001 ACC-018**: critical severity, low effort, so **critical** priority. englishtest.duolingo.com/faq has its canonical on testcenter.zendesk.com (1 of 21 pages)
  - **F-002 RND-001**: critical severity, high effort, so **high** priority. Homepage 0 vs 163 words, /team 0 vs 1,280, schools/help 0 vs 496
  - **F-003 SDA-006**: high severity, medium effort, so **high** priority. No Organization/WebSite JSON-LD on the homepage
- On screen, the launch line is typed exactly as in REPLAY, followed by version, hash, the prompt and `Skill(audit-orchestrator)`.

Total narration is about **240 words ≈ 1:40**. Each 🎬 line says what should be on screen while you speak; trim the video so it lines up. Read the text in quotes.

---

### 1 · Identity and hash
🎬 `claude --version`, then the `Get-FileHash` output

> "This is Claude Code 2.1.281, driving Claude Opus 5.5. That hash is our exact Round 3 zip."

### 2 · Launch and URL
🎬 The `claude --model … --allowedTools …` line, then the prompt being pasted, then Enter

> "We launch the harness with the exact command from our REPLAY file, and paste its prompt word for word. The target is duolingo.com. It's not in our corpus."

### 3 · The agent runs our engine
🎬 `Skill(audit-orchestrator)`, then the `run_audit.py` command (cut the waiting)

> "Claude Code loads our audit-orchestrator skill, which runs our Python engine. The findings come from the engine; the model only drives it and summarises. It read 27 pages, rendered three with Playwright, and ran all six detectors in about fifty seconds."

### 4 · The result
🎬 The table appearing

> "Twenty-three findings, overall 50 out of 100. Render and engagement are weakest, at 38."

### 5 · First by priority: ACC-018
🎬 Row F-001 (ACC-018), then the agent's evidence for it

> "First by fix priority is ACC-018. One help page, englishtest.duolingo.com slash faq, declares its canonical on testcenter.zendesk.com, so systems credit that page to Zendesk. The fix is a self-referencing canonical: cheap, so it ranks first. To be fair, on one page of twenty-one it arguably shouldn't rate critical, and we say so in REPLAY."

### 6 · The biggest problem: RND-001
🎬 Row F-002 (RND-001) and its evidence table (0 / 163, 0 / 1,280, 0 / 496)

> "The biggest site-wide problem is RND-001. All three rendered pages ship zero words in their server HTML. The homepage has 0 against 163 after JavaScript, and the team page 0 against 1,280."

🎬 Browser, view-source tab, scrolling

> "This is what an AI crawler receives: scripts, nothing to quote. It's measured with a real browser, using the same extractor on both sides, so confidence is high. Zero coverage is under our 0.30 line, which makes it critical. Fix: server-render that content. Verify: re-run RND-001 and check coverage exceeds 0.75."

### 7 · Prioritisation
🎬 The table, showing the priority and effort columns for F-001 to F-003

> "That's severity crossed with effort. ACC-018 is cheap, so it's critical priority. RND-001 is critical but high effort, so it sits at high, level with the missing Organization JSON-LD."

### 8 · Caveat and close
🎬 The table, or the end of the agent's answer

> "One caveat: the dead-end and no-action findings read the server HTML, and the render gap is their real cause. It's all in our REPLAY file. Thanks!"

---

## If Part 2 runs over 2:00, cut in this order
1. Section 3's last sentence ("It read 27 pages…")
2. Section 4
3. Section 5's last sentence ("To be fair…"). Keep it if you can: REPLAY mentions it, and judges value the honesty.

## Trimming the 4:14 recording to ≤ 2:00 (Clipchamp)
1. **Work on a copy** of `part_final_final.mp4`. Never edit the original.
2. Mute the clip's own audio: select the clip → **Audio** → volume **0**.
3. Cut **only waiting time** (spinners, "Thinking…", long pauses). Keep all of these:
   - `claude --version` and the hash
   - the `claude --model …` launch line and Enter
   - the prompt paste and Enter
   - `Skill(audit-orchestrator)` and the `run_audit.py` command
   - the table, the ACC-018 and RND-001 evidence, and the view-source scroll
4. **Record → Voice**, section by section, lining each one up with its 🎬 moment.
5. Place it after Part 1 and check: **Part 2 ≤ 2:00, total ≤ 5:00** (aim for about 4:50).
