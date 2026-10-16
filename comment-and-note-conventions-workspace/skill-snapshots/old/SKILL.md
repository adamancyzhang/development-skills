---
name: comment-and-note-conventions
description: "The internal discipline (心法) of every word written beside code — comments, docstrings, docs, notes: what earns a comment, what must never be written where it will be trusted, where each kind of note must live so it cannot drift out of date, and how to judge words already on the page. Consult it before writing, or while reviewing, any prose attached to a project — a comment, a docstring, a design doc, a note, a TODO, a changelog — even when the word 'comment' is never spoken. Pair it with code-testing, whose tests are the strongest keeper a fact can have."
version: 1.0.0
author: Adamancy Zhang
license: MIT
---

# Comments & Notes — The Discipline of Durable Words (惜字)

## Overview

Words are the one artifact a project asks its reader to believe on sight. A comment, a note, a page of documentation — each exists so the next mind does not have to re-derive, and each is read as true because being believed is the whole point. That is the value of prose around code, and it is also the liability. A missing comment is honest ignorance: it turns the reader back to the source, where the truth actually lives. A stale comment is false confidence: it stops the search — and the search was the thing that would have saved them. The most dangerous sentence in a file is not the absent one; it is the one that was true when it was written.

This skill is the discipline of that prose — what earns a comment, what must never be placed where it will be trusted, where every kind of note must live so it cannot drift, and how to judge words already on the page — in any language, any project, any medium a message can be left in. The strongest keeper a fact can have is an execution: a test that fails the moment the words go false. For that mechanism, see the `code-testing` skill; for the practice that writes the keeper first, `test-driven-development`. This skill governs the word itself.

These principles carry no language, framework, or worked example on purpose. They are meant to hold on the first project and the thousandth.

## The Iron Law

```
EVERY DURABLE WORD IS A PROMISE — WRITE ONLY WHAT A MECHANISM, A NEIGHBORHOOD, OR A KEEPER CAN KEEP.
```

Three forces can keep a promise true, in descending strength. A **mechanism** fails — loudly, by itself — the moment the words stop matching the world: a test, a validator, a generator that rewrites what it owns. A **neighborhood** brings the falsifying change and the word together by proximity — same file, same diff, same review — so the truth gets its chance to be re-earned every time it is threatened. A **keeper** — a person, a process, a declared trigger — renews the word on purpose, because someone owns the promise. A word none of the three holds is not a reminder or an aspiration; it is a lie that has not happened yet. Write only what something can keep.

## 1. Words are believed — and belief is the liability

Every sentence committed to the record spends two currencies: the reader's time when they read it, and the reader's trust if it ever turns out false. Stale words bankrupt the second currency — the very thing that made the words worth anything. The corollary is not "write less" but "write truer": one load-bearing fact outvalues a page of narration, because narration inflates exactly the surface a future reader must distrust.

Words that carry nothing are deleted with no loss: the record becomes leaner, not poorer. Untrustworthy words can only be tolerated or hunted — they are never quietly believed again. Write each sentence for a reader who cannot check it, because that reader is the one you are writing for.

Rot has one shape, wherever it appears: the world moves, the words do not, and nothing connects the two.

## 2. Every durable word needs a keeper

The Iron Law names the three keepers; this is how they are chosen. Before writing anything meant to outlive its moment, ask three questions, in order:

1. **Who keeps this true?** — a mechanism, a neighborhood, or a keeper. If no one, the sentence is already false; find it a keeper or leave it unwritten.
2. **Whose fact is this?** — if the fact lives somewhere else, its home is there, not here. Writing it here buys one reader's convenience and sells every future reader's accuracy.
3. **What breaks when it goes false — and who notices in time?** — if nothing breaks and no one ever notices, this is not information; it is decoration.

The strongest available keeper sets the sentence's right form. A fact a check could enforce belongs in the check — pushed to its enforcement point (执法点) and made loud, rather than left as prose hoping to be obeyed. A fact that cannot be executed belongs at the smallest distance from its subject, so the change that would falsify it must meet it face to face. Only what neither can hold is granted a human custodian — and then the custodian should be real, not implied.

## 3. Never point — name it, or say it where it stands

A position is the least durable thing a sentence can depend on. Files move, symbols are renamed, pages are reorganized — and a sentence pointing at the old location neither changes nor complains. A name is different in kind: a name can be searched, and a rename is a dated event — the trail from old name to new is on the record — so a mention that goes false can be hunted. A position cannot be searched for; when it moves, nothing remains to hunt. Names leave trails; positions rot in silence. This is the rot of the pointing reference (指路).

So there are exactly two honest ways to speak of the elsewhere. **Name it** — a name is a handle a future reader can pull, and where the tooling itself can walk to it — a symbol, a definition, a call graph — the tool carries the journey; a mechanism is kept by force. Or **say the fact here**, fully enough that the sentence stands without the trip: a fact stated at the point of need is paid for once, by the reader who needed it. What must never be written is a hand-drawn map.

## 4. Never keep a second copy of a fact

A fact has exactly one home. Every further copy is one reader's convenience paid for with a silent divergence: two copies cannot be corrected by the same act, so a day arrives when one of them is wrong — and nothing marks which. This is why prose must not restate what the code already declares (复述), why a document must not inventory what a source already lists, and why no comment should enumerate its callers — the calls declare themselves, and the declaration maintains itself for free.

Where a copy is truly unavoidable — a mirrored definition across a boundary no tool crosses — it may exist only with its coordinates declared (镜像坐标): name the authoritative home, state the invariant that binds the two (they must agree, exactly), and say what breaks when they drift. A copy with declared coordinates is a contract someone can police; a copy without is a countdown.

## 5. Never speak of now — or of then

Two tenses are forbidden in the durable record: the present, when it describes state; the past, when it narrates a journey.

A statement of current state (快照) is true exactly once — when it is written — and thereafter belongs to nobody: it is a copy of a state owned elsewhere, and any correction it ever receives is luck, not discipline. State belongs to whatever holds the state. An inventory wants to be a query; a progress line wants to be the tracker; a capability list wants to be the code's own declarations; a changelog wants to be a rendering of the records it summarizes; anything derivable wants to be derived — generated from its source and marked as generated, so that regeneration is the keeper and no hand ever edits it.

The journey — what was moved, what it replaced, what was tried and reverted — belongs to the change itself: its own record, dated by existence, scoped to its diff, read only by those who go looking. The past is not wrong to keep; it is wrong to keep here, where every reader pays for it and no reader needs it. Both temptations share one root: writing for the writer's present — what I know now, what I just did — when the record is read only in the writer's absence.

What remains beside the code, then, is the *why* of the present: not how we got here, but what must stay true — the constraint, and what breaks when it is violated. That why does not rot by the clock, because it is not a statement about time — it is a statement about the mechanism. Only a change in the world it names can falsify it, and that change happens right where the sentence lives.

## 6. What a comment is for

The code already says what it does — line by line, precisely, and it never drifts. A comment earns its place only by saying what the code cannot:

- **The semantics the syntax cannot carry** (口径): the range a value may take, what an absence means, where a value came from, which units, whose clock, which identity — meaning no type and no name can hold.
- **The constraints of use**: what must happen first, what must never happen at once, what the caller owes the callee.
- **The failure modes**: what breaks, and how it shows — the sentence that turns someone's future debugging night into a glide path.
- **The external contract**: what the world outside promised, which the code must honor even where the code looks wrong.
- **The counterintuitive**: the line that looks like a mistake and is not, so the next careful reader does not "fix" it.

The test is derivability. What could the reader get, just as fast, from the code itself? That is not a comment — it is a rehearsal of the code in prose, and it charges twice: the reader's time now, and their trust later, when it drifts. What the reader could not get at all — that is the comment that was always worth writing.

And it must stand alone. A comment whose meaning requires a trip elsewhere is not a comment yet — it is half a sentence holding the other half hostage, and the missing half will rot first.

## 7. Where notes live

A note is not homeless writing. Its address is decided by the same question as everything else: who keeps it true, and for how long must it stay true? The lifespan of the truth chooses the home — write the note where its keeper lives.

- **The change story** — what this task changed, and why — belongs to the change's own record, not to the code the change touched.
- **Decisions and their archaeology** — the road taken, the roads rejected, the constraints that forced the choice — belong to the decision's own record, with its date and status: superseded, not rewritten, so that the record remains true about itself.
- **Intentions** — not yet, next, someday — belong to the tracker, where they have owners, schedules, and permission to die honestly. A plan written into the code is a promise made to no one.
- **Current state** — what exists, what it counts, what it supports — belongs to the source that holds the state, or to a generated view of it. Never to a sentence someone would have to remember to edit.
- **Working memory** — the half-formed, the scratch, the session's running notes, a person's or a machine's — belongs outside the project entirely, in whatever notebook its writer keeps. The repository is a record, not a desk; drafts written onto the record are how the record stops being worth reading.

## 8. Judging words already on the page

Existing words face the same three questions, now asked as a judge: who keeps this true, whose fact is it, and what breaks — for whom — if it goes false. But the audit's first error is certainty. A sentence can look like a violation and be load-bearing: the fact only it still carries, the constraint only it still explains, the 口径 no other home preserved. Precision is the judge's temptation, and over-deletion destroys exactly what the record exists to keep.

Three dispositions, in order of preference:

- **Keep** — a keeper exists and the consequence of loss is real. However shabby the phrasing, a load-bearing fact stays.
- **Rewrite in place** — the fact deserves to live, but its form betrays it: a pointer becomes a naming or a statement of the fact itself; a restatement becomes the fact said once, at its home; a snapshot becomes either a derivation or a deletion.
- **Delete** — no keeper, no consequence, nobody's search saved. Deletion is not loss; it is the record becoming honest by subtraction.

And this is a habit, not a campaign. Every time you change code, the words describing it are in front of you and the falsifying change is in your hands — reconcile them then, in the same diff, because that is the cheapest moment there will ever be. Orphans left behind by a change — in code or in words — are the same kind of debt (see `architecture-thinking`).

## Failure modes

Each of these is a way trust quietly dies:

- The comment that narrates what the code plainly says — words spent buying back what the reader already had.
- The second copy of a fact — accurate the day it was made, superstitious ever after.
- The snapshot of the present — a rumor of the past, still wearing the present tense.
- The list of callers — complete until the first caller it never heard about.
- The diary entry in the permanent record — someone's afternoon, frozen into everyone's forever.
- The constraint with nothing enforcing it — an imperative with no police.
- The half sentence — a comment that means nothing until the reader takes the trip, and by then the trip is gone.
- The over-vigilant audit — precision that mistook a load-bearing fact for clutter.
- The map that outlived its ground — a pointer whose target moved on, and only the pointer stayed.

## Final Rule

```
A pointer to a place        → a map that ages as the ground moves
A second copy of a fact     → two truths, one of them unguarded
Words about "now"           → the past, wearing the present tense
A restatement of the code   → the reader's trust, spent and unbought
What the code cannot say    → the comment that was always worth writing
A promise with a keeper     → a word that stays true
```
