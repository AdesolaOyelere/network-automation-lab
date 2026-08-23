# network-automation-lab

A public portfolio repo: self-contained network automation and administration
projects, built by Adesola Oyelere (network engineer) to demonstrate real Python
engineering in their own domain. It mirrors the structure and conventions of the
sibling repo `ai-training-lab` (same author, `../ai-training-lab`). For the exact
shape a finished project should take, look at
`03-ip-address-management/subnet-calculator/` in this repo first — it's the
reference example. If a convention isn't covered here or exemplified there, look at
a finished project in `ai-training-lab` (e.g. `07-finetuning/dataset-decontamination/`)
before guessing.

## The one hard rule

**Nothing in this repo talks to a real device.** Any project that would otherwise
need to SSH into a router/switch or hit a device API sits behind a small
transport/client interface with a deterministic mock — a fake device that returns
scripted, realistic command output and tracks its own state. Every project's tests
and `run.py` must work fully offline, with no lab hardware, VPN, or credentials.
State that limitation plainly in the project's README rather than implying it talks
to real gear.

Never commit real device credentials, IPs from a real production network, or a real
inventory file. Sample data is always synthetic. `.gitignore` blocks a few
secret-shaped filenames as a second layer — that is not a substitute for reviewing
`git status`/`git diff` before every commit.

## Repo structure

```
README.md, PROJECTS.md   generated index + hand-maintained backlog (see below)
LICENSE (MIT), pyproject.toml, .github/workflows/ci.yml
scripts/new_project.py   scaffold a new <category>/<slug>/ folder
scripts/gen_index.py     regenerate the tables in README.md/PROJECTS.md from meta.json
shared/README_TEMPLATE.md
01-device-automation/ … 10-tooling/   10 category folders, one per skill area
```

Every project lives at `<category>/<slug>/` and follows this shape:

```
<category>/<slug>/
  README.md      Problem -> Approach -> How to run -> Sample output -> What this demonstrates
  meta.json      {title, slug, category, status, skills[], summary}
  conftest.py    sys.path insert boilerplate (scaffold script does NOT create this — add manually)
  <core module>  the real logic: parsing, validation, diffing, scoring — pure Python, tested
  <mock module>  the fake device/transport layer, e.g. transport.py or device.py
  <dataset>      committed fixture data (jsonl/json/yaml) the project runs against
  run.py         CLI entry point; writes results/results.json, --report writes results/results.md
  requirements.txt   usually just a comment — most projects need only the stdlib
  tests/          real unit coverage of the core logic's edge cases, plus an end-to-end
                  test that pins the aggregate result against the committed results.json
  results/        committed sample output, viewable without running anything
```

## Workflow for adding a project

1. Check `PROJECTS.md`'s backlog for the item (or agree on a new one with the user);
   confirm the slug/category doesn't already exist and doesn't conceptually duplicate
   a done project — if there's real overlap, adjust the angle and say so in the README.
2. `python scripts/new_project.py <category> <slug> "<Title>" "<summary>"` to scaffold.
3. Add `conftest.py` manually.
4. Write the mock transport/device layer first, then the core logic against it.
5. **Run the code for real** to get actual numbers before writing a word of README
   prose or pinning a single test assertion. Never hand-compute an expected value —
   verify by executing. (A hand-computed test fixture was wrong and caught immediately
   by actually running it, in the sibling repo's history — that's the standard to hold
   here too.)
6. Write tests: direct coverage of the core logic's edge cases, plus one end-to-end
   test that pins results against `results/results.json`.
7. `python -m pytest` inside the project dir — all green.
8. `uvx ruff check <category>/<slug>` from repo root — fix any lint issues.
9. Write the README from the template, using only real numbers from step 5.
10. Flip the backlog line to `✅` in `PROJECTS.md`, then run
    `python scripts/gen_index.py` from repo root to regenerate the generated tables.
11. Run the full per-project regression loop from repo root before committing:
    ```
    for d in [0-9][0-9]-*/*/; do
      if ls "${d}tests/"test_*.py >/dev/null 2>&1 || ls "${d}"test_*.py >/dev/null 2>&1; then
        ( cd "$d" && python3 -m pytest -q ) || echo "FAIL: $d"
      fi
    done
    ```
12. Clean caches (`__pycache__`, `.pytest_cache`, `.ruff_cache`) before committing.
13. `git add` the new project dir plus the modified `README.md`/`PROJECTS.md` by name
    (never `git add -A`/`.`) and commit:
    ```
    Add <short description> (<category short name>)

    <1-3 sentences on what it does and the specific engineering point it demonstrates>

    Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
    ```

## Git and GitHub

- One commit per project, in the style above. No `--amend`, no force-push, no
  `--no-verify`.
- The GitHub remote exists: `origin` -> `https://github.com/AdesolaOyelere/network-automation-lab`
  (public), branch `main`. Push normally after each project's commit — no need to ask
  first for a routine push, but still confirm before anything destructive (force-push,
  history rewrite, `--amend` on a pushed commit).
- Local git identity for this repo: `Adesola Oyelere <oyelere.emmanuel@gmail.com>`
  (already configured locally, not global).
