# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

Recent updates add lightweight intelligence to planning:

- Time-aware sorting using HH:MM task start times.
- Flexible filtering by pet name and completion status.
- Recurring task rollover for daily and weekly tasks when completed.
- Conflict detection for overlapping task windows (same pet or different pets).
- Non-blocking conflict warnings so planning continues without crashing.

## Getting started

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Testing PawPal+

Use pytest to validate scheduler behaviors before demoing or submitting.

### Run all tests

```bash
python -m pytest
```

### Run focused scheduler checks

```bash
python -m pytest -q tests/test_pawpal.py -k "sort_tasks_by_hhmm_time_attribute or complete_task_with_recurrence_creates_next_daily_instance or detect_task_time_conflicts_for_exact_same_time_interval"
```

### What these tests verify

- The test suite covers scheduler happy paths and edge cases for sorting, recurrence rollover, filtering, conflict detection, and daily planning constraints.
- Sorting correctness: tasks with HH:MM times are returned in chronological order.
- Recurrence logic: completing a daily task creates a new pending task for the next day.
- Conflict detection: duplicate/overlapping times are flagged by the scheduler.

### Confidence Level: ★★★★☆ (4/5)

Reasoning based on results:

Full suite passed: 28 tests.
Targeted critical checks passed for sorting, daily recurrence rollover, and duplicate-time conflict detection.
Coverage includes both happy paths and important edge cases (empty plans, overlap boundaries, filtering normalization, budget/window constraints).