from datetime import date

from pawpal_system import Owner, Pet, PlanningConstraints, Scheduler, SchedulerService, Task


def test_task_mark_complete_changes_status() -> None:
	task = Task(description="Give medicine", duration_minutes=10)

	assert task.is_completed is False
	task.mark_complete()
	assert task.is_completed is True


def test_add_task_to_pet_increases_task_count() -> None:
	pet = Pet(name="Mochi", species="dog")
	task = Task(description="Evening walk", duration_minutes=20)

	initial_count = len(pet.tasks)
	pet.add_task(task)

	assert len(pet.tasks) == initial_count + 1


def test_sort_tasks_by_time_orders_shortest_first() -> None:
	scheduler = Scheduler()
	tasks = [
		Task(description="Long walk", duration_minutes=45, priority="high"),
		Task(description="Quick feed", duration_minutes=10, priority="medium"),
		Task(description="Brush coat", duration_minutes=15, priority="low"),
	]

	ordered = scheduler.sort_tasks_by_time(tasks)

	assert [task.description for task in ordered] == ["Quick feed", "Brush coat", "Long walk"]


def test_sort_tasks_by_hhmm_time_attribute() -> None:
	scheduler = Scheduler()
	tasks = [
		Task(description="Meds", duration_minutes=10, time="14:30"),
		Task(description="Breakfast", duration_minutes=15, time="08:00"),
		Task(description="Lunch", duration_minutes=20, time="12:15"),
	]

	ordered = scheduler.sort_tasks_by_time(tasks)

	assert [task.description for task in ordered] == ["Breakfast", "Lunch", "Meds"]


def test_filter_tasks_by_pet_and_status() -> None:
	scheduler = Scheduler()
	tasks = [
		Task(description="Dog walk", duration_minutes=20, pet_name="Mochi", is_completed=False),
		Task(description="Cat feed", duration_minutes=10, pet_name="Nori", is_completed=False),
		Task(description="Dog meds", duration_minutes=5, pet_name="Mochi", is_completed=True),
	]

	filtered = scheduler.filter_tasks(tasks, pet_name="Mochi", is_completed=False)

	assert len(filtered) == 1
	assert filtered[0].description == "Dog walk"


def test_filter_tasks_by_status_or_pet_pet_only() -> None:
	scheduler = Scheduler()
	tasks = [
		Task(description="Dog walk", duration_minutes=20, pet_name="Mochi", is_completed=False),
		Task(description="Cat feed", duration_minutes=10, pet_name="Nori", is_completed=False),
	]

	filtered = scheduler.filter_tasks_by_status_or_pet(tasks, pet_name="Mochi")

	assert [task.description for task in filtered] == ["Dog walk"]


def test_filter_tasks_by_status_or_pet_status_only() -> None:
	scheduler = Scheduler()
	tasks = [
		Task(description="Dog walk", duration_minutes=20, pet_name="Mochi", is_completed=False),
		Task(description="Dog meds", duration_minutes=5, pet_name="Mochi", is_completed=True),
	]

	filtered = scheduler.filter_tasks_by_status_or_pet(tasks, is_completed=True)

	assert [task.description for task in filtered] == ["Dog meds"]


def test_complete_task_with_recurrence_creates_next_daily_instance() -> None:
	scheduler = Scheduler()
	pet = Pet(name="Mochi", species="dog")
	task = Task(
		description="Daily walk",
		duration_minutes=20,
		frequency="daily",
		time="08:00",
		due_date=date(2026, 3, 28),
	)
	pet.add_task(task)

	next_task = scheduler.complete_task_with_recurrence(pet, task)

	assert task.is_completed is True
	assert next_task is not None
	assert next_task.description == "Daily walk"
	assert next_task.is_completed is False
	assert next_task.frequency == "daily"
	assert next_task.due_date == date(2026, 3, 29)
	assert len(pet.tasks) == 2


def test_complete_task_with_recurrence_creates_next_weekly_instance() -> None:
	scheduler = Scheduler()
	pet = Pet(name="Nori", species="cat")
	task = Task(
		description="Weekly grooming",
		duration_minutes=30,
		frequency="weekly",
		due_date=date(2026, 3, 28),
	)
	pet.add_task(task)

	next_task = scheduler.complete_task_with_recurrence(pet, task)

	assert task.is_completed is True
	assert next_task is not None
	assert next_task.frequency == "weekly"
	assert next_task.is_completed is False
	assert next_task.due_date == date(2026, 4, 4)
	assert len(pet.tasks) == 2


def test_complete_task_with_recurrence_does_not_clone_one_time_task() -> None:
	scheduler = Scheduler()
	pet = Pet(name="Mochi", species="dog")
	task = Task(description="Vet visit", duration_minutes=60, frequency="once")
	pet.add_task(task)

	next_task = scheduler.complete_task_with_recurrence(pet, task)

	assert task.is_completed is True
	assert next_task is None
	assert len(pet.tasks) == 1


def test_detect_task_time_conflicts_for_same_pet() -> None:
	scheduler = Scheduler()
	tasks = [
		Task(description="Morning walk", duration_minutes=30, time="08:00", pet_name="Mochi"),
		Task(description="Breakfast", duration_minutes=20, time="08:15", pet_name="Mochi"),
		Task(description="Noon play", duration_minutes=15, time="12:00", pet_name="Mochi"),
	]

	conflicts = scheduler.detect_task_time_conflicts(tasks)

	assert len(conflicts) == 1
	assert conflicts[0][0].description == "Morning walk"
	assert conflicts[0][1].description == "Breakfast"


def test_detect_task_time_conflicts_for_different_pets() -> None:
	scheduler = Scheduler()
	tasks = [
		Task(description="Dog walk", duration_minutes=30, time="09:00", pet_name="Mochi"),
		Task(description="Cat feeding", duration_minutes=15, time="09:10", pet_name="Nori"),
	]

	conflicts = scheduler.detect_task_time_conflicts(tasks)

	assert len(conflicts) == 1
	assert {conflicts[0][0].pet_name, conflicts[0][1].pet_name} == {"Mochi", "Nori"}


def test_detect_task_time_conflicts_returns_empty_when_no_overlap() -> None:
	scheduler = Scheduler()
	tasks = [
		Task(description="Walk", duration_minutes=20, time="08:00", pet_name="Mochi"),
		Task(description="Feeding", duration_minutes=15, time="08:30", pet_name="Mochi"),
		Task(description="Play", duration_minutes=10, time="10:00", pet_name="Nori"),
	]

	conflicts = scheduler.detect_task_time_conflicts(tasks)

	assert conflicts == []


def test_get_conflict_warnings_returns_messages_without_exception() -> None:
	scheduler = Scheduler()
	tasks = [
		Task(description="Dog walk", duration_minutes=30, time="09:00", pet_name="Mochi"),
		Task(description="Cat feeding", duration_minutes=20, time="09:10", pet_name="Nori"),
	]

	warnings = scheduler.get_conflict_warnings(tasks)

	assert len(warnings) == 1
	assert "Conflict:" in warnings[0]
	assert "Dog walk" in warnings[0]
	assert "Cat feeding" in warnings[0]


def test_get_conflict_warnings_returns_empty_when_no_conflict() -> None:
	scheduler = Scheduler()
	tasks = [
		Task(description="Walk", duration_minutes=20, time="08:00", pet_name="Mochi"),
		Task(description="Feed", duration_minutes=15, time="08:30", pet_name="Nori"),
	]

	warnings = scheduler.get_conflict_warnings(tasks)

	assert warnings == []


def test_generate_plan_respects_recurring_day_rules() -> None:
	scheduler = SchedulerService()
	owner = Owner(name="Jordan")
	pet = Pet(name="Mochi", species="dog")

	tasks = [
		Task(description="Daily walk", duration_minutes=20, frequency="daily", priority="high", pet_name="Mochi"),
		Task(description="Tuesday grooming", duration_minutes=15, frequency="tuesday", priority="medium", pet_name="Mochi"),
		Task(description="Mon/Wed meds", duration_minutes=10, frequency="weekly:mon,wed", priority="high", pet_name="Mochi"),
	]

	for task in tasks:
		pet.add_task(task)

	constraints = PlanningConstraints(available_minutes=60, day_start="08:00", day_name="monday")
	plan = scheduler.generate_plan(owner=owner, pet=pet, tasks=tasks, constraints=constraints)

	selected = [entry.task.description for entry in plan.entries]
	assert "Daily walk" in selected
	assert "Mon/Wed meds" in selected
	assert "Tuesday grooming" not in selected


def test_generate_plan_skips_conflicting_preferred_window() -> None:
	scheduler = SchedulerService()
	owner = Owner(name="Jordan")
	pet = Pet(name="Mochi", species="dog")

	tasks = [
		Task(
			description="Morning walk",
			duration_minutes=30,
			frequency="daily",
			priority="high",
			pet_name="Mochi",
			preferred_window="08:00-08:45",
		),
		Task(
			description="Breakfast",
			duration_minutes=20,
			frequency="daily",
			priority="high",
			pet_name="Mochi",
			preferred_window="08:00-08:15",
		),
	]

	constraints = PlanningConstraints(available_minutes=60, day_start="08:00", day_name="monday")
	plan = scheduler.generate_plan(owner=owner, pet=pet, tasks=tasks, constraints=constraints)

	selected = [entry.task.description for entry in plan.entries]
	skipped = [task.description for task in plan.skipped_tasks]

	assert "Morning walk" in selected
	assert "Breakfast" in skipped
