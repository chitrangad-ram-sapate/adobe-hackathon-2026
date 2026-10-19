# Gate 2 check catalogue: render and extractability

## The render gap, and how it is measured honestly

Most AI retrieval fetchers take the HTTP response and do not execute
JavaScript. Anything the client assembles afterwards does not exist for them.
The gap between the two is the single most consequential measurement in this
audit, and also the easiest to fake, so it is measured in two clearly separated
modes:

| Mode | Available when | check | `method` | `confidence` |
| --- | --- | --- | --- | --- |
| Measured | A browser engine (Playwright) is installed | `RND-001` | `rendered` | high |
| Estimated | No engine available | `RND-002` | `heuristic` | medium |

In estimated mode the finding says, in its own `evidence_detail`, that no DOM
was executed, and `audit.limitations` carries the same statement. **A finding
must never claim a `method` that did not run.** Presenting an estimate as a
measurement is treated here as a correctness bug, not a presentational one.

The estimate fires only on the conjunction of three signals - almost no text,
a response large enough to be carrying content, and client-framework markers -
because any one of them alone produces false positives on legitimately short
pages.

### The three shapes of the same problem, and why they get different fixes

### Why the comparison uses main content only

Both sides of the ratio are measured with the **same extractor**, over
`main_text` (the `<main>`/`<article>` landmark, or `<body>` minus nav, header,
footer and aside) rather than whole-page text.

Whole-page text measures furniture. JavaScript routinely expands mega-menus,
injects cookie banners and builds footers without adding a single quotable
word, so a fully server-rendered page can show a large raw-to-rendered
difference while its actual content is byte-identical. Measured that way,
python.org read as 73% coverage - "content assembled by JavaScript" - when its
main content did not change at all between the raw response and the browser
DOM.

`main_text` is also what an extractive system would quote, which is what this
check claims to be about. On a corpus of server-rendered and static sites the
main-content ratio sits at 0.99-1.00, while genuinely client-rendered pages
fall to 0.00-0.06, so the 0.75 threshold sits in open space rather than
between overlapping classes.

1. **Empty application shell** (`RND-002`). The response is a container and a
   script bundle. Nothing is in the bytes. Fix: server-side rendering or
   pre-rendering. Expensive.
2. **Hydration-only content** (`RND-003`). The content *is* in the bytes, as
   serialised JSON, but not as prose. Fix: render the fields the payload
   already carries into HTML. Much cheaper, and a materially different
   conversation with the engineering team - which is why it is a separate
   check rather than a variant of the first.
3. **Interaction-gated content** (`RND-011`). The content is in the HTML as
   prose but hidden until a click. Weakest of the three: some extractors
   discount it, and a visitor who does not click never reads it. Fix: expand
   by default and mark FAQs up.

---

## Checks

| ID | Fires when | Severity | Do NOT flag when |
| --- | --- | --- | --- |
| `RND-001` | Raw-to-rendered **main-content** word coverage below 0.75 on a rendered page | critical <0.30, high <0.60, else medium | The rendered page has under 80 words of main content - there is nothing on it either way, so a ratio is meaningless. Application shells that thin are left to `RND-003`. |
| `RND-002` | Content page with under 60 raw words, over 15 KB response, and framework/shell markers | critical (blast-radius scaled) | A browser engine was available - `RND-001` supersedes it and the composer drops this one. Also never on pages under 15 KB: a genuinely short page is not a shell. |
| `RND-003` | Over 20 KB of inline hydration JSON, under 250 words of prose, payload over 25% of the response | high | Prose is present in normal volume. The data being in the response is a mitigating factor, not an aggravating one. |
| `RND-004` | A `<noscript>` block states that JavaScript is required | medium | `<noscript>` contains real fallback content instead of a warning. |
| `RND-005` | 30%+ of content pages fall below the word floor for their page type | medium | A render-gap finding already fired - it explains the emptiness, and reporting both double-counts one root cause. Floors are deliberately low (home 90, article 200) to mark pages with nothing to quote, not pages that could be longer. |
| `RND-006` | Images whose filename or position indicates they carry words (chart, price, menu, banner, heading graphics) have no alt text | high | The image has alt text, or its filename gives no indication it carries data. Decorative imagery is out of scope here. |
| `RND-007` | Over 30% of images, and at least 5, have no alt attribute | medium, or high above 70% | Fewer than 5 images total - too small a sample. |
| `RND-008` | A linked PDF contains image data but no `/Font` plus text-drawing operators | high | The PDF has a text layer. Detected from PDF object structure, not by running OCR, so it is emitted at medium confidence. |
| `RND-009` | Half or more of linked PDFs carry no `/Title` metadata | low | Fewer than 2 PDFs. |
| `RND-010` | A page has under 200 words of its own body text while embedding a substantive iframe | high | The iframe is a known media or utility embed (YouTube, Vimeo, Maps, consent, captcha, analytics) - those are never a page's primary content. |
| `RND-011` | Over 40% of body text, and over 150 words, sit in collapsed regions at load | medium | The page has under 100 words total, or the hidden text is a small fraction. Note: only inline hiding is detected (`hidden`, `aria-hidden`, inline `display:none`); class-based hiding needs a style engine and is deliberately out of scope rather than guessed at. |
| `RND-012` | 40%+ of pages, and at least 2, have no `<h1>` | medium | The site has fewer than 2 affected pages. |
| `RND-013` | 60%+ of pages have no `<main>` or `<article>` | low | Landmarks are present. |
| `RND-014` | 50%+ of pages have no `lang` attribute | low | The attribute is present, even if the value is unusual. |
| `RND-015` | 40%+ of pages have 3 or more `<h1>` elements | low | Two H1s - common and harmless in practice, so the threshold is 3. |
