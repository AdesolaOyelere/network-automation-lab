# <Project Title>

> One-sentence description of what this project does and the skill it demonstrates.

**Category:** <category> · **Skills:** <comma-separated>

## Problem

What real network engineering/administration problem this addresses, in two or three
sentences.

## Approach

How it works. Keep it concrete: the core logic, the data/config shapes, the interfaces.

## How to run

```bash
python -m pytest            # deterministic core, no live device needed
python run.py --help        # entry point
```

Any project that would otherwise need a real device hides it behind a transport
interface with a deterministic mock, so tests and CI never need lab hardware or
credentials. Real sample output (against the mock) is committed.

## Sample output

Paste or link a small, real example from `results/`.

## What this demonstrates

Two or three bullets naming the concrete skills a reviewer should take away.
