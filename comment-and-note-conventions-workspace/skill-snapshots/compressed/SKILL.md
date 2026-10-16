---
name: comment-and-note-conventions
description: "The internal discipline (心法) of durable words in a project — comments, docstrings, docs, notes, TODOs: what earns one, where each must live, and how to judge the ones already on the page. Consult it before writing or reviewing durable text, or when a change may falsify or orphan the words around it — even when the word 'comment' is never spoken. Pair it with code-testing, whose tests are the strongest keeper a fact can have."
version: 1.0.1-eval-compressed
author: Adamancy Zhang
license: MIT
---

# Comments & Notes — The Discipline of Durable Words (惜字)

## Overview

Words beside code are trusted on sight, which is their value and their liability: a stale word stops the search — and the search was the thing that would have saved the reader. A missing word is honest ignorance; a false one is false confidence. This skill governs what earns a comment, what must never be written where it will be trusted, where each kind of note must live, and how to judge words already on the page — in any language, any project, any medium.

## The Iron Law

```
EVERY DURABLE WORD IS A PROMISE — WRITE ONLY WHAT A MECHANISM, A NEIGHBORHOOD, OR A CUSTODIAN CAN KEEP.
```

Three forces keep a promise true, in descending strength: a **mechanism** (a test, a validator, a generator) fails loudly when the words stop matching the world; a **neighborhood** brings the falsifying change and the word together by proximity, so the truth is met and re-earned every time the file is touched (a change that passes a word without meeting it has failed the neighborhood); a **custodian** (a person, a process, a declared trigger) renews the word on purpose. A word none of the three holds is a lie that has not happened yet — write only what something can keep.

## Keepers and their laws

Ask three questions, in order: **Who keeps this true? Whose fact is this? What breaks when it goes false — and who notices in time?** A keeper counts when it can be named, reached from the sentence, and pointed to its next occasion to meet the truth again; failing any of the three, install a keeper or leave the word unwritten. One keeper outranks the questions: the user's explicit instruction and the project's own declared practice — write it as asked; where you would judge differently, say so once; do not refuse, and do not later delete what was asked for. The strongest keeper sets the form: a fact a check can enforce belongs in the check; otherwise it stands at the smallest distance from its subject.

Two temptations of form:

- **Pointing.** A position (a line number, a page anchor, a name whose rename is recorded in some other system) rots in silence. A name — a symbol, a definition, a path in this repository — leaves a trail a tool or a reader can walk. A reference that crosses systems must say so, and say its drift will be silent.
- **Copying.** A fact has one home; prose must not restate what the code declares. A second copy needs declared coordinates (镜像坐标): the authoritative home, the invariant that binds the two, what renews the agreement, and what breaks on drift. A copy whose agreement nothing renews may not be written — it is a countdown.

And two forbidden tenses: the present, when it describes state (快照); the past, when it narrates a journey. State belongs to whatever holds the state; journeys belong to the change's own record. What stays beside the code is the *why*: what must stay true, and what breaks when it is violated. Where the world it names lies beyond this repository, a named re-check trigger keeps it.

## 6. What a comment is for

The code already says what it does — line by line, precisely, and it never drifts. A comment earns its place only by saying what the code cannot:

- **The semantics the syntax cannot carry** (口径): the range a value may take, what an absence means, where a value came from, which units, whose clock, which identity — meaning no type and no name can hold.
- **The constraints of use**: what must happen first, what must never happen at once, what the caller owes the callee.
- **The failure modes**: what breaks, and how it shows — the sentence that turns someone's future debugging night into a glide path.
- **The external contract**: what the world outside promised, which the code must honor even where the code looks wrong.
- **The counterintuitive**: the line that looks like a mistake and is not, so the next careful reader does not "fix" it.

The test is derivability. What could the reader get, just as fast, from the code itself? That is not a comment — it is a rehearsal of the code in prose, and it charges twice: the reader's time now, and their trust later, when it drifts. What the reader could not get at all — that is the comment that was always worth writing.

The test is relative to the reader. Derivability asks what this reader could get, just as fast, from the sources this reader can reach. A reader who cannot reach the code — a published interface, a consumer-facing page — cannot derive the contract; there the contract is the fact itself, and its keeper is the generation or the release process that publishes it.

And it must stand alone. A comment whose meaning requires a trip elsewhere is not a comment yet — it is half a sentence holding the other half hostage, and the missing half will rot first. A trip is a journey a reader must make in prose; a name the tooling can resolve is not a trip — and a fact with no other home, said here, is not a copy of anything.

Words whose form is owned by another discipline's declared process — a test-governance header, a generated-file marker, a lint pragma — are kept by that process, provided the process actually renews them; judge them by their owner's law, not this one.

## 7. Where notes live

A note is not homeless writing. Its address is decided by the same question as everything else: who keeps it true, and for how long must it stay true? The lifespan of the truth chooses the home — write the note where its keeper lives.

- **The change story** — what this task changed, and why — belongs to the change's own record, not to the code the change touched.
- **Decisions and their archaeology** — the road taken, the roads rejected, the constraints that forced the choice — belong to the decision's own record, with its date and status: superseded, not rewritten, so that the record remains true about itself.
- **Intentions** — not yet, next, someday — belong to the tracker, where they have owners, schedules, and permission to die honestly. A plan written into the code is a promise made to no one. An intention that names its keeper — a ticket, an owner, a declared trigger — is not that plan: it may stand where its consequence lands, judged by its keeper's law. Where no tracker is reachable, a TODO naming an owner or a trigger is the keeper made visible. Only a bare intention, naming no keeper and no trigger, is relocated or dropped. A documented architectural debt with a scheduled repayment is held by its schedule — record it where the schedule lives.
- **Current state** — what exists, what it counts, what it supports — belongs to the source that holds the state, or to a generated view of it. Never to a sentence someone would have to remember to edit.
- **Working memory** — the half-formed, the scratch note (of words, not of artifacts), the session's running notes, a person's or a machine's — belongs outside the project entirely, in whatever notebook its writer keeps. The repository is a record, not a desk; drafts written onto the record are how the record stops being worth reading.

The *why* of what must stay true stays beside its subject — at the smallest distance from the change that could falsify it.

## 8. Judging words already on the page

Existing words face the same three questions, now asked as a judge: who keeps this true, whose fact is it, and what breaks — for whom — if it goes false. But the audit's first error is certainty. A sentence can look like a violation and be load-bearing: the fact only it still carries, the constraint only it still explains, the 口径 no other home preserved. Precision is the judge's temptation, and over-deletion destroys exactly what the record exists to keep.

**Before the dispositions, one repair:** where a keeper can be installed in place — coordinates declared for a copy (镜像坐标), an owner or a ticket named for an intention, a re-check trigger for a fact this repository cannot guard — install it. A word that can acquire its keeper is not deleted; it is repaired.

Three dispositions, in order of preference:

- **Keep** — a keeper exists and the consequence of loss is real. However shabby the phrasing, a load-bearing fact stays.
- **Rewrite in place** — the fact deserves to live, but its form betrays it: a pointer becomes a naming or a statement of the fact itself; a restatement becomes the fact said once, at its home; a snapshot becomes a derivation, a kept word with its keeper installed, or — only when neither is possible — a deletion.
- **Delete** — no keeper, no consequence, nobody's search saved. Deletion is not loss; it is the record becoming honest by subtraction.

**When the keeper cannot be checked from where you sit** — it lives in someone's head, in another system, or outside the repository — the disposition is Keep. Delete is earned only when you can say, concretely, that nothing breaks and no search is saved; where you cannot say it, keep the word.

And this is a habit, not a campaign. Every time you change code, the words describing it are in front of you and the falsifying change is in your hands — reconcile them then, in the same diff, because that is the cheapest moment there will ever be. The duty's radius is the words this change touches; the rest of the record waits for its own change. Orphans left behind by a change — in code or in words — are the same kind of debt (the code-side orphan lists live in `architecture-thinking`; the word side is this section's own duty).

## Failure modes

Each of these is a way trust quietly dies:

- The comment that narrates what the code plainly says — words spent buying back what the reader already had.
- The second copy of a fact — accurate the day it was made, superstitious ever after.
- The snapshot of the present — a rumor of the past, still wearing the present tense.
- The list of callers no tool refreshes — complete until the first caller it never heard about.
- The diary entry in the permanent record — someone's afternoon, frozen into everyone's forever.
- The constraint no keeper renews — an imperative no mechanism, no neighborhood, and no custodian stands behind.
- The half sentence — a comment that means nothing until the reader takes the trip, and by then the trip is gone.
- The over-vigilant audit — precision that mistook a load-bearing fact for clutter.
- The map that outlived its ground — a pointer whose target moved on, and only the pointer stayed.
- The word kept far from its subject — the change and the comment never meet, and only the comment ages.

## Final Rule

```
A pointer to a place        → a map that ages as the ground moves
A second copy of a fact     → two truths, one of them kept by no one
Words about "now"           → the past, wearing the present tense
A restatement of the code   → the reader's trust, spent and unbought
A word the change meets     → a truth re-earned where it stands
What the code cannot say    → the comment that was always worth writing
A promise with a keeper     → a word that stays true
```
