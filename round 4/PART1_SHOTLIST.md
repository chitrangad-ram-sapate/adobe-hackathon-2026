# Part 1: click-by-click shot list (target ≤ 2:50)

**The one navigation trick used throughout:** press **Ctrl+P**, type
`filename:line` (for example `check_render.py:105`), and press **Enter**. VS Code
opens that file with the cursor on that line. Then hold **Shift** and press
**↓** the stated number of times to highlight the lines you're talking about.
Press **Esc** to clear a highlight.

Keep this list and the narration on your **phone**, never on the recorded screen.

---

## Setup (before recording; about 10 min)

1. Press **Win**, type `PowerShell`, press **Enter**.
2. Type these two lines, pressing Enter after each:
   ```powershell
   cd "d:\Adobe\round 4"
   .\open_demo.ps1
   ```
3. A VS Code window titled **"Delulu Devs - Round 4 demo"** opens with many tabs. Click into it.
4. Press **Win+↑** to maximise it.
5. Press **Ctrl+B** to hide the file sidebar. The code gets the full width.
6. **Don't open a terminal.** Part 1 is code only; the terminal is set up afterwards for Part 2.
7. Close the other windows:
   - Close the REHEARSAL VS Code window if it's open (click its X).
   - **Minimise** the VS Code window with the Claude chat (don't close it).
   - Close or minimise the browser, PowerShell, and everything else.
8. Test the trick once: **Ctrl+P**, type `check_render.py:105`, **Enter**. It should jump to line 105. Then press **Ctrl+P**, type `marketplace.json:1`, and press **Enter** to come back.
9. Text size: if code looks small from a metre away, press **Ctrl+=** once. Press **Ctrl+-** to undo.
10. Open **OBS** → check the mic meter moves when you talk → **minimise OBS**.
11. Put this shot list on your phone. Take a breath.

---

## Recording

Press **Ctrl+Shift+1** to start OBS. Wait 1 second in silence.

### Shot 1 · `marketplace.json` (~20 s)
- **Click:** you're already on `marketplace.json` at line 1. Click on line **6** (`"entrypoint": "audit-orchestrator"`) and press **Shift+↓ ×3** to highlight lines 6–9.
- **Say:**
  > "We're Delulu Devs. Our marketplace is eight skills behind one entrypoint, `audit-orchestrator`. Our research showed an AI assistant reaches a brand's facts through a fixed pipeline: it must *access* the page, *render* it, *extract* a quotable fact, and *trust* it. Then the visitor it sends must *engage*. Every check belongs to exactly one of those gates."
- While saying "eight skills", scroll down slowly with the mouse wheel through the `skills` list, which shows the six detectors.

### Shot 2 · render catalogue (~10 s)
- **Click:** **Ctrl+P** → `render-gap-playbook.md:67` → **Enter**. Then **Shift+↓ ×2** (highlights the `RND-001` and `RND-002` rows).
- Move the mouse pointer over the **"Do NOT flag when"** text at the end of the `RND-001` row.
- **Say:**
  > "Each signal lives in a reference catalogue with its threshold and a 'do not flag when' clause. `check_consistency.py` fails the build if code and catalogue drift apart."

### Shot 3 · `check_render.py` (~30 s)
- **Click:** **Ctrl+P** → `check_render.py:99` → **Enter**. Then **Shift+↓ ×14** (highlights lines 99–113: the comment, `main_word_count` and `coverage < 0.75`).
- **Say:**
  > "Our key lesson came from live sites. Our first render check compared whole-page text, and JavaScript menus made server-rendered python.org look 73% broken. Now we compare *main content only*, with the same extractor on both sides: line 105. Server-rendered sites score 99 to 100%, client-rendered ones 3% or less, so the 0.75 threshold sits in empty space. False positives went from 8 to 0 across 71 sites, and it started catching Notion."
- On "line 105", point the mouse at `main_word_count`. On "0.75", point at `coverage < 0.75`.

### Shot 4 · `check_identity.py` (~10 s)
- **Click:** **Ctrl+P** → `check_identity.py:454` → **Enter**. Then **Shift+↓ ×3** (lines 454–457).
- **Say:**
  > "Off-site, we verify the profiles a site claims in `sameAs`. A 404 is a dead claim. A 403 is only unverified: blocked is not dead."

### Shot 5 · severity rubric (~10 s)
- **Click:** **Ctrl+P** → `severity-rubric.md:32` → **Enter**. Then **Shift+↓ ×12** (the section heading and the severity table, lines 32–44).
- **Say:**
  > "Severity measures how much of the site's ability to be found or cited a defect removes. Critical means a whole gate closed, site-wide."

### Shot 6 · blast radius in `findings.py` (~15 s)
- **Click:** **Ctrl+P** → `findings.py:46` → **Enter**. Then **Shift+↓ ×13** (the `apply_blast_radius` function, lines 46–59).
- **Say:**
  > "It's enforced in code: every detector emits through `findings.py`. Blast radius adjusts it: a defect on 80% of pages goes up a level, and one under 20% goes down, so one broken page is never reported as site-wide."
- On "80%", point at `share >= 0.8`. On "20%", point at `share < 0.2`.

### Shot 7 · precedence in `compose_report.py` (~15 s)
- **Click:** **Ctrl+P** → `compose_report.py:126` → **Enter** (`def apply_gate_precedence`). **Shift+↓ ×1.**
- **Say (first half):**
  > "Gates are sequential, so if the crawler is blocked, `apply_gate_precedence` demotes downstream findings."
- **Click:** **Ctrl+G** → type `70` → **Enter**. Then **Shift+↓ ×1** (highlights `("RND-001", "RND-002")`).
- **Say (second half):**
  > "And a measured check always outranks an estimate: RND-001 supersedes RND-002."

### Shot 8 · a real finding (~15 s)
- **Click:** **Ctrl+P** → `example-real-site.json:128` → **Enter**. Then **Shift+↓ ×26** (from `evidence` down to `verify`, lines 128–154).
- **Say**, pointing with the mouse at each field as you name it:
  > "Every finding carries its evidence (point at `evidence`, line 128), the *mechanism*, meaning why it stops an AI citing you (point at `mechanism`, line 139), concrete steps (point at `how`, line 145), and a `verify` line naming the check to re-run (point at `verify`, line 154). A fix with a mechanism can be checked."

### Shot 9 · priority matrix (~8 s)
- **Click:** **Ctrl+P** → `findings.py:23` → **Enter**. Then **Shift+↓ ×9** (the comment plus `PRIORITY_MATRIX`, lines 23–32).
- **Say:**
  > "Priority is severity crossed with effort, so a cheap fix for a medium problem comes before an expensive fix for a high one."
- On "cheap fix for a medium problem", point at `("medium", "low"): "high"`.

### Shot 10 · remediation planner (~5 s)
- **Click:** **Ctrl+P** → `plan_remediation.py:233` → **Enter**. Then **Shift+↓ ×6** (the per-topic fix playbooks: `jsonld`, `ssr`, `meta`, `edge`).
- **Say:**
  > "The remediation planner rewrites each fix for the site's own CMS or framework."

### Shot 11 · the corpus (~8 s)
- **Click:** **Ctrl+P** → `sites.txt:1` → **Enter**. Scroll down slowly with the mouse wheel through the list of sites.
- **Say:**
  > "We validated on 71 live sites: all completed, all schema-valid, none over five minutes. Today's site isn't on this list."

Pause 1 second. Press **Ctrl+Shift+2** to stop OBS.

---

## After recording

1. Open File Explorer → `d:\Adobe\round 4\evidence\`. Rename the newest `.mp4` to `part1_take1.mp4`.
2. Double-click it and watch it through. Check:
   - Every highlighted file was readable when you talked about it.
   - Your voice is clear, with no clipping.
   - The length is about 2:30–2:50.
3. **Stumbled on one shot?** You don't need to redo everything. Navigate to that shot's file, press **Ctrl+Shift+1**, redo just that shot and press **Ctrl+Shift+2**. Name it `part1_shot3_retake.mp4` and swap it in when editing.
4. **Over 3:00?** Drop Shot 10 (saves about 5 s) and speak slightly faster in Shot 3.

Then continue with **Part 2** in `RECORDING_DAY.md`, section C. The terminal setup for Part 2 is in section A3 of that file.
