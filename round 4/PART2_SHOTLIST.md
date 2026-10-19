# Part 2: every click

Live trial run. It must be **≤ 2:00 after editing**.

**Rules**
- One continuous recording, from `claude --version` to "Thanks!". Never stop OBS in between.
- Waiting time gets cut in editing. A raw take of 4–6 minutes is normal.
- At most **3 takes**, at least **10 minutes apart**.

---

## SETUP (about 10 min, not recorded)

### S0. Label the old recordings (once)
In File Explorer → `d:\Adobe\round 4\evidence\`, rename the earlier Part 2 recordings so they can't be mixed up:
- `2026-09-26 14-14-10.mp4` → `part2_NOT_USED_take1.mp4`
- any recording from the run without check IDs → `part2_NOT_USED_noIDs.mp4`
- `2026-09-26 14-13-55.mp4` (a false start) → delete it

### S1. Open the demo window
1. Press **Win**, type `PowerShell`, press **Enter**.
2. Type `cd "d:\Adobe\round 4"`, press **Enter**.
3. Type `.\open_demo.ps1`, press **Enter**.
4. Check that it prints **ENGINE OK: identical to the submitted zip**. If not, stop and tell Claude.
5. The **"Delulu Devs - Round 4 demo"** window opens. Click anywhere in it.
6. **Win+↑** to maximise.
7. If the file sidebar shows, press **Ctrl+B** to hide it.
8. Right-click the **REPLAY_DeluluDevs.txt** tab → **Close Others**.
9. Close the PowerShell window you used for step 3: click it, type `exit` → **Enter**. (S2 opens a fresh one for the run.)

### S2. Separate PowerShell window beside REPLAY
⚠️ Don't use VS Code's built-in terminal for the run. Inside it, Claude Code links to VS Code, sees your REPLAY selection and reads the file, so the run no longer matches REPLAY. A **separate** PowerShell window has no link.

1. If a VS Code terminal is open, close it: click in it and type `exit` → **Enter**.
2. Press **Win**, type `PowerShell`, press **Enter**. A new PowerShell window opens.
3. In it, type `cd "d:\Adobe\round 4\demo\brand-ai-readiness-audit"` → **Enter**.
4. Press **Ctrl+=** three or four times so the text is large.
5. Press **Win+→** to snap this window to the **right half** of the screen.
6. Click the VS Code demo window and press **Win+←** to snap it to the **left half**. REPLAY is visible on the left.

### S3. Pre-flight (in the PowerShell window)
1. Type `claude --version` → **Enter**. It must show **2.1.281 (Claude Code)**.
2. Type:
   `python "d:\Adobe\round 4\verify_engine.py" "d:\Adobe\round 4\demo"`
   and press **Enter**. It must show **ENGINE OK**.
3. Type `Get-ChildItem audit-report.*` → **Enter**. It must print **nothing**. (If it lists files, delete them with `Remove-Item audit-report.*`.)
4. Type `cls` → **Enter**.
5. ✅ **Check:** the last line must be `PS D:\Adobe\round 4\demo\brand-ai-readiness-audit>`. That means Claude is **not** running. (The folder is already trusted, so no trust prompt will appear.)

### S4. Browser
1. Open the browser. Close every tab, then open a new one.
2. Type `view-source:https://www.duolingo.com/`, press **Enter**. This is **tab 1**.
3. **Ctrl+=** twice to enlarge the text.
4. **Ctrl+T**, type `https://www.duolingo.com/`, press **Enter**. This is **tab 2**.
5. **Ctrl+1** to go back to tab 1.
6. **Alt+Tab** back to VS Code.

### S5. Screen and OBS
1. **Win+N** → turn on **Do not disturb**.
2. Minimise the Claude chat window and everything else. Only two windows are visible: **VS Code (REPLAY) on the left** and the **run PowerShell window on the right**. The browser stays behind them.
3. Open OBS. Speak and check the mic meter moves. **Minimise OBS.**

### S6. Practise the two copies (not recorded)
1. In REPLAY, find **line 17** (`claude --model ...`). Click just **left of the c** in `claude`.
2. **Shift+End**, then **Shift+End** again. The highlight must end after `"Write"`. Press **Esc**.
3. Find **line 19** (`Use the audit-orchestrator skill...`). Click just **left of the U**.
4. **Shift+End** twice. The highlight must end after `top two findings.`. Press **Esc**.

---

## RECORDING

### ▶ Press Ctrl+Shift+1. Stay silent for 1 second.

### Shot 1: Identity and hash
1. Click in the **PowerShell window** (right).
2. Type `claude --version` → **Enter**.
   🎙 *"This is Claude Code 2.1.281, driving Claude Opus 5.5."*
3. Type `Get-FileHash ..\..\brand-ai-readiness-audit.zip` → **Enter**. Hold still for 2 seconds.
   🎙 *"That hash is our exact Round 3 zip."*
4. Optional: type `python ..\..\verify_engine.py ..` → **Enter**.
   🎙 *"And the folder we're running is identical to it, file by file."*
5. 🎙 *"Claude Code calls our real audit-orchestrator skill, which runs our Python engine. The findings come from the engine; the model just drives it."*

### Shot 2: Launch the agent
1. In REPLAY (left), click just left of `claude` on **line 17**.
2. **Shift+End** twice → **Ctrl+C**.
3. Click in the PowerShell window.
   ✅ **Check:** the line you're pasting into starts with `PS D:\Adobe\...>`. If you see Claude's `>` box instead, Claude is already running. Type `/exit` first.
4. **Ctrl+V** (or right-click to paste) → **Enter**.
5. Claude Code starts. Its header shows **Claude Code v2.1.281 · Opus 5.5** and an empty input box `>`.

### Shot 3: Enter the URL
1. In REPLAY, click just left of `Use` on **line 19**.
2. **Shift+End** twice → **Ctrl+C**.
3. Click in the PowerShell window, **inside Claude's input box**.
4. **Ctrl+V**. The prompt appears.
   - If it shows **[Pasted text …]** instead of the full text, that's fine. Point at the highlighted line 19 in REPLAY while you speak.
5. Pause for 1 second.
   🎙 *"The target is duolingo.com. It's not in our corpus."*
6. **Enter**.
   ⚠️ If you ever see **"Selected … lines from … in Visual Studio Code"** or **"Read outside the working directories"**, Claude is linked to VS Code. Press **Esc**, stop recording, and redo S2.

### Shot 4: Let it work
1. When **Skill(audit-orchestrator)** appears:
   🎙 *"There's the skill call."*
2. When **python skills/audit-orchestrator/scripts/run_audit.py …** appears:
   🎙 *"It's running our engine: crawling, rendering with Playwright, running the six detectors."*
3. **If a permission prompt appears**, press **1** (Yes) → **Enter**.
4. **Hands off.** Stay silent for about 2–4 minutes. Don't scroll or click.

### Shot 5: Drill into the findings
Wait until the agent **finishes completely**, meaning the input box `>` is back.

In take 1 the table showed **F-001 = ACC-018** first and **F-002 = RND-001** second. Follow **5A** if that's what you see. If **RND-001 is first**, skip to **5B**.

**5A. ACC-018 (name it briefly)**
1. Scroll the PowerShell window with the mouse wheel until the table's top rows are visible.
2. Hover over row **F-001 (ACC-018)**.
   🎙 *"First by fix priority is ACC-018: one help page, englishtest-dot-duolingo-slash-faq, declares its canonical on zendesk.com, so credit for it goes to Zendesk. It's real and cheap to fix, though on one page of twenty-two it arguably shouldn't rate critical. We've noted that in REPLAY. The biggest site-wide problem is next: RND-001."*

**5B. RND-001 (the main drill-down)**
1. Hover over row **F-002 (RND-001)**, then scroll to where the agent quotes its evidence (0 against 163, and so on).
   🎙 *"Three of three rendered pages ship zero words in their server HTML. The homepage has 0 against 163 after JavaScript, and the team page 0 against 1,327."*
   ⚠️ Say the **numbers on screen**, even if they differ.
2. Optional, to show the report file:
   - Click the **VS Code window** (left) first
   - **Ctrl+P** → type `audit-report.md` → **Enter**
   - **Ctrl+F** → type `RND-001` → **Enter**
   - Hover over its evidence, fix and verify lines
   - Click the **PowerShell window** to go back
3. **Alt+Tab** to the browser, which opens on **tab 1 (view-source)**.
4. Scroll slowly down with the mouse wheel.
   🎙 *"This is what an AI crawler gets: scripts, nothing to quote. It's measured with a real browser, so confidence is high. Critical because 0% coverage is under our 0.30 line. Fix: server-render that content. Verify: re-run RND-001, and coverage should exceed 0.75."*
5. Optional: **Ctrl+2** for 2 seconds (the page a human sees) → **Ctrl+1**.
6. **Alt+Tab** back, then **click inside the PowerShell window** so the wheel scrolls it again.

### Shot 6: Prioritisation
1. Scroll the PowerShell window so rows **F-002 (RND-001)** and **F-003 (SDA-006)** are both visible.
2. Hover over the **Fix priority** and **Effort** columns of those two rows.
   🎙 *"Priority is severity crossed with effort. That's why RND-001, critical but high effort, sits level with the missing Organization JSON-LD, which is high severity but medium effort. Cheap fixes aren't buried under expensive ones."*

### Shot 7: Caveat and close
1. 🎙 *"One caveat: the dead-end and no-action findings read the server HTML, and the render gap is their real cause. It's all in our REPLAY file. Thanks!"*
2. Stay silent for 1 second.

### ■ Press Ctrl+Shift+2 to stop.

---

## RIGHT AFTER THE TAKE

1. Click the PowerShell window. Type `/exit` → **Enter**.
2. Type this and press **Enter**:
   `New-Item -ItemType Directory -Force "d:\Adobe\round 4\evidence\final"; Copy-Item audit-report.json, audit-report.md "d:\Adobe\round 4\evidence\final\"`
3. **Win+E** → go to `d:\Adobe\round 4\evidence\`.
4. Right-click the newest `.mp4` → **Rename** → type `part2_raw_FINAL.mp4` → **Enter**.
   ⚠️ **Never edit this file.** Make a copy to edit.
5. Double-click it and watch it through. Check:
   - [ ] The hash is readable
   - [ ] The URL is readable before Enter
   - [ ] The Skill call is visible
   - [ ] The findings and view-source page are readable
   - [ ] The audio is clear
6. Tell Claude: **"done, final take"**.

---

## RETAKE (only if the run itself failed)

1. Wait **10 minutes**.
2. Close the demo window. In PowerShell:
   `cd "d:\Adobe\round 4"` → `.\open_demo.ps1`
3. Redo:
   - S1 steps 5–8
   - S2 (a fresh PowerShell window)
   - S3
   - S6
4. Redo the whole **RECORDING** section.
5. First rename the failed recording to `part2_NOT_USED_2.mp4`. Then save the new one as `part2_raw_FINAL.mp4`, and copy its `audit-report.*` into `evidence\final\`.

---

## IF SOMETHING GOES WRONG

**The agent asks a question**
Answer briefly ("yes, run it") and keep recording.

**The run fails or takes over 6 minutes**
Stop. Wait 10 minutes. Retake.

**The numbers aren't 0 and 163**
That's normal for a live site. Say what's on screen.

**ACC-018 or RND-001 is at the top**
Use Shot 5A and 5B as written. If something else is at the top, say its title in one line, then drill into RND-001.

**Paste does nothing**
Right-click in the PowerShell window → **Paste**.

**You stumble on a sentence**
Keep going and re-say it. The stumble can be trimmed later.

---

✅ Never stop OBS between Shot 1 and Shot 7.
✅ If something unexpected happens, narrate what's on screen and keep going.
