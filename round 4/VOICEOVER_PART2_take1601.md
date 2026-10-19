# Part 2 voice-over — final take (26 Sep, 16:01)

Recording: `evidence/2026-09-26 16-01-39.mp4`
Report: `evidence/final/audit-report.json` (audited 10:33 UTC)

What that run found:
- **23 findings, overall 50.2/100**, 29 pages crawled in **51 seconds**
- Gate scores: access 54, render 38, extract 53, trust 73, engagement 38
- Top of the fix-priority table:
  - **F-001 ACC-018**: critical severity, low effort, so **critical** priority
  - **F-002 RND-001**: critical severity, high effort, so **high** priority
  - **F-003 SDA-006**: high severity, medium effort, so **high** priority
- The findings are identical to two other live crawls earlier that day (take 1 at 14:16 and the 14:56 run).

Total narration is about **250 words ≈ 1:45**. Each 🎬 line says what should be on screen while you speak; trim the video so it lines up. Read the text in quotes.

---

### 1 · Identity and hash
🎬 `claude --version`, then the `Get-FileHash` output

> "This is Claude Code 2.1.281, driving Claude Opus 5.5. That hash is our exact Round 3 zip."

*(Only if `verify_engine.py` appears in the take, add: "…and the folder we're running is identical to it.")*

### 2 · Launch and URL
🎬 Pasting the launch command, then the prompt with the URL, then Enter

> "We paste the exact launch command and prompt from our REPLAY file. The target is duolingo.com. It's not in our corpus."

### 3 · The agent runs our engine
🎬 `Skill(audit-orchestrator)`, then the `run_audit.py` command (cut the waiting)

> "Claude Code calls our real audit-orchestrator skill, which runs our Python engine. The findings come from the engine; the model just drives it. It crawled 29 pages, rendered three with Playwright, and ran all six detectors in about fifty seconds."

### 4 · The result
🎬 The summary line and the top of the table

> "Twenty-three findings, overall 50 out of 100. Render and engagement are weakest, at 38."

### 5 · First by priority: ACC-018
🎬 Row F-001 (ACC-018), then the agent's evidence for it

> "First by fix priority is ACC-018. One help page, englishtest.duolingo.com slash faq, declares its canonical on testcenter.zendesk.com, so systems credit that page to Zendesk. The fix is a self-referencing canonical: cheap, so it ranks first. To be honest, on one page of twenty-two it arguably shouldn't rate critical, and we note that in REPLAY."

### 6 · The biggest problem: RND-001
🎬 Row F-002 (RND-001), then its evidence

> "The biggest site-wide problem is RND-001. All three rendered pages ship zero words in their server HTML. The homepage has 0 against 163 after JavaScript, and the team page 0 against 1,327."

🎬 Browser, view-source tab, scrolling

> "This is what an AI crawler receives: scripts, nothing to quote. It's measured with a real browser, using the same extractor on both sides, so confidence is high. Zero coverage is under our 0.30 line, which makes it critical. Fix: server-render that content. Verify: re-run RND-001 and check coverage exceeds 0.75."

### 7 · Prioritisation
🎬 The table, showing the priority and effort columns for F-001 to F-003

> "That's severity crossed with effort. ACC-018 is cheap, so it's critical priority. RND-001 is critical but high effort, so it sits at high, level with the missing Organization JSON-LD."

### 8 · Caveat and close
🎬 The table or the end of the agent's answer

> "One caveat: the dead-end and no-action findings read the server HTML, and the render gap is their real cause. It's all in our REPLAY file. Thanks!"

---

## If Part 2 runs over 2:00, cut in this order
1. Section 3's last sentence ("It crawled 29 pages…")
2. Section 5's last sentence ("To be honest…"). Keep it if you can: judges value the honesty, and REPLAY mentions it.
3. Section 4

## Recording the voice-over in Clipchamp
1. Import `2026-09-26 16-01-39.mp4`. **Work on a copy. Never edit the original.**
2. Cut only waiting time. Keep the paste, the Enter, the Skill call, the table and the view-source scroll.
3. Mute the clip's own audio: select the clip → **Audio** → volume **0**.
4. **Record → Voice** (or record in the Windows Sound Recorder app and import it). Record section by section, lining each one up with its 🎬 moment.
5. Check the final Part 2 length is **≤ 2:00**.
