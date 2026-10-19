# Recording day runbook — Delulu Devs, Round 4

Open this on your phone and follow it top to bottom. Allow about 2–3 hours,
including retakes and editing.

---

## A. Preparation (20 min, nothing recorded yet)

### A1. Clean the machine
1. Plug the laptop in and connect to stable Wi-Fi.
2. Turn on Do Not Disturb: **Win + N → Do not disturb**.
3. Quit WhatsApp, Discord, Teams, mail, and anything that pops up notifications.
4. In the browser, close every personal tab. Open exactly two tabs:
   - Tab 1: `view-source:https://www.duolingo.com/`
   - Tab 2: `https://www.duolingo.com/`

### A2. Open the demo workspace
1. Open PowerShell and run:
   ```powershell
   cd "d:\Adobe\round 4"
   .\open_demo.ps1
   ```
   A VS Code window titled **"Delulu Devs - Round 4 demo"** opens with all the Part 1 files in tabs and REPLAY as the active tab.
2. Close the REHEARSAL window. **Minimise** the VS Code window where you chat with Claude (don't close it, or the chat ends). Only the demo window should be visible.
3. Press **Ctrl + B** to hide the sidebar, which gives more room for code.

### A3. Put the terminal in place
1. In the demo window, press **Ctrl + `** to open a terminal. It opens in `demo\brand-ai-readiness-audit`.
2. Right-click the terminal tab → **Move Terminal into Editor Area**.
3. Drag the terminal tab to the right half, so REPLAY is on the left and the terminal on the right.

### A4. Pre-accept the folder trust prompt (keeps it off camera)
In that terminal:
```powershell
claude
```
- When it asks "Do you trust the files in this folder?", choose **Yes**.
- Type `/exit` and press Enter.
- Run `cls` to clear the terminal.

### A5. Pre-flight check (in the same terminal)
```powershell
claude --version        # must print 2.1.281 (Claude Code)
python --version        # 3.9 or newer
Get-ChildItem audit-report.* -ErrorAction SilentlyContinue   # must print nothing
python "d:\Adobe\round 4\verify_engine.py" "d:\Adobe\round 4\demo"   # must print ENGINE OK
```
**Never edit files in the demo window.** The workspace makes them read-only. If
`verify_engine.py` ever prints CHANGED or EXTRA, close VS Code (choose **Don't
Save**) and re-run `.\open_demo.ps1`, which restores the engine from the zip.
Then run `cls` again.

### A6. Set up OBS (first time only)
1. Open **OBS Studio**. Under **Scenes**, click `+` and name the scene `Demo`.
2. Under **Sources**, click `+`:
   - **Display Capture**: pick your main monitor.
   - **Audio Input Capture**: pick your microphone (a headset mic is best).
   - Optional: **Video Capture Device** (your webcam). Drag it small into the **bottom-right corner** so it covers no terminal text.
3. **Settings → Output → Recording**:
   - Recording Path: `D:\Adobe\round 4\evidence`
   - Recording Format: **MP4** (or Hybrid MP4)
4. **Settings → Video**: Base and Output resolution **1920×1080**, FPS **30**.
5. **Settings → Hotkeys**: set **Start Recording** = `Ctrl+Shift+1` and **Stop Recording** = `Ctrl+Shift+2`, so you never need to show OBS on screen.
6. Speak normally and watch the mic meter in the **Audio Mixer**. Peaks should sit in the **yellow** zone, not the red.
7. Record 10 seconds as a test, play it back, and check the terminal text is sharp and your voice is clear. Delete the test file.
8. **Minimise OBS.** It must not appear in the recording.

---

## B. Record Part 1: methodology (target ≤ 2:50)

Follow **`PART1_SHOTLIST.md`**: every click and every line to say, shot by shot. Record Part 1 **before** setting up the terminal (A3–A5), because Part 1 uses the full-width editor.

---

## C. Record Part 2: live trial run (ONE continuous take)

Follow **`PART2_SHOTLIST.md`**: setup, every click, every line to say, and what to do right after the take.

---

## D. Editing in Clipchamp (30–45 min)

1. Open **Clipchamp** (built into Windows 11) → **Create a new video**.
2. Import `part1_*.mp4` and `part2_raw_takeN.mp4` (the take you're using). Drag them onto the timeline in order.
3. Part 1: cut stumbles and dead air freely.
4. Part 2: use the **split tool (S)** to cut **only waiting time**, such as spinners, long crawls and the agent thinking. Keep all of these visible:
   - the `claude --version` and hash commands
   - the paste and the Enter on the prompt
   - the `Skill(audit-orchestrator)` call and the `run_audit.py` command
   - the findings appearing
   - the whole drill-down and table
   **Never rearrange clips or insert footage from another take.**
5. Optional: a 2-second title card, "Delulu Devs — Round 4 Live Agent Demo". It counts towards the 5 minutes.
6. Check the timeline: **Part 1 ≤ 3:00, Part 2 ≤ 2:00, total ≤ 5:00.** Aim for about 4:45 to be safe.
7. **Export → 1080p.** Save as `d:\Adobe\round 4\evidence\DeluluDevs_Round4_Demo.mp4`.
8. Watch the exported file once, start to finish, with sound.

---

## E. After recording

1. Tell Claude: "recording done, I used take N". Claude will then:
   - check `evidence\audit-report.json` against the REPLAY file
   - update REPLAY's "WHAT TO EXPECT" numbers to match your run
   - run the final integrity checklist
2. A teammate replays `REPLAY_DeluluDevs.txt` cold on their own machine.
3. Submit **`DeluluDevs_Round4_Demo.mp4`** and **`REPLAY_DeluluDevs.txt`** before the deadline on **27 September**.

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `claude` not recognised in the VS Code terminal | Close all VS Code windows and reopen with `.\open_demo.ps1` (the terminal needs the new PATH) |
| "running scripts is disabled" | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then reopen the terminal |
| Agent doesn't call the skill | The prompt wasn't pasted exactly. `/exit`, then retake with the exact REPLAY text |
| Audit takes over 5 minutes, or network errors | Check Wi-Fi, wait 10 minutes, retake |
| Findings differ from the rehearsal numbers | Normal for a live site. Narrate what's on screen; Claude updates REPLAY afterwards |
| OBS recording is black | Settings → Advanced → turn off hardware acceleration in the browser, or use **Window Capture** instead of Display Capture |
