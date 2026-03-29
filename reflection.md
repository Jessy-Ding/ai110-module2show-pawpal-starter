# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Answer: For this phase, I designed a requirement-first UML that a teacher can quickly map to the assignment rubric: clear data models, one scheduling service, one controller, and a thin Streamlit UI in `app.py`. The design intentionally avoids over-engineering while still supporting constraints, prioritization, and plan explanation.

I used these classes and responsibilities:

1. `Owner`
- Stores owner identity/preferences and manages multiple pets.

2. `Pet`
- Stores pet profile and a list of care tasks.

3. `Task`
- Represents each care activity (description, duration, frequency, completion status, priority, type, linked pet, optional preferred window).

4. `PlanningConstraints`
- Captures daily limits and user choices (available minutes and optional start time).

5. `ScheduleEntry`
- Represents one scheduled task with start/end and a short reason.

6. `DailyPlan`
- Contains ordered schedule entries and summary fields (used minutes, skipped tasks).

7. `SchedulerService`
- Core algorithm unit that filters tasks by constraints, ranks by priority, and builds `DailyPlan`.

8. `Scheduler`
- Shared scheduling "brain" that retrieves and organizes tasks across all of an owner's pets.

9. `PawPalController`
- Orchestrates app flow: validates UI input, builds domain objects, calls scheduler, returns output.

10. `StreamlitApp_app_py`
- The actual UI boundary in `app.py`: collects form inputs, triggers controller actions, displays tasks and plan.

Initial UML (phase-appropriate draft):

```mermaid
classDiagram
    class Owner {
        +name: str
        +preferences: dict
        +pets: list
        +add_pet(pet)
        +get_pet(pet_name)
        +get_all_tasks(include_completed)
    }

    class Pet {
        +name: str
        +species: str
        +notes: str
        +tasks: list
        +add_task(task)
        +get_pending_tasks()
        +remove_task(description)
    }

    class Task {
        +description: str
        +duration_minutes: int
        +frequency: str
        +is_completed: bool
        +priority: str
        +task_type: str
        +pet_name: Optional[str]
        +preferred_window: Optional[str]
        +mark_complete()
        +mark_incomplete()
    }

    class PlanningConstraints {
        +available_minutes: int
        +day_start: str
    }

    class ScheduleEntry {
        +start_time: str
        +end_time: str
        +reason: str
    }

    class DailyPlan {
        +entries: list
        +used_minutes: int
        +skipped_tasks: list
    }

    class SchedulerService {
        +_add_minutes(time_str, minutes): str
        +generate_plan(owner, pet, tasks, constraints): DailyPlan
        +score_task(task, owner, pet): int
        +fits_constraints(task, remaining_minutes): bool
    }

    class Scheduler {
        +PRIORITY_SCORE: dict
        +retrieve_all_tasks(owner, include_completed): list
        +organize_tasks(tasks): list
        +plan_tasks_for_day(owner, available_minutes, include_completed): list
    }

    class PawPalController {
        +add_task(task_data): Task
        +build_plan(owner_data, pet_data, tasks_data, constraints_data): DailyPlan
    }

    class StreamlitApp_app_py {
        +collect_inputs()
        +on_add_task()
        +on_generate_schedule()
        +render_task_table(tasks)
        +render_plan(plan)
    }

    Owner "1" --> "1..*" Pet : owns
    Pet "1" --> "0..*" Task : requires
    SchedulerService --|> Scheduler : extends
    Scheduler ..> Owner : retrieves tasks
    Scheduler ..> Task : orders by priority
    SchedulerService ..> Owner : reads preferences
    SchedulerService ..> Pet : reads profile
    SchedulerService ..> Task : evaluates
    SchedulerService ..> PlanningConstraints : applies
    SchedulerService --> DailyPlan : produces
    DailyPlan *-- "1..*" ScheduleEntry : contains
    ScheduleEntry --> Task : schedules
    PawPalController --> SchedulerService : calls
    StreamlitApp_app_py --> PawPalController : sends input
    StreamlitApp_app_py --> DailyPlan : renders output
```

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Answer: Yes. After reviewing and implementing the skeleton, I made two targeted design changes.

1. Added an explicit Task-to-Pet link
- Change: I added `pet_name: Optional[str]` to `Task`.
- Why: The earlier model had an implied relationship (`Pet` requires tasks), but each task object did not explicitly store which pet it belonged to. This could become a bottleneck if the app later supports multiple pets, because scheduling would not be able to unambiguously assign tasks.

2. Split scheduling responsibility into `Scheduler` + `SchedulerService`
- Change: I introduced a base `Scheduler` class for cross-pet retrieval and organization (`retrieve_all_tasks`, `organize_tasks`, `plan_tasks_for_day`) and kept `SchedulerService` for concrete plan generation (`generate_plan`, `score_task`, `fits_constraints`).
- Why: This reduced logic bottlenecks by separating generic scheduling behavior from app-specific plan building. It also improved maintainability and made the owner-pet-task traversal explicit.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

Answer: One tradeoff my scheduler makes is using a lightweight conflict-handling strategy: it detects overlapping task windows and returns warning messages, but it does not automatically optimize or re-arrange the schedule to resolve every conflict. In other words, the system prioritizes clarity and stability over full automatic optimization.

This is reasonable for the PawPal+ scenario because the owner still gets a usable plan quickly, plus clear warnings they can act on, without the app becoming overly complex or unpredictable. For a class project and early product version, this approach keeps the code maintainable while still preventing silent scheduling mistakes.

---
## Final UML 

```mermaid
classDiagram
    class Owner {
        +name: str
        +preferences: Dict[str, Any]
        +pets: List[Pet]
        +add_pet(pet: Pet) None
        +get_pet(pet_name: str) Optional[Pet]
        +get_all_tasks(include_completed: bool) List[Task]
    }

    class Pet {
        +name: str
        +species: str
        +notes: str
        +tasks: List[Task]
        +add_task(task: Task) None
        +get_pending_tasks() List[Task]
        +remove_task(description: str) bool
    }

    class Task {
        +description: str
        +duration_minutes: int
        +time: Optional[str]
        +due_date: Optional[date]
        +frequency: str
        +is_completed: bool
        +priority: str
        +task_type: str
        +pet_name: Optional[str]
        +preferred_window: Optional[str]
        +title: str
        +mark_complete() None
        +mark_incomplete() None
    }

    class PlanningConstraints {
        +available_minutes: int
        +day_start: str
        +day_name: str
    }

    class ScheduleEntry {
        +task: Task
        +start_time: str
        +end_time: str
        +reason: str
    }

    class DailyPlan {
        +entries: List[ScheduleEntry]
        +used_minutes: int
        +skipped_tasks: List[Task]
    }

    class Scheduler {
        +PRIORITY_SCORE: Dict
        +retrieve_all_tasks(owner: Owner, include_completed: bool, pet_name: Optional[str]) List[Task]
        +filter_tasks(tasks: List[Task], pet_name: Optional[str], is_completed: Optional[bool]) List[Task]
        +filter_tasks_by_status_or_pet(tasks: List[Task], is_completed: Optional[bool], pet_name: Optional[str]) List[Task]
        +complete_task_with_recurrence(pet: Pet, task: Task) Optional[Task]
        +sort_tasks_by_time(tasks: List[Task], reverse: bool) List[Task]
        +detect_task_time_conflicts(tasks: List[Task]) List[tuple[Task, Task]]
        +get_conflict_warnings(tasks: List[Task]) List[str]
        +organize_tasks(tasks: List[Task], sort_by_time: bool) List[Task]
        +plan_tasks_for_day(owner: Owner, available_minutes: int, include_completed: bool, pet_name: Optional[str], status: Optional[bool], sort_by_time: bool) List[Task]
    }

    class SchedulerService {
        +WEEKDAY_LOOKUP: Dict
        +is_task_due_on_day(task: Task, day_name: str) bool
        +detect_conflict(proposed_start: int, proposed_end: int, entries: List[ScheduleEntry]) bool
        +generate_plan(owner: Owner, pet: Pet, tasks: List[Task], constraints: PlanningConstraints) DailyPlan
        +score_task(task: Task, owner: Owner, pet: Pet) int
        +fits_constraints(task: Task, remaining_minutes: int) bool
    }

    class PawPalController {
        +scheduler: SchedulerService
        +add_task(task_data: Dict[str, Any]) Task
        +build_plan(owner_data: Dict[str, Any], pet_data: Dict[str, Any], tasks_data: List[Dict[str, Any]], constraints_data: Dict[str, Any]) DailyPlan
    }

    Owner "1" --> "0..*" Pet : owns
    Pet "1" --> "0..*" Task : has
    SchedulerService --|> Scheduler : extends
    Scheduler ..> Owner : retrieves
    Scheduler ..> Pet : reads
    Scheduler ..> Task : filters/sorts
    SchedulerService ..> PlanningConstraints : applies
    SchedulerService --> DailyPlan : produces
    DailyPlan *-- "0..*" ScheduleEntry : contains
    ScheduleEntry --> Task : schedules
    PawPalController --> SchedulerService : calls
    PawPalController ..> Owner : constructs
    PawPalController ..> Pet : constructs
    PawPalController ..> Task : constructs
```


## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
