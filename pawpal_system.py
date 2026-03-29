from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Owner:
	name: str
	preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Pet:
	name: str
	species: str
	notes: str = ""


@dataclass
class Task:
	title: str
	task_type: str
	duration_minutes: int
	priority: str
	pet_name: Optional[str] = None
	preferred_window: Optional[str] = None


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


class SchedulerService:
	def generate_plan(
		self,
		owner: Owner,
		pet: Pet,
		tasks: List[Task],
		constraints: PlanningConstraints,
	) -> DailyPlan:
		raise NotImplementedError("Implement scheduling logic in generate_plan")

	def score_task(self, task: Task, owner: Owner, pet: Pet) -> int:
		raise NotImplementedError("Implement task scoring in score_task")

	def fits_constraints(self, task: Task, remaining_minutes: int) -> bool:
		raise NotImplementedError("Implement constraint checks in fits_constraints")


class PawPalController:
	def __init__(self, scheduler: Optional[SchedulerService] = None) -> None:
		self.scheduler = scheduler or SchedulerService()

	def add_task(self, task_data: Dict[str, Any]) -> Task:
		raise NotImplementedError("Implement task creation/validation in add_task")

	def build_plan(
		self,
		owner_data: Dict[str, Any],
		pet_data: Dict[str, Any],
		tasks_data: List[Dict[str, Any]],
		constraints_data: Dict[str, Any],
	) -> DailyPlan:
		raise NotImplementedError("Implement orchestration in build_plan")

