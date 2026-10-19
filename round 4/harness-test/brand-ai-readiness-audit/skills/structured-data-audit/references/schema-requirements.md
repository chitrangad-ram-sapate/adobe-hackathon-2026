# Gate 3a check catalogue: structured data

## The principle: fields, not presence

"Has schema markup" is close to a useless signal. A `Product` node with no
`offers`, or an `Organization` with nothing but a name, validates cleanly and
answers no question. So every type is modelled by **the fields that make it
answer something**, and the finding names the question the type exists to
answer.

| Type | Required (node is unusable without) | Recommended | Answers |
| --- | --- | --- | --- |
| `Organization` | name, url | logo, description, sameAs, address, contactPoint, foundingDate | Who is this company, and is it the same entity as the one on Wikipedia/LinkedIn |
| `LocalBusiness` | name, address | telephone, openingHours(Specification), geo, priceRange, url, sameAs | Where is it, when is it open, how do I contact it |
| `Product` | name, offers | image, description, brand, sku, aggregateRating, gtin | What is this and what does it cost |
| `Offer` | price, priceCurrency | availability, url, priceValidUntil, shippingDetails | What does it cost and can I buy it now |
| `Article` / `BlogPosting` / `NewsArticle` | headline, datePublished | author, dateModified, image, publisher | What does this say, when, and who said it |
| `FAQPage` | mainEntity | - | Question-and-answer pairs quotable verbatim |
| `BreadcrumbList` | itemListElement | - | Where this page sits, which gives an isolated page context |
| `WebSite` | name, url | publisher, potentialAction, inLanguage | What this site is called as a whole |
| `Person` | name | jobTitle, sameAs, worksFor | Who this is, and whether they are the same person as elsewhere |
| `Event` | name, startDate, location | endDate, offers, eventStatus | What, when, where |
| `JobPosting` | title, datePosted, hiringOrganization | jobLocation, baseSalary, employmentType | The role, where, for how much |
| `SoftwareApplication` | name | applicationCategory, operatingSystem, offers | What it does and what it costs |
| `Service` | name | provider, areaServed, description, offers | What is offered and to whom |
| `Recipe` | name, recipeIngredient, recipeInstructions | cookTime, prepTime, nutrition | How do I make this |

A field is "populated" only if it holds something usable. Empty strings, empty
arrays, and template placeholders (`N/A`, `TBD`, `Your Company Name`,
`lorem ipsum`) all count as absent - they validate and answer nothing.

## Expected types by page class

This mapping is the applicability gate. A type is only ever demanded of a page
class it belongs to.

| Page class | Expected | Extra gate |
| --- | --- | --- |
| home | Organization, WebSite | any Organization subtype is credited |
| product | Product | - |
| article | Article / BlogPosting / NewsArticle | any article subtype is credited |
| faq | FAQPage | - |
| contact | Organization, or LocalBusiness | LocalBusiness only demanded when site type is local_business |
| about | Organization | - |
| pricing | Product, Offer, Service, SoftwareApplication | only when site type is saas, ecommerce, marketplace or unknown |
| careers | JobPosting | - |

Any other page class expects nothing. Unknown schema.org types are never
reported as defects - the vocabulary is large and sites legitimately use types
this module does not model.

---

## Checks

| ID | Fires when | Severity | Do NOT flag when |
| --- | --- | --- | --- |
| `SDA-001` | A JSON-LD block fails to parse | high | It parses. Note a block that parses only after HTML-unescaping is `SDA-002`, not this. |
| `SDA-002` | A block parses only after HTML entity unescaping | medium | It parses as served. |
| `SDA-003` | No JSON-LD, microdata or RDFa anywhere on the sampled pages | high | Any of the three is present anywhere. |
| `SDA-004` | Microdata or RDFa present but no JSON-LD | low | JSON-LD is present. Microdata is still consumed; this is a preference, not a failure, and is scored accordingly. |
| `SDA-005` | 2+ pages of a class lack that class's expected type | varies by class, blast-radius scaled | Only 1 page of the class lacks it - one page is not a pattern, and the skip is recorded with that reason. |
| `SDA-006` | The homepage has no Organization-family or WebSite markup | high | Any organisation subtype is present. |
| `SDA-007` | A known type is missing required fields | high for Product/Offer/LocalBusiness, else medium | The type is not in the table above. Also: the `offers` field is yielded to `SDA-008` when that fired, so a missing price is reported once, not twice. |
| `SDA-008` | Product-family markup exists with no populated Offer price | high (blast-radius scaled) | Site type is not commercial, or no product/pricing pages were sampled. |
| `SDA-009` | 3+ question-shaped headings on a page with no FAQPage markup | medium | FAQPage or QAPage markup already exists on that page. |
| `SDA-010` | 80%+ of nested pages have no BreadcrumbList | low | Fewer than 3 nested pages sampled. |
