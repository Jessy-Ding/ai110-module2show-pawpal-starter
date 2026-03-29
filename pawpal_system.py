from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Owner:
	name: str
	preferences: Dict[str, Any] = field(default_factory=dict)
	pets: List["Pet"] = field(default_factory=list)

	def add_pet(self, pet: "Pet") -> None:
		self.pets.append(pet)

	def get_pet(self, pet_name: str) -> Optional["Pet"]:
		for pet in self.pets:
			if pet.name == pet_name:
				return pet
		return None

	def get_all_tasks(self, include_completed: bool = True) -> List["Task"]:
		all_tasks: List[Task] = []
		for pet in self.pets:
			if include_completed:
				all_tasks.extend(pet.tasks)
			else:
				all_tasks.extend(pet.get_pending_tasks())
		return all_tasks


@dataclass
class Pet:
	name: str
	species: str
	notes: str = ""
	tasks: List["Task"] = field(default_factory=list)

	def add_task(self, task: "Task") -> None:
		if task.pet_name is None:
			task.pet_name = self.name
		self.tasks.append(task)

	def get_pending_tasks(self) -> List["Task"]:
		return [task for task in self.tasks if not task.is_completed]

	def remove_task(self, description: str) -> bool:
		for i, task in enumerate(self.tasks):
			if task.description == description:
				del self.tasks[i]
				return True
		return False


@dataclass
class Task:
	description: str
	duration_minutes: int
	frequency: str = "daily"
	is_completed: bool = False
	priority: str = "medium"
	task_type: str = "general"
	pet_name: Optional[str] = None
	preferred_window: Optional[str] = None

	@property
	def title(self) -> str:
		return self.description

	def mark_complete(self) -> None:
		self.is_completed = True

	def mark_incomplete(self) -> None:
		self.is_completed = False


@dataclass
class PlanningConstraints:
	available_minutes: int
	day_start: str = "08:00"


@dataclass
class ScheduleEntry:
	task: Task
	start_time: str
	end_time: str
	reason: str


@dataclass
class DailyPlan:
	entries: List[ScheduleEntry] = field(default_factory=list)
	used_minutes: int = 0
	skipped_tasks: List[Task] = field(default_factory=list)


class Scheduler:
	PRIORITY_SCORE = {
		"high": 3,
		"medium": 2,
		"low": 1,
	}

	def retrieve_all_tasks(self, owner: Owner, include_completed: bool = False) -> List[Task]:
		return owner.get_all_tasks(include_completed=include_completed)

	def organize_tasks(self, tasks: List[Task]) -> List[Task]:
		return sorted(
			tasks,
			key=lambda task: (
				-self.PRIORITY_SCORE.get(task.priority.lower(), 0),
				task.duration_minutes,
				task.description.lower(),
			),
		)

	def plan_tasks_for_day(
		self,
		owner: Owner,
		available_minutes: int,
		include_completed: bool = False,
	) -> List[Task]:
		remaining = available_minutes
		selected: List[Task] = []
		for task in self.organize_tasks(self.retrieve_all_tasks(owner, include_completed=include_completed)):
			if task.duration_minutes <= remaining:
				selected.append(task)
				remaining -= task.duration_minutes
		return selected


class SchedulerService(Scheduler):
	@staticmethod
	def _add_minutes(time_str: str, minutes: int) -> str:
		hour_str, minute_str = time_str.split(":")
		total_minutes = int(hour_str) * 60 + int(minute_str) + minutes
		total_minutes %= 24 * 60
		hour = total_minutes // 60
		minute = total_minutes % 60
		return f"{hour:02d}:{minute:02d}"

	def generate_plan(
		self,
		owner: Owner,
		pet: Pet,
		tasks: List[Task],
		constraints: PlanningConstraints,
	) -> DailyPlan:
		candidate_tasks = tasks if tasks else pet.get_pending_tasks()
		ordered = self.organize_tasks(
			[task for task in candidate_tasks if self.fits_constraints(task, constraints.available_minutes)]
		)

		remaining = constraints.available_minutes
		current_time = constraints.day_start
		entries: List[ScheduleEntry] = []
		skipped: List[Task] = []

		for task in ordered:
			if task.is_completed:
				continue
			if task.duration_minutes <= remaining:
				start_time = current_time
				end_time = self._add_minutes(start_time, task.duration_minutes)
				entries.append(
					ScheduleEntry(
						task=task,
						start_time=start_time,
						end_time=end_time,
						reason=f"Selected due to {task.priority} priority and time fit.",
					)
				)
				current_time = end_time
				remaining -= task.duration_minutes
			else:
				skipped.append(task)

		for task in ordered:
			if task not in [entry.task for entry in entries] and task not in skipped and not task.is_completed:
				skipped.append(task)

		used_minutes = constraints.available_minutes - remaining
		return DailyPlan(entries=entries, used_minutes=used_minutes, skipped_tasks=skipped)

	def score_task(self, task: Task, owner: Owner, pet: Pet) -> int:
		score = self.PRIORITY_SCORE.get(task.priority.lower(), 0)
		preferred_types = owner.preferences.get("preferred_task_types", [])
		if isinstance(preferred_types, list) and task.task_type in preferred_types:
			score += 1
		if task.pet_name and task.pet_name == pet.name:
			score += 1
		return score

	def fits_constraints(self, task: Task, remaining_minutes: int) -> bool:
		return task.duration_minutes <= remaining_minutes


class PawPalController:
	def __init__(self, scheduler: Optional[SchedulerService] = None) -> None:
		self.scheduler = scheduler or SchedulerService()

	def add_task(self, task_data: Dict[str, Any]) -> Task:
		description = str(task_data.get("description", task_data.get("title", ""))).strip()
		if not description:
			raise ValueError("Task description/title is required.")

		duration_minutes = int(task_data.get("duration_minutes", task_data.get("time", 0)))
		if duration_minutes <= 0:
			raise ValueError("Task duration_minutes must be greater than 0.")

		return Task(
			description=description,
			duration_minutes=duration_minutes,
			frequency=str(task_data.get("frequency", "daily")),
			is_completed=bool(task_data.get("is_completed", False)),
			priority=str(task_data.get("priority", "medium")),
			task_type=str(task_data.get("task_type", "general")),
			pet_name=task_data.get("pet_name"),
			preferred_window=task_data.get("preferred_window"),
		)

	def build_plan(
		self,
		owner_data: Dict[str, Any],
		pet_data: Dict[str, Any],
		tasks_data: List[Dict[str, Any]],
		constraints_data: Dict[str, Any],
	) -> DailyPlan:
		owner = Owner(
			name=str(owner_data.get("name", "Owner")),
			preferences=dict(owner_data.get("preferences", {})),
		)
		pet = Pet(
			name=str(pet_data.get("name", "Pet")),
			species=str(pet_data.get("species", "other")),
			notes=str(pet_data.get("notes", "")),
		)
		owner.add_pet(pet)

		tasks: List[Task] = []
		for task_data in tasks_data:
			task = self.add_task(task_data)
			if task.pet_name is None:
				task.pet_name = pet.name
			pet.add_task(task)
			tasks.append(task)

		constraints = PlanningConstraints(
			available_minutes=int(constraints_data.get("available_minutes", 60)),
			day_start=str(constraints_data.get("day_start", "08:00")),
		)

		return self.scheduler.generate_plan(owner, pet, tasks, constraints)

