from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
	owner = Owner(name="Jordan", preferences={"preferred_task_types": ["walk", "feeding"]})

	pet1 = Pet(name="Mochi", species="dog", notes="Needs a morning walk.")
	pet2 = Pet(name="Nori", species="cat", notes="Indoor cat.")

	# Intentionally add tasks out of chronological order for sorting verification.
	pet1.add_task(
		Task(
			description="Evening walk",
			duration_minutes=30,
			time="18:30",
			frequency="daily",
			priority="high",
			task_type="walk",
		)
	)
	pet1.add_task(
		Task(
			description="Morning feeding",
			duration_minutes=15,
			time="07:45",
			frequency="daily",
			priority="high",
			task_type="feeding",
		)
	)
	pet1.add_task(
		Task(
			description="Midday meds",
			duration_minutes=10,
			time="12:10",
			frequency="daily",
			priority="medium",
			task_type="medication",
			is_completed=True,
		)
	)
	pet2.add_task(
		Task(
			description="Quick brushing",
			duration_minutes=15,
			time="07:45",
			frequency="daily",
			priority="low",
			task_type="grooming",
		)
	)
	pet2.add_task(
		Task(
			description="Litter box cleaning",
			duration_minutes=20,
			time="09:15",
			frequency="daily",
			priority="medium",
			task_type="cleaning",
		)
	)
	pet2.add_task(
		Task(
			description="Play session",
			duration_minutes=25,
			time="16:00",
			frequency="daily",
			priority="low",
			task_type="enrichment",
		)
	)

	owner.add_pet(pet1)
	owner.add_pet(pet2)

	scheduler = Scheduler()
	all_tasks = scheduler.retrieve_all_tasks(owner, include_completed=True)
	sorted_by_time = scheduler.sort_tasks_by_time(all_tasks)
	mochi_pending = scheduler.filter_tasks_by_status_or_pet(all_tasks, is_completed=False, pet_name="Mochi")
	mochi_pending_sorted = scheduler.sort_tasks_by_time(mochi_pending)
	completed_tasks = scheduler.filter_tasks_by_status_or_pet(all_tasks, is_completed=True)
	conflict_warnings = scheduler.get_conflict_warnings(all_tasks)
	today_tasks = scheduler.plan_tasks_for_day(owner, available_minutes=75, include_completed=False)

	print("Conflict Warnings")
	print("=" * 17)
	if conflict_warnings:
		for warning in conflict_warnings:
			print(f"Warning: {warning}")
	else:
		print("No scheduling conflicts detected.")

	print("Raw Task Order (as added)")
	print("=" * 24)
	for i, task in enumerate(all_tasks, start=1):
		pet_label = task.pet_name or "Unknown pet"
		time_label = task.time or "--:--"
		status_label = "done" if task.is_completed else "pending"
		print(f"{i}. [{pet_label}] {time_label} {task.description} ({status_label})")

	print("\nSorted by HH:MM")
	print("=" * 15)
	for i, task in enumerate(sorted_by_time, start=1):
		pet_label = task.pet_name or "Unknown pet"
		time_label = task.time or "--:--"
		print(f"{i}. [{pet_label}] {time_label} {task.description}")

	print("\nFiltered: Mochi pending tasks")
	print("=" * 29)
	for i, task in enumerate(mochi_pending_sorted, start=1):
		time_label = task.time or "--:--"
		print(f"{i}. {time_label} {task.description}")

	print("\nFiltered: Completed tasks")
	print("=" * 25)
	for i, task in enumerate(completed_tasks, start=1):
		pet_label = task.pet_name or "Unknown pet"
		time_label = task.time or "--:--"
		print(f"{i}. [{pet_label}] {time_label} {task.description}")

	print("\nToday's Schedule (75 min budget)")
	print("=" * 16)
	if not today_tasks:
		print("No tasks fit within the available time.")
		return

	total = 0
	for i, task in enumerate(today_tasks, start=1):
		total += task.duration_minutes
		pet_label = task.pet_name or "Unknown pet"
		print(f"{i}. [{pet_label}] {task.description} ({task.duration_minutes} min)")

	print(f"Total planned time: {total} minutes")


if __name__ == "__main__":
	main()
