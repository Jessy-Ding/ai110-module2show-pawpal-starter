from pawpal_system import Pet, Task


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
