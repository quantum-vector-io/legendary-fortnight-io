# Legendary Fortnight Lab

This repository is a personal laboratory for exploring new languages, frameworks, interview questions, and math topics. It is organized to keep quick experiments separate from reusable knowledge and long-term notes, so everything stays searchable and easy to revisit.

## Layout

- `experiments/` — time-boxed explorations named `YYYY-MM/topic` with throwaway code, scratch notes, and command logs.
- `foundations/` — reusable snippets, reference implementations, proofs, or helpers organized by domain (e.g., `math/`, `algorithms/`).
- `interview-prep/` — preparation material grouped by focus area such as `behavioral/`, `coding/`, and `system-design/`.
- `notes/` — dated log entries (`YYYY-MM-DD.md`) capturing insights, resources, and follow-ups that link back to experiments or foundations.
- `scripts/` — utilities that speed up new experiment scaffolding or automate repetitive tasks.
- `.editorconfig`, linters, and other shared config live at the repo root so every experiment benefits from consistent tooling.

## Getting Started

1. Pick a question or topic worth exploring.
2. Run `./scripts/new-experiment.ps1` (or scaffold manually) to create a new folder under `experiments/` using the `YYYY-MM/topic` convention.
3. Capture the goal in the experiment README, work through the problem, and jot down findings or commands. Push any valuable results to `foundations/` when they feel reusable.
4. Record learnings in the daily `notes/` entry so you can track progress over time.

## Conventions

- Keep experiment folders light and disposable; archive only what you might revisit.
- Promote code or ideas worth keeping into `foundations/` with a short README explaining usage.
- Reference related experiments or notes with relative links to create a knowledge trail.
- Favor small commits/branches per experiment if you decide to version control progress.

Happy exploring!
