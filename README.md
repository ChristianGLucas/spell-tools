# spell-tools

Composable [Axiom](https://axiom.dev) nodes for **dictionary-based spell
correction and word segmentation**, wrapping the MIT-licensed
[symspellpy](https://github.com/mammothb/symspellpy) — the Python port of
Wolf Garbe's SymSpell algorithm — with its bundled English frequency and
bigram dictionaries (82,765 words / 243,342 word pairs) copied into this
repo's `data/` directory (byte-identical to the copies symspellpy itself
ships on PyPI). No runtime download; the dictionaries ship in the image.
Offline, deterministic, and bounded.

**Dictionary attribution:** the dictionary files are redistributed under
symspellpy's MIT license. The underlying word-frequency data is in turn
derived from the [Google Books Ngram
dataset](https://storage.googleapis.com/books/ngrams/books/datasetsv3.html)
(CC BY 3.0 Unported) and [SCOWL](http://wordlist.aspell.net/), per
[SymSpell's own documented sources](https://github.com/wolfgarbe/SymSpell) —
attribution: *"Ngram data from the Google Books Ngram Viewer, used under CC
BY 3.0."*

Built for the Axiom marketplace under the handle `christiangeorgelucas`.

Distinct from `fuzzy-match-tools` (pairwise string similarity between two
*given* strings — no dictionary involved) and `phonetic-tools` (sound-alike
encoding — no correction). This package corrects against a real
word-frequency dictionary.

## Nodes

| Node | Input → Output | What it does |
|------|----------------|--------------|
| **CorrectWord** | `SpellQuery → WordCorrection` | Correct a single misspelled word (e.g. `"hte"` → `"the"`) to its top-N most likely intended words, ranked by edit distance then frequency. |
| **CorrectPhrase** | `SpellQuery → PhraseCorrection` | Correct an entire phrase, including multiple typos and a single missing/extra space that merges or splits two adjacent words, using bigram context. |
| **SegmentText** | `SpellQuery → SegmentationResult` | Segment a run-together string into words (e.g. `"thequickbrownfox"` → `"the quick brown fox"`), correcting spelling along the way. |
| **CheckWord** | `SpellQuery → WordCheck` | Fast, exact, case-insensitive dictionary membership check for a single word, with its corpus frequency. |
| **FindMisspellings** | `SpellQuery → MisspellingReport` | Tokenize a phrase and flag every word not in the dictionary, each with ranked suggestions — "spellcheck as you type," as opposed to CorrectPhrase's single committed rewrite. |

## Shared request envelope

Every node takes a `SpellQuery { text, max_edit_distance?, top_n?, max_segment_length? }`.
Which optional field matters depends on the node (see each node's description
in `axiom.yaml`); unused fields are ignored. `max_edit_distance` is 0-2
(default 2) — the package's compiled SymSpell maximum.

## Known boundary: CorrectPhrase vs. SegmentText

`CorrectPhrase`'s missing-space recovery is bounded to a single two-word
merge/split within `max_edit_distance` (verified: `"whereis the exit"` →
`"where is the exit"`). It does **not** reliably reconstruct a multi-word
run-together blob (three or more merged words, e.g. `"thequickbrown"`) — use
`SegmentText` for that; it is purpose-built for arbitrary-length run-together
input.

## Determinism & correctness

Every node is a pure function of its input against the bundled, versioned
dictionary. The test suite pins results against independent oracles — known
English corrections and segmentations (`"hte"` → `"the"`,
`"thequickbrownfox"` → `"the quick brown fox"`) — not just round-trips
through the library. Malformed input (blank, multi-word where a single token
is required, out-of-range `max_edit_distance`/`top_n`, oversized text)
returns a structured `error` field instead of crashing — including guarding
a real crash in the underlying library (`word_segmentation("")` raises
`IndexError` outright; this package rejects blank input before calling in).

## Example

```bash
curl localhost:8083/nodes/CorrectWord -d '{"text":"hte"}'
# → {"input":"hte","candidates":[{"word":"the","editDistance":1,"frequency":"23135851162"}, ...]}

curl localhost:8083/nodes/SegmentText -d '{"text":"thequickbrownfox"}'
# → {"input":"thequickbrownfox","segmented":"the quick brown fox","editDistance":3,"logProbability":-14.56...}
```

## License

MIT © 2026 Christian George Lucas. Wraps symspellpy (MIT), including its
bundled frequency and bigram dictionaries (redistributed under symspellpy's
MIT license, originally from Wolf Garbe's SymSpell project; see "Dictionary
attribution" above for the underlying data's own CC BY 3.0 / SCOWL sourcing).
