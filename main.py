from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
	owner = Owner(name="Jordan", preferences={"preferred_task_types": ["walk", "feeding"]})

	pet1 = Pet(name="Mochi", species="dog", notes="Needs a morning walk.")
	pet2 = Pet(name="Nori", species="cat", notes="Indoor cat.")

	pet1.add_task(
		Task(
			description="Morning walk",
			duration_minutes=30,
			frequency="daily",
			priority="high",
			task_type="walk",
		)
	)
	pet1.add_task(
		Task(
			description="Breakfast feeding",
			duration_minutes=15,
			frequency="daily",
			priority="high",
			task_type="feeding",
		)
	)
	pet2.add_task(
		Task(
			description="Litter box cleaning",
			duration_minutes=20,
			frequency="daily",
			priority="medium",
			task_type="cleaning",
		)
	)

	owner.add_pet(pet1)
	owner.add_pet(pet2)

	scheduler = Scheduler()
	today_tasks = scheduler.plan_tasks_for_day(owner, available_minutes=75)

	print("Today's Schedule")
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
