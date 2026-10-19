# Severity, confidence and priority rubric

Every finding emitted by any skill in this marketplace is assigned severity by this
rubric and nothing else. The rubric exists so that two runs, two sites, and two
detectors all mean the same thing by "high" — and so a reader can audit the
judgement rather than trust it.

---

## 1. The gate model

Findings are classified by which gate of the pipeline they break. The gates are
**sequential**: failing an earlier gate makes later gates unreachable, which is why
an earlier-gate defect of the same shape outranks a later-gate one.

| Gate | Question | Failing it means |
| --- | --- | --- |
| `access` | Can a machine reach the page at all? | The page does not exist for that system |
| `render` | Can it read what a human sees? | The page is reachable but effectively blank |
| `extract` | Can it pick out the specific fact asked about? | The page is readable but unquotable |
| `trust` | Will the fact be believed and repeated? | The page is quotable but gets hedged, confused with another entity, or ignored in favour of a corroborated source |
| `engagement` | Does the arriving human orient, act and stay? | Discoverability succeeded and was wasted |

**Gate-precedence rule.** When an `access`-gate defect makes the whole site
unreachable, downstream detectors still run but their findings are demoted to at most
`medium` and the report says so — a missing `Product` schema is not the site's
problem if the crawler is being served a 403. The orchestrator applies this in
`compose_report.py::apply_gate_precedence`.

---

## 2. Severity scale

Severity answers one question: **how much of the site's ability to be found, cited,
or used does this defect remove?** It is a function of *blast radius* and *gate*, not
of how easy the fix is.

| Severity | Definition | Test to apply |
| --- | --- | --- |
| `critical` | Closes an entire gate for the entire site. The site is functionally absent from, or actively misrepresented by, AI answers. | "If nothing else changed, would this alone keep the brand out of AI answers site-wide?" |
| `high` | Closes a gate for an important page class, or removes the primary fact users ask about (price, location, what the company does, contact). | "Would this alone stop the brand being cited for a whole category of question?" |
| `medium` | Materially reduces the likelihood or quality of retrieval, citation, or conversion, but a determined system or visitor still gets through. | "Does this make success meaningfully less likely rather than impossible?" |
| `low` | Polish. Real, correct, worth doing, but marginal on its own. | "Is the cost of ignoring this small and diffuse?" |
| `info` | Not a defect. An observation the reader needs in order to interpret other findings (e.g. "site is a single-page brochure; page-class checks did not apply"). | Never counted as a problem. |

**Blast-radius modifiers.** A detector computes a base severity for the check, then
applies:

- Affects `>= 80%` of sampled pages of an applicable class → keep or raise one level (never above `critical`).
- Affects `< 20%` of sampled pages and the site's primary pages are clean → lower one level.
- Affects only pages excluded from indexing anyway (noindex, robots-disallowed) → lower to `low`, or drop entirely if the exclusion is clearly deliberate.

**Never inflate.** A detector may not emit `critical` unless the check's own
definition in its `references/` file lists `critical` as a possible outcome with the
site-wide condition that triggers it. This is the primary defence against the most
common failure mode in this problem space — a report where everything is urgent and
therefore nothing is.

---

## 3. Confidence and method

Severity says how bad it is. **Confidence says how sure we are we measured it**, and
the two must never be conflated: a `critical` finding at `low` confidence is reported
as `critical` with the uncertainty stated in the evidence sentence, not quietly
downgraded.

| `confidence` | Meaning |
| --- | --- |
| `high` | Directly measured from fetched bytes or a live probe. The evidence sentence contains the measurement. |
| `medium` | Measured by a proxy that is strongly but not perfectly correlated with the defect (e.g. render gap inferred from an empty-shell signature rather than an executed DOM). |
| `low` | Inferred heuristically, typically from language or layout patterns. Reported, but the reader is told it needs human confirmation. |

| `method` | Meaning |
| --- | --- |
| `static` | From the raw HTTP response body, headers or status |
| `rendered` | From a DOM produced by an actual JavaScript engine |
| `probe` | From a deliberate differential request (e.g. bot UA vs browser UA) |
| `heuristic` | From pattern matching over text or structure, no separate request |
| `external` | From a source other than the audited site |

**Honesty rule (hard requirement).** A finding may never claim a `method` that did not
run. If JavaScript rendering was unavailable, render-gap findings are emitted with
`method: heuristic`, `confidence: medium`, and a matching entry in
`audit.limitations`. Silently guessing and presenting it as measurement is the single
fastest way to produce a false positive, and is treated here as a correctness bug.

---

## 4. Priority of the suggested action

Severity describes the problem. **Priority describes the fix**, and they are
deliberately allowed to differ — a `medium` defect with a ten-minute fix should be
done before a `high` defect requiring a re-platform.

```
priority = rank( severity_weight x breadth ) adjusted by effort
```

| | effort `low` | effort `medium` | effort `high` |
| --- | --- | --- | --- |
| severity `critical` | critical | critical | high |
| severity `high` | high | high | medium |
| severity `medium` | high | medium | medium |
| severity `low` | medium | low | low |

Effort is estimated by the detector from the shape of the fix:

- `low` — a config value, a meta tag, a robots line, one block of JSON-LD, a copy edit.
- `medium` — a template change applied across a page class, a new page, a schema rollout.
- `high` — a rendering-architecture change, a re-platform, an ongoing content programme.

Every `suggested_action` also carries `owner` (`engineering` / `content` / `marketing`
/ `ops` / `design`) so the report can be split across teams without re-reading it, and
`verify` — how to confirm the fix landed, named against the check that found it.

---

## 5. Scoring

Scores exist for the non-expert reader and for tracking change over time. They are
derived, never authored.

Each gate starts at 100 and loses points per finding in that gate:

| Severity | Points deducted |
| --- | --- |
| `critical` | 40 |
| `high` | 20 |
| `medium` | 8 |
| `low` | 3 |
| `info` | 0 |

Gate scores floor at 0. The overall score is the weighted mean:

```
access 0.20, render 0.20, extract 0.25, trust 0.15, engagement 0.20
```

`extract` is weighted highest because it is the gate that most often separates a site
that is crawled from a site that is *cited*: reachable, readable content that still
contains no liftable answer is the most common shape of the problem this marketplace
exists to diagnose.

A gate with no applicable checks (for example `extract` page-class checks on a
one-page brochure site) is excluded from the mean rather than scored 100, and the
report records the exclusion in `audit.checks_skipped`.

---

## 6. False-positive discipline

The rubric that grades this marketplace penalises false positives as much as misses.
Three rules are binding on every detector:

1. **Applicability gate first.** Every check declares which site types and page types
   it applies to. `structured-data-audit` does not ask a personal blog for
   `Product`/`Offer` markup; `engagement-audit` does not demand a pricing CTA from a
   documentation site. If applicability cannot be established, the check is skipped
   and recorded in `checks_skipped` — not fired at a guess.
2. **Every check carries an explicit `do not flag when` clause**, written in its
   skill's `references/` file at authoring time. A check without one is not finished.
3. **Absence of evidence is not evidence.** If a page could not be fetched, rendered,
   or parsed, that is a `limitations` entry, never a finding against the site.

A well-built site must produce a short report. A detector that cannot stay silent on a
clean site is broken, and `tests/` contains clean-site fixtures asserting exactly that.
