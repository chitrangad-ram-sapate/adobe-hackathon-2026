# Opens the Round 4 demo window with every file Part 1 needs, in narration order,
# plus REPLAY for Part 2. Usage:  .\open_demo.ps1        (or  .\open_demo.ps1 -Rehearsal)
param([switch]$Rehearsal)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($Rehearsal) {
    $ws  = Join-Path $root "REHEARSAL.code-workspace"
    $pkg = Join-Path $root "harness-test\brand-ai-readiness-audit"
} else {
    $ws  = Join-Path $root "DEMO.code-workspace"
    $pkg = Join-Path $root "demo\brand-ai-readiness-audit"
}

# Clear output from any previous take so the run starts clean.
Get-ChildItem $pkg -Filter "audit-report.*" -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem $pkg -Filter "run.*" -ErrorAction SilentlyContinue | Remove-Item -Force

if (-not $Rehearsal) {
    # The demo engine must be byte-identical to the submitted zip; put back anything that was edited.
    python (Join-Path $root "verify_engine.py") (Split-Path -Parent $pkg) --restore
}

code -n $ws
Start-Sleep -Seconds 3

# Part 1 files, in the order DEMO_SCRIPT.md narrates them.
$files = @(
    "marketplace.json:1",
    "skills\render-extractability-audit\references\render-gap-playbook.md:67",
    "skills\render-extractability-audit\scripts\check_render.py:105",
    "skills\entity-corroboration-audit\scripts\check_identity.py:454",
    "skills\audit-orchestrator\references\severity-rubric.md:32",
    "lib\auditlib\findings.py:17",
    "skills\audit-orchestrator\scripts\compose_report.py:70",
    "examples\example-real-site.json:1",
    "skills\remediation-planner\scripts\plan_remediation.py:236",
    "tests\sites.txt:1"
)
foreach ($f in $files) { code -r -g (Join-Path $pkg $f) }

# Part 2: REPLAY opened last, so it is the active tab.
code -r (Join-Path $root "REPLAY_DeluluDevs.txt")
