# Phase 56 — a refusal that reads two words: the compound head is the head, not the neighbour (#105 closes)

## 1. Completed

The modifier slot's refusal changed shape. `_COLLISION_BLOCK` refused any word that is itself on the noun
list, which is what kept `meets it at 60 markets spread over the plane` reading as sixty *markets* -- and
also what kept `two radius definitions` and `3 path budgets` reading as `two radius` and `3 path`. #105
recorded that the two cannot be told apart by anything in the slot, because both are `<noun> <noun-shaped
word>`. This phase moves the test to the only place the evidence actually is: `_PARTICIPLE_HEAD_BLOCK`
reads two words and refuses a counted noun in the modifier position only when the word **after** it is in
`_PARTICIPLE_HEADS` (`spread`, `spanning`), and `definitions` and `budgets` joined `_REPORT_NOUN_BODY`.

Measured over the five inventoried texts, and each variant enumerated rather than argued:

| Rule | phrases | quantities | phantoms | misattributions |
|---|---|---|---|---|
| blanket refusal (as #104 shipped it) | 198 | 196 | 2 | 0 |
| no refusal at all (Phase 53's greedy) | 200 | 198 | 0 | 1 (`60 markets spread`) |
| head-keyed refusal outside the optional group | 197 | 197 | 0 | 0, but `one spread` and `zero spread` deleted |
| head-keyed lookahead in front of the group | 197 | 197 | 0 | 0, but `60 markets` deleted too |
| **shipped: head-keyed, inside the group** | **199** | **199** | **0** | **0** |

The census reads 199 of 199 with both phantom lists empty, and the repair is not a rename: `two radius
definitions` and `3 path budgets` are now counted for what their sentences count. Widening the noun list
also surfaced a claim that had never been visible -- the report's `the two definitions disagree whenever
the mean is material`, about the EWMA recursion's two written conventions -- which is now declared with its
own anchor and its own ledger row, so the pair count moved 46 → 47 and `none:` 27 → 28 with a new category,
`convention-set`.

`phantom:` left the ledger's vocabulary. It existed for one row, the rule's own truncation, and the
mechanism that produced it is gone, so the kind, its guard branch, its reading entry and its plant were
deleted rather than kept as a branch that can never be reached.

Register: #105 amended closed, its reversal condition met by measurement. 4 plants added, 1 retired
(150 → 153).

## 2. Assumptions this rests on

- `_PARTICIPLE_HEADS` is vocabulary, not grammar. A participle absent from the list produces a truncation
  silently; the per-document census is what notices, which is why the census gold is the gate on this rule
  and not these two sentences.
- `definitions` and `budgets` are on the noun list because this corpus counts them. A noun that appears
  nowhere in the five texts is not added, since the list's only evidence is the enumeration.
- The two-word lookahead is evaluated at the modifier slot only. That placement is load-bearing in both
  directions, and both wrong placements were measured (see the table) rather than predicted.
- The rule still cannot know what a sentence counts; it can now see the head. A phrase like `four stress
  artifacts` remains a modifier reading because `artifacts` is not on the participle list -- correct here,
  and correct only because the corpus says so.

## 3. Files changed

- `tests/python/test_artifact_metadata.py` -- `_PARTICIPLE_HEADS`, `_PARTICIPLE_HEAD_BLOCK`, the tail
  assembly, `_REPORT_NOUN_BODY`, property 9's four-shape controls, the census gold and both phantom lists,
  `_DECLARATION_KINDS` (no `phantom`), `_DECLARATION_CATEGORIES` (+`convention-set`), `_DECLARATION_READING`,
  the ledger's refiled row and its new one, `_REPORT_DECLARED`'s new anchor, and the ledger's own comment.
- `scripts/mutation_plants.py` -- four plants added, one retired, six anchors re-pointed for the new kind
  spellings, the emptied phantom lists and the new plant count.
- `docs/limitations.md` -- #105 amended closed.
- `docs/project_scope.md` -- §9 row.
- Count cascade: `docs/interview_defense.md`, `paper/technical_report.tex` and the rebuilt
  `paper/technical_report.pdf` with its `technical_report.build.json` pair.

## 4. What the phase learned, including about its own first design

**A failing lookahead in front of an optional group is not a refusal of the group.** The first candidate
for the head test read `(?! nouns \s+ verbs \s )` placed before `(?:[A-Za-z]+\s+)?` and the noun. It should
have let `60 markets` through while blocking the three-word parse; it blocked the whole tail at that
position, so the phrase vanished from the census. 197 phrases, and the missing one was the markets. The
distinction -- refuse the *slot*, not the *match* -- is invisible in a table of counts and visible only
when you ask which phrase left.

**Two wrong placements were measured because both looked plausible, and one of them was a reconstruction
this project had already made.** Phase 51 hoisted the collision lookahead and lost 92 phrases; #105's own
entry recorded the greedy alternative as trading 2 phantoms for 1 misattribution. Neither earlier
measurement pinned the *placement* of a head-keyed test, so this phase ran all four shapes and kept the
numbers, which is why property 9 now separates them rather than asserting that one construction is right.

**Deleting a kind is a real change, and the guard that polices dead taxonomy is the thing that said so.**
`_DECLARATION_READING` pins the kind counts, and a kind with no row cannot survive it -- the alternative is
a branch that can never be reached, which is finding 89's shape wearing a different hat. The lesson general
than this ledger: a taxonomy pinned to instances must shrink when the instances go, or the pin stops
measuring anything.

**A repair that reveals a claim is a cost, not a bonus.** `two definitions` had never been visible to the
inventory, so it arrived unowned and the report guard refused the change until it was classified. Every
widening of a detector owes an answer for each thing it newly sees; the census and the owned-or-declared
guard together are what make that debt visible at commit time rather than later.

**A plant reddens a set, not a name.** #103 asks whether the guard a plant names is the guard that
actually fails, and the answer was only obtainable by running the module with the mutation in place and
reading the whole failing set -- `build/phase56-branch-audit.py`, 4 of 4 plants, tree restored
byte-for-byte after each. Membership held for all four: each named guard failed, and each failure carried
the message its claim predicted (`the participle-head rule reads ['60 markets spread']`, `no longer prints
these real counts: ['two radius definitions']`, `no longer prints these real counts: ['two radius']`, `the
declared anchor '... because the other' is not in the report: it is stale`). The set was *wider* than the
name in 3 of 4: dropping `spread` from the participle list reddens
the census too, un-widening the noun list reddens four guards, and a stale declaration anchor reddens the
ledger and the ownership check together. The union of extra guards over this sample is four distinct tests.
So the pairing audit #103 prescribes has to assert membership of the failing set, not equality with a
singleton -- a plant that trips two guards is not mis-paired, and an assert that demanded one name would
refuse the honest ones.

_Dated correction, 2026-10-18._ The first version of this paragraph quoted the fourth plant's message as
`the ledger and the declarations disagree`. That failure is real, but it belongs to the **neighbour**
guard, not to the plant's named one: the probe sliced the transcript at a fixed-width separator, and pytest
pads a section header to the terminal width, so a 71-character test name is wrapped in two underscores and
the slice ran straight through the boundary into the next section. Re-measured with the boundary matched by
pattern rather than by width -- `build/phase56-capture-check.py` proves the cutter on both the padded and
the two-underscore header before the suite was spent on it -- the named guard's own message is the
stale-anchor refusal quoted above. None of the counts moved: 4 of 4 named guards reddened, 3 of 4 sets
wider, every target restored. What moved is whose evidence was being cited, which is the one thing a branch
audit exists to establish.

## 5. Exact test results

| Gate | Command | Measured result |
|---|---|---|
| Lint | `.venv/bin/ruff check .` | All checks passed! |
| Format | `.venv/bin/ruff format --check .` | 200 files already formatted, measured on the `git archive` export of `d4b37e5` (finding 81's rule), and the runner reports the same 200 |
| Types | `.venv/bin/mypy python/quantrisk` | Success: no issues found in 23 source files |
| C++ | `ctest --test-dir build/dev` | 100% tests passed out of 204 |
| Validate | `.venv/bin/quantrisk validate` | 7/7 checks passed |
| Evidence | `.venv/bin/python scripts/verify_evidence_manifest.py` | `Evidence is intact.` -- 95 OK, 0 CHANGED, 0 MISSING. The report bundle moved to `d6e66063a16c` (PDF `35ff1590e862`) when this phase's cascade landed; no experiment artifact was re-frozen |
| Offline collection | `.venv/bin/python scripts/measure_offline_collection.py` | 458 tests collected |
| Python | `.venv/bin/python -m pytest -q` | 527 passed in 88.96s, re-measured on this record tree; the same 527 passed in 98.36s on `d4b37e5` |
| Falsification, full sweep | `.venv/bin/python scripts/run_mutation_suite.py --all` on `d4b37e5` | 153/153 planted defects were rejected by their guard, tree clean afterwards, exit 0 |
| Branch audit of this phase's plants | `.venv/bin/python build/phase56-branch-audit.py` on `d4b37e5` | 4 of 4 named guards in the failing set with the predicted message, 3 of 4 sets wider than the name, every target restored byte-for-byte |
| CI on the pushed head | run `39110753030` on `d4b37e5`, read from each job's own log | lint `All checks passed!`, `200 files already formatted`, mypy `Success: no issues found in 23 source files`; C++ and Python `100% tests passed out of 204` and `457 passed, 5 skipped in 157.51s (0:02:37)`, which is #91's reconciliation against the 458 the probe collects (`457 + 5 = 458 + 4 = 462`); benchmark `suite: 19/19 executed and passed, 0 aggregated from disk, 0 failed, 0 skipped, 427.0s total` |

## 6. Numerical validation

| Figure | Value | Producer |
|---|---|---|
| Census totals before / after | 198 phrases, 196 quantities, 2 phantoms → 199, 199, 0 | `_census_hits` |
| Sheet / report gold | 40 of 40 / 85 of 85 | the census lists |
| Rule variants measured | 5 | `build/phase56-probe.py` |
| Declared pairs | 46 → 47 | `_declared_pairs()` |
| Ledger kinds | 2 artifact, 6 card, 10 record, 1 granularity, 28 none | `_DECLARATION_READING` |
| `none:` categories | 15, all used | the vocabulary assert |
| Plants | 150 → 153 (4 added, 1 retired) | `scripts/mutation_plants.py` |
| Branch audit | 4 of 4 named guards reddened, 3 of 4 sets wider, 4 extra guards in the union | `build/phase56-branch-audit.py` |

## 7. Remaining limitations

- The participle list is vocabulary. A new `<noun> <participle>` pair in an inventoried document produces
  a truncation and is caught only by the next census pass.
- The rule still cannot tell which of two adjacent nouns a sentence counts when *neither* is a known
  participle; it prefers the longer parse. `four stress artifacts`-shaped phrases are correct here because
  the corpus is small enough to read.
- The census is scoped to the five inventoried texts. A truncation in a document outside that set is
  invisible to it, as it has always been.

## 8. Technical debt registered here

Nothing opened. #105 is amended closed on the condition its own entry set. The residual risk -- an
unregistered participle -- is stated inside #105's closing clause rather than opened as a new entry,
because the only instrument for it is the census that already exists and no further mechanism is nameable.

Still open from earlier phases: **#103**, whose static half was measured and rejected and whose dynamic
form costs a suite run per plant. Related: #104, #102, #101, #106.

## 9. The gate

The gate this phase moves is the one #105 said could not be closed without a part-of-speech decision. The
decision was made, but not by the rule: it was made by reading which word of the two a given sentence
counts, writing that down as a two-word test, and letting the census -- the instrument built three phases
earlier for exactly this kind of disagreement -- check the answer over 199 phrases instead of over the two
sentences that motivated the change. The rule is still vocabulary, and the entry says so; what changed is
that the vocabulary is now read off the head, which is the only place the corpus states its own intent.
