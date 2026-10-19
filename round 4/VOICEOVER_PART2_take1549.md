# Part 2 voice-over — final take (26 Sep, 15:49)

Recording: `evidence/2026-09-26 15-49-25.mp4`
Report: `evidence/final/audit-report.json`

What that run found:
- **22 findings, overall 58.2/100**, 28 pages crawled in **57 seconds**
- Gate scores: access 94, render 38, extract 53, trust 73, engagement 38
- Top two by fix priority: **F-001 RND-001** (critical), **F-002 SDA-006** (high)

Total narration is about **230 words ≈ 1:35**. Each 🎬 line says what should be on screen while you speak; trim the video so it lines up. Read the text in quotes.

---

### 1 · Identity and hash
🎬 `claude --version`, then the `Get-FileHash` output

> "This is Claude Code 2.1.281, driving Claude Opus 5.5. That hash is our exact Round 3 zip, and the folder we're running is identical to it."

### 2 · Launch and URL
🎬 Pasting the launch command, then the prompt with the URL, then Enter

> "We paste the exact launch command and prompt from our REPLAY file. The target is duolingo.com. It's not in our corpus."

### 3 · The agent runs our engine
🎬 `Skill(audit-orchestrator)`, then the `run_audit.py` command (cut the waiting)

> "Claude Code calls our real audit-orchestrator skill, which runs our Python engine. The findings come from the engine; the model just drives it. It crawled 28 pages, rendered three with Playwright, and ran all six detectors in under a minute."

### 4 · The result
🎬 The summary line and the top of the findings table

> "Twenty-two findings, overall 58 out of 100. Render and engagement are the weakest gates, at 38 each."

### 5 · Top finding: RND-001
🎬 Row F-001 (RND-001), then the agent's evidence for it

> "Top finding, critical: RND-001. All three rendered pages ship zero words in their server HTML. The homepage has 0 against 163 after JavaScript, the team page 0 against 1,327, and the schools help page 0 against 496."

🎬 Browser, view-source tab, scrolling

> "This is what an AI crawler receives: scripts, nothing to quote. It's measured with a real browser, using the same extractor on both sides, so confidence is high. Zero percent coverage is under our 0.30 line, which makes it critical. The fix is to server-render or pre-render that content, and the verify step is to re-run RND-001 and check coverage exceeds 0.75."

### 6 · Second finding: SDA-006
🎬 Row F-002 (SDA-006) and its evidence

> "Second, SDA-006: the homepage has no Organization or WebSite JSON-LD, so no machine-readable statement of who Duolingo is. Fix: add Organization markup to the home template."

### 7 · Prioritisation
🎬 The table, showing the fix priority and effort columns (rows F-001 to F-007)

> "Priority is severity crossed with effort. RND-001 is critical but high effort, so it sits at high priority, level with cheap fixes like the missing H1, which is medium severity but low effort. And because the site type was unknown, the engine skipped the price and comparison checks rather than guess."

### 8 · Caveat and close
🎬 The table or the end of the agent's answer

> "One caveat: the dead-end and no-action findings read the server HTML, and the render gap is their real cause. It's all in our REPLAY file. Thanks!"

---

## Recording the voice-over in Clipchamp
1. Import `2026-09-26 15-49-25.mp4`. **Make a copy first. Never edit the original.**
2. Cut only waiting time. The paste, the Enter, the Skill call, the table and the view-source scroll all stay.
3. Mute the clip's original audio: right-click the clip → **Audio** → volume **0**.
4. **Record → Voice** (or record in the Windows Sound Recorder app and import it). Read section by section, lining each one up with its 🎬 moment.
5. Part 2 should come to **≤ 2:00**. If it runs long, drop the last sentence of section 7 ("And because the site type was unknown…").
