# PawPal+

PawPal+ is a Streamlit-based pet care planning app. It helps owners manage tasks across pets, prioritize daily care, detect scheduling conflicts, and generate practical day plans.

## Table of Contents

- Overview
- Key Features
- Architecture
- Project Structure
- Quick Start
- Running the App
- How to Use PawPal+
- 📸 Demo
- Testing
- UML Artifacts
- Troubleshooting

## Overview

PawPal+ solves a common planning problem for pet owners: too many care tasks and not enough time. The app allows users to:

- Create an owner profile and multiple pets
- Add care tasks with duration, priority, frequency, and optional start time
- Filter and sort tasks cleanly
- Generate a schedule within a time budget
- Detect and explain overlapping task conflicts without interrupting planning

## Key Features

- Time-aware sorting: orders timed tasks by HH:MM, then by duration, priority, and description; untimed tasks are placed after timed tasks.
- Priority scoring: ranks tasks using high/medium/low weights (3/2/1) during organization and selection.
- Flexible filtering: supports pet filtering and completion-status filtering independently or combined.
- Recurrence rollover: marking daily/weekly tasks complete creates a new pending task with due date advanced by +1 or +7 days.
- Recurrence day matching: evaluates daily, named weekdays, and weekly lists (for example weekly:mon,wed) against the planning day.
- Conflict detection algorithm: uses sorted time intervals and overlap checks to catch both same-pet and cross-pet conflicts.
- Non-blocking conflict warnings: returns readable conflict messages without interrupting plan generation.
- Preferred window constraints: enforces HH:MM-HH:MM task windows and skips tasks that do not fit.
- Budget-constrained planning: greedily selects tasks that fit within available minutes and tracks skipped tasks separately.

## Architecture

Core implementation is in [pawpal_system.py](pawpal_system.py).

- Owner: stores owner identity, preferences, and pet collection
- Pet: stores pet profile and task list
- Task: stores task metadata (duration, time, frequency, status, etc.)
- Scheduler: shared scheduling utilities (sorting, filtering, recurrence, conflicts)
- SchedulerService: plan-generation logic and constraint handling
- PawPalController: validates incoming task data and builds plans from UI payloads

Streamlit UI entry point: [app.py](app.py)

## Project Structure

- [app.py](app.py): Streamlit UI
- [main.py](main.py): CLI-style example usage/demo
- [pawpal_system.py](pawpal_system.py): domain model + scheduling logic
- [tests/test_pawpal.py](tests/test_pawpal.py): automated test suite
- [reflection.md](reflection.md): design reflection and UML history
- [uml_final.mmd](uml_final.mmd): final Mermaid UML source
- [uml_final.png](uml_final.png): final UML image export

## Quick Start

### 1. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the App

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal (usually http://localhost:8501).

## How to Use PawPal+

1. Enter owner name.
2. Add one or more pets.
3. Select a pet and add tasks.
4. Optionally provide task start times in HH:MM format.
5. Use task status filters to inspect pending/completed tasks.
6. Click Generate schedule and set available daily minutes.
7. Review schedule table and conflict warnings.

## 📸 Demo

<a href="/course_images/ai110/pawpal_final_app.png" target="_blank"><img src='/course_images/ai110/pawpal_final_app.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

## Testing

### Run all tests

```bash
python -m pytest
```

### Run focused scheduler checks

```bash
python -m pytest -q tests/test_pawpal.py -k "sort_tasks_by_hhmm_time_attribute or complete_task_with_recurrence_creates_next_daily_instance or detect_task_time_conflicts_for_exact_same_time_interval"
```

### Coverage summary

The suite validates both happy paths and edge cases for:

- Sorting correctness
- Recurrence rollover behavior
- Filtering by pet and completion status
- Conflict detection and warning generation
- Daily planning constraints and skip logic

Current confidence level based on passing automated tests: 4/5.

## UML Artifacts

- Editable Mermaid source: [uml_final.mmd](uml_final.mmd)
- Exported diagram image: [uml_final.png](uml_final.png)
- Reflection document: [reflection.md](reflection.md)

## Troubleshooting

- Command not found for streamlit:
Install dependencies with pip install -r requirements.txt and confirm your virtual environment is active.

- Tests fail unexpectedly:
Run python -m pytest -q for detailed test output and inspect [tests/test_pawpal.py](tests/test_pawpal.py).

- Diagram rendering issues:
Use the Mermaid source in [uml_final.mmd](uml_final.mmd) and regenerate the image if needed.