from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import json
from typing import Any, Dict, List, Optional


@dataclass
class Owner:
	name: str
	preferences: Dict[str, Any] = field(default_factory=dict)
	pets: List["Pet"] = field(default_factory=list)

	def add_pet(self, pet: "Pet") -> None:
		"""Add a pet to this owner's managed pet list."""
		self.pets.append(pet)

	def get_pet(self, pet_name: str) -> Optional["Pet"]:
		"""Return the pet with the given name, or None if not found."""
		for pet in self.pets:
			if pet.name == pet_name:
				return pet
		return None

	def get_all_tasks(self, include_completed: bool = True) -> List["Task"]:
		"""Collect tasks from all pets, optionally excluding completed tasks."""
		all_tasks: List[Task] = []
		for pet in self.pets:
			if include_completed:
				all_tasks.extend(pet.tasks)
			else:
				all_tasks.extend(pet.get_pending_tasks())
		return all_tasks

	def save_to_json(self, file_path: str = "data.json") -> None:
		"""Persist owner, pets, and tasks to JSON for cross-run restoration."""
		payload = {
			"name": self.name,
			"preferences": self.preferences,
			"pets": [
				{
					"name": pet.name,
					"species": pet.species,
					"notes": pet.notes,
					"tasks": [
						{
							"description": task.description,
							"duration_minutes": task.duration_minutes,
							"time": task.time,
							"due_date": task.due_date.isoformat() if task.due_date else None,
							"frequency": task.frequency,
							"is_completed": task.is_completed,
							"priority": task.priority,
							"task_type": task.task_type,
							"pet_name": task.pet_name,
							"preferred_window": task.preferred_window,
						}
						for task in pet.tasks
					],
				}
				for pet in self.pets
			],
		}

		with open(file_path, "w", encoding="utf-8") as handle:
			json.dump(payload, handle, ensure_ascii=True, indent=2)

	@classmethod
	def load_from_json(cls, file_path: str = "data.json") -> "Owner":
		"""Restore an Owner hierarchy from a JSON file."""
		with open(file_path, "r", encoding="utf-8") as handle:
			payload = json.load(handle)

		owner = cls(
			name=str(payload.get("name", "Owner")),
			preferences=dict(payload.get("preferences", {})),
		)

		for pet_data in payload.get("pets", []):
			pet = Pet(
				name=str(pet_data.get("name", "Pet")),
				species=str(pet_data.get("species", "other")),
				notes=str(pet_data.get("notes", "")),
			)
			for task_data in pet_data.get("tasks", []):
				raw_due_date = task_data.get("due_date")
				due_date_value = date.fromisoformat(raw_due_date) if raw_due_date else None
				task = Task(
					description=str(task_data.get("description", "")),
					duration_minutes=int(task_data.get("duration_minutes", 0)),
					time=task_data.get("time"),
					due_date=due_date_value,
					frequency=str(task_data.get("frequency", "daily")),
					is_completed=bool(task_data.get("is_completed", False)),
					priority=str(task_data.get("priority", "medium")),
					task_type=str(task_data.get("task_type", "general")),
					pet_name=task_data.get("pet_name"),
					preferred_window=task_data.get("preferred_window"),
				)
				pet.add_task(task)
			owner.add_pet(pet)

		return owner


@dataclass
class Pet:
	name: str
	species: str
	notes: str = ""
	tasks: List["Task"] = field(default_factory=list)

	def add_task(self, task: "Task") -> None:
		"""Attach a task to this pet and set task.pet_name when missing."""
		if task.pet_name is None:
			task.pet_name = self.name
		self.tasks.append(task)

	def get_pending_tasks(self) -> List["Task"]:
		"""Return only tasks that are not yet completed."""
		return [task for task in self.tasks if not task.is_completed]

	def remove_task(self, description: str) -> bool:
		"""Remove the first task matching description and report success."""
		for i, task in enumerate(self.tasks):
			if task.description == description:
				del self.tasks[i]
				return True
		return False


@dataclass
class Task:
	description: str
	duration_minutes: int
	time: Optional[str] = None
	due_date: Optional[date] = None
	frequency: str = "daily"
	is_completed: bool = False
	priority: str = "medium"
	task_type: str = "general"
	pet_name: Optional[str] = None
	preferred_window: Optional[str] = None

	@property
	def title(self) -> str:
		"""Expose description as a title-style alias for compatibility."""
		return self.description

	def mark_complete(self) -> None:
		"""Mark this task as completed."""
		self.is_completed = True

	def mark_incomplete(self) -> None:
		"""Mark this task as not completed."""
		self.is_completed = False


@dataclass
class PlanningConstraints:
	available_minutes: int
	day_start: str = "08:00"
	day_name: str = "monday"


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

	@staticmethod
	def _supports_auto_recurrence(frequency: str) -> bool:
		"""Return whether a frequency should auto-generate a follow-up task.

		Supported recurring values include daily variants and weekly variants.
		"""
		normalized = frequency.strip().lower()
		return normalized in {"daily", "everyday", "every day", "weekly"} or normalized.startswith("weekly:")

	@staticmethod
	def _recurrence_interval_days(frequency: str) -> int:
		"""Map a frequency label to its recurrence interval in whole days."""
		normalized = frequency.strip().lower()
		if normalized in {"daily", "everyday", "every day"}:
			return 1
		if normalized == "weekly" or normalized.startswith("weekly:"):
			return 7
		return 0

	def retrieve_all_tasks(
		self,
		owner: Owner,
		include_completed: bool = False,
		pet_name: Optional[str] = None,
	) -> List[Task]:
		"""Fetch all tasks across an owner's pets."""
		tasks = owner.get_all_tasks(include_completed=include_completed)
		if pet_name is None:
			return tasks
		pet_name_normalized = pet_name.strip().lower()
		return [task for task in tasks if (task.pet_name or "").strip().lower() == pet_name_normalized]

	def filter_tasks(
		self,
		tasks: List[Task],
		pet_name: Optional[str] = None,
		is_completed: Optional[bool] = None,
	) -> List[Task]:
		"""Filter tasks by pet and completion status."""
		filtered = tasks
		if pet_name is not None:
			pet_name_normalized = pet_name.strip().lower()
			filtered = [task for task in filtered if (task.pet_name or "").strip().lower() == pet_name_normalized]
		if is_completed is not None:
			filtered = [task for task in filtered if task.is_completed is is_completed]
		return filtered

	def filter_tasks_by_status_or_pet(
		self,
		tasks: List[Task],
		is_completed: Optional[bool] = None,
		pet_name: Optional[str] = None,
	) -> List[Task]:
		"""Filter tasks by completion status and/or pet name.

		Use either argument independently, or pass both to apply both filters.
		"""
		return self.filter_tasks(tasks, pet_name=pet_name, is_completed=is_completed)

	def complete_task_with_recurrence(self, pet: Pet, task: Task) -> Optional[Task]:
		"""Complete a task and optionally create the next recurring instance.

		Returns:
			A new pending Task when frequency is recurring, otherwise None.

		Notes:
			- Already completed tasks are ignored and return None.
			- The next due date is computed via timedelta from task.due_date,
			  falling back to today's date when due_date is missing.
		"""
		if task.is_completed:
			return None

		task.mark_complete()
		if not self._supports_auto_recurrence(task.frequency):
			return None

		interval_days = self._recurrence_interval_days(task.frequency)
		base_due_date = task.due_date or date.today()
		next_due_date = base_due_date + timedelta(days=interval_days)

		next_task = Task(
			description=task.description,
			duration_minutes=task.duration_minutes,
			time=task.time,
			due_date=next_due_date,
			frequency=task.frequency,
			is_completed=False,
			priority=task.priority,
			task_type=task.task_type,
			pet_name=task.pet_name or pet.name,
			preferred_window=task.preferred_window,
		)
		pet.add_task(next_task)
		return next_task

	def sort_tasks_by_time(self, tasks: List[Task], reverse: bool = False) -> List[Task]:
		"""Sort tasks by priority first, then HH:MM time, then duration/description."""
		return sorted(
			tasks,
			key=lambda task: (
				-self.PRIORITY_SCORE.get(task.priority.lower(), 0),
				0 if task.time else 1,
				tuple(map(int, task.time.split(":"))) if task.time else (99, 99),
				task.duration_minutes,
				task.description.lower(),
			),
			reverse=reverse,
		)

	def find_next_available_slot(
		self,
		tasks: List[Task],
		duration_minutes: int,
		day_start: str = "08:00",
		day_end: str = "22:00",
	) -> Optional[str]:
		"""Return next HH:MM slot that can fit duration within [day_start, day_end)."""
		day_start_minutes = SchedulerService._to_minutes(day_start)
		day_end_minutes = SchedulerService._to_minutes(day_end)
		if duration_minutes <= 0 or day_start_minutes >= day_end_minutes:
			return None

		intervals: List[tuple[int, int]] = []
		for task in tasks:
			interval = self._task_interval(task)
			if interval is None:
				continue
			start, end = interval
			if end <= day_start_minutes or start >= day_end_minutes:
				continue
			intervals.append((max(start, day_start_minutes), min(end, day_end_minutes)))

		if not intervals:
			return SchedulerService._to_time_str(day_start_minutes) if day_start_minutes + duration_minutes <= day_end_minutes else None

		intervals.sort(key=lambda item: item[0])
		merged: List[tuple[int, int]] = []
		for start, end in intervals:
			if not merged or start > merged[-1][1]:
				merged.append((start, end))
			else:
				merged[-1] = (merged[-1][0], max(merged[-1][1], end))

		cursor = day_start_minutes
		for start, end in merged:
			if cursor + duration_minutes <= start:
				return SchedulerService._to_time_str(cursor)
			cursor = max(cursor, end)

		if cursor + duration_minutes <= day_end_minutes:
			return SchedulerService._to_time_str(cursor)
		return None

	@staticmethod
	def _task_interval(task: Task) -> Optional[tuple[int, int]]:
		"""Convert a scheduled task into a [start, end) minute interval.

		Returns None when the task has no explicit HH:MM start time.
		"""
		if not task.time:
			return None
		hour_str, minute_str = task.time.split(":")
		start = int(hour_str) * 60 + int(minute_str)
		end = start + task.duration_minutes
		return start, end

	@staticmethod
	def _intervals_overlap(first: tuple[int, int], second: tuple[int, int]) -> bool:
		"""Return True when two half-open intervals [start, end) overlap."""
		start_a, end_a = first
		start_b, end_b = second
		return start_a < end_b and start_b < end_a

	def detect_task_time_conflicts(self, tasks: List[Task]) -> List[tuple[Task, Task]]:
		"""Detect overlapping task windows across same-pet and cross-pet schedules.

		Algorithm:
			1. Precompute task intervals once.
			2. Sort intervals by start time.
			3. Sweep forward and early-break when later tasks cannot overlap.

		Returns:
			A list of (task_a, task_b) pairs that overlap in time.
		"""
		interval_records: List[tuple[int, int, Task]] = []
		for task in tasks:
			interval = self._task_interval(task)
			if interval is None:
				continue
			start, end = interval
			interval_records.append((start, end, task))

		interval_records.sort(key=lambda record: record[0])

		conflicts: List[tuple[Task, Task]] = []
		for i, (start_a, end_a, task_a) in enumerate(interval_records):
			for start_b, end_b, task_b in interval_records[i + 1 :]:
				if start_b >= end_a:
					break
				if self._intervals_overlap((start_a, end_a), (start_b, end_b)):
					conflicts.append((task_a, task_b))

		return conflicts

	def get_conflict_warnings(self, tasks: List[Task]) -> List[str]:
		"""Build non-fatal, human-readable warning messages for schedule conflicts.

		This method intentionally avoids raising exceptions so callers can show
		warnings and continue planning.
		"""
		warnings: List[str] = []
		for left, right in self.detect_task_time_conflicts(tasks):
			left_pet = left.pet_name or "Unknown pet"
			right_pet = right.pet_name or "Unknown pet"
			left_time = left.time or "--:--"
			right_time = right.time or "--:--"
			warnings.append(
				f"Conflict: '{left.description}' ({left_pet}, {left_time}) overlaps with "
				f"'{right.description}' ({right_pet}, {right_time})."
			)
		return warnings

	def organize_tasks(self, tasks: List[Task], sort_by_time: bool = False) -> List[Task]:
		"""Sort tasks by priority, then duration, then description."""
		if sort_by_time:
			return self.sort_tasks_by_time(tasks)
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
		pet_name: Optional[str] = None,
		status: Optional[bool] = None,
		sort_by_time: bool = True,
	) -> List[Task]:
		"""Select the best-fitting tasks for the available daily time budget."""
		remaining = available_minutes
		selected: List[Task] = []
		tasks = self.retrieve_all_tasks(owner, include_completed=include_completed, pet_name=pet_name)
		tasks = self.filter_tasks_by_status_or_pet(tasks, is_completed=status, pet_name=pet_name)
		for task in self.organize_tasks(tasks, sort_by_time=sort_by_time):
			if task.duration_minutes <= remaining:
				selected.append(task)
				remaining -= task.duration_minutes
		return selected


class SchedulerService(Scheduler):
	WEEKDAY_LOOKUP = {
		"mon": "monday",
		"monday": "monday",
		"tue": "tuesday",
		"tues": "tuesday",
		"tuesday": "tuesday",
		"wed": "wednesday",
		"wednesday": "wednesday",
		"thu": "thursday",
		"thur": "thursday",
		"thurs": "thursday",
		"thursday": "thursday",
		"fri": "friday",
		"friday": "friday",
		"sat": "saturday",
		"saturday": "saturday",
		"sun": "sunday",
		"sunday": "sunday",
	}

	@staticmethod
	def _add_minutes(time_str: str, minutes: int) -> str:
		"""Return HH:MM after adding minutes to a starting HH:MM time."""
		hour_str, minute_str = time_str.split(":")
		total_minutes = int(hour_str) * 60 + int(minute_str) + minutes
		total_minutes %= 24 * 60
		hour = total_minutes // 60
		minute = total_minutes % 60
		return f"{hour:02d}:{minute:02d}"

	@staticmethod
	def _to_minutes(time_str: str) -> int:
		"""Convert HH:MM to minutes since midnight."""
		hour_str, minute_str = time_str.split(":")
		return int(hour_str) * 60 + int(minute_str)

	@staticmethod
	def _to_time_str(total_minutes: int) -> str:
		"""Convert minutes since midnight to HH:MM."""
		total_minutes %= 24 * 60
		hour = total_minutes // 60
		minute = total_minutes % 60
		return f"{hour:02d}:{minute:02d}"

	def _normalize_day_name(self, day_name: str) -> str:
		"""Normalize day labels like Mon/monday to canonical lowercase names."""
		return self.WEEKDAY_LOOKUP.get(day_name.strip().lower(), day_name.strip().lower())

	def is_task_due_on_day(self, task: Task, day_name: str) -> bool:
		"""Evaluate simple recurring frequencies against a target weekday."""
		frequency = task.frequency.strip().lower()
		normalized_day = self._normalize_day_name(day_name)

		if frequency in {"", "daily", "everyday", "every day"}:
			return True
		if frequency == "once":
			return not task.is_completed
		if frequency in self.WEEKDAY_LOOKUP:
			return self._normalize_day_name(frequency) == normalized_day
		if frequency.startswith("weekly:"):
			days = [self._normalize_day_name(part) for part in frequency.split(":", 1)[1].split(",") if part.strip()]
			return normalized_day in days
		if frequency == "weekly":
			# Basic convention for weekly tasks: schedule on Monday unless a specific day is provided.
			return normalized_day == "monday"
		return True

	@staticmethod
	def _parse_preferred_window(window: str) -> Optional[tuple[int, int]]:
		"""Parse preferred window strings in HH:MM-HH:MM format."""
		if "-" not in window:
			return None
		start_raw, end_raw = window.split("-", 1)
		start = SchedulerService._to_minutes(start_raw.strip())
		end = SchedulerService._to_minutes(end_raw.strip())
		if end < start:
			return None
		return start, end

	@staticmethod
	def _overlaps(start_a: int, end_a: int, start_b: int, end_b: int) -> bool:
		"""Return True when intervals [start, end) overlap."""
		return start_a < end_b and start_b < end_a

	def detect_conflict(self, proposed_start: int, proposed_end: int, entries: List[ScheduleEntry]) -> bool:
		"""Check if a proposed interval conflicts with any existing schedule entry."""
		for entry in entries:
			entry_start = self._to_minutes(entry.start_time)
			entry_end = self._to_minutes(entry.end_time)
			if self._overlaps(proposed_start, proposed_end, entry_start, entry_end):
				return True
		return False

	def generate_plan(
		self,
		owner: Owner,
		pet: Pet,
		tasks: List[Task],
		constraints: PlanningConstraints,
	) -> DailyPlan:
		"""Build a time-ordered daily plan from candidate tasks and constraints."""
		candidate_tasks = tasks if tasks else pet.get_pending_tasks()
		due_tasks = [
			task
			for task in candidate_tasks
			if not task.is_completed
			and self.is_task_due_on_day(task, constraints.day_name)
			and self.fits_constraints(task, constraints.available_minutes)
		]
		ordered = self.organize_tasks(due_tasks, sort_by_time=True)

		remaining = constraints.available_minutes
		current_time_minutes = self._to_minutes(constraints.day_start)
		entries: List[ScheduleEntry] = []
		skipped: List[Task] = []
		selected_tasks: set[int] = set()

		for task in ordered:
			start_minutes = current_time_minutes
			if task.preferred_window:
				window = self._parse_preferred_window(task.preferred_window)
				if window is None:
					skipped.append(task)
					continue
				window_start, window_end = window
				if start_minutes < window_start:
					start_minutes = window_start
				if start_minutes + task.duration_minutes > window_end:
					skipped.append(task)
					continue

			end_minutes = start_minutes + task.duration_minutes
			if task.duration_minutes <= remaining:
				if self.detect_conflict(start_minutes, end_minutes, entries):
					skipped.append(task)
					continue
				start_time = self._to_time_str(start_minutes)
				end_time = self._to_time_str(end_minutes)
				entries.append(
					ScheduleEntry(
						task=task,
						start_time=start_time,
						end_time=end_time,
						reason=f"Selected due to {task.priority} priority and time fit.",
					)
				)
				selected_tasks.add(id(task))
				current_time_minutes = end_minutes
				remaining -= task.duration_minutes
			else:
				skipped.append(task)

		for task in ordered:
			if id(task) not in selected_tasks and task not in skipped:
				skipped.append(task)

		used_minutes = constraints.available_minutes - remaining
		return DailyPlan(entries=entries, used_minutes=used_minutes, skipped_tasks=skipped)

	def score_task(self, task: Task, owner: Owner, pet: Pet) -> int:
		"""Compute a numeric task score from priority and owner/pet relevance."""
		score = self.PRIORITY_SCORE.get(task.priority.lower(), 0)
		preferred_types = owner.preferences.get("preferred_task_types", [])
		if isinstance(preferred_types, list) and task.task_type in preferred_types:
			score += 1
		if task.pet_name and task.pet_name == pet.name:
			score += 1
		return score

	def fits_constraints(self, task: Task, remaining_minutes: int) -> bool:
		"""Check whether a task fits in the remaining minute budget."""
		return task.duration_minutes <= remaining_minutes


class PawPalController:
	def __init__(self, scheduler: Optional[SchedulerService] = None) -> None:
		"""Initialize controller with an injectable scheduler service."""
		self.scheduler = scheduler or SchedulerService()

	def add_task(self, task_data: Dict[str, Any]) -> Task:
		"""Validate input task data and convert it into a Task object."""
		description = str(task_data.get("description", task_data.get("title", ""))).strip()
		if not description:
			raise ValueError("Task description/title is required.")

		duration_minutes = int(task_data.get("duration_minutes", task_data.get("time", 0)))
		if duration_minutes <= 0:
			raise ValueError("Task duration_minutes must be greater than 0.")

		return Task(
			description=description,
			duration_minutes=duration_minutes,
			time=task_data.get("time"),
			due_date=self._parse_due_date(task_data.get("due_date")),
			frequency=str(task_data.get("frequency", "daily")),
			is_completed=bool(task_data.get("is_completed", False)),
			priority=str(task_data.get("priority", "medium")),
			task_type=str(task_data.get("task_type", "general")),
			pet_name=task_data.get("pet_name"),
			preferred_window=task_data.get("preferred_window"),
		)

	@staticmethod
	def _parse_due_date(raw_due_date: Any) -> Optional[date]:
		"""Parse due_date values from date objects or YYYY-MM-DD strings."""
		if raw_due_date is None:
			return None
		if isinstance(raw_due_date, date):
			return raw_due_date
		if isinstance(raw_due_date, str):
			cleaned = raw_due_date.strip()
			if not cleaned:
				return None
			try:
				return datetime.strptime(cleaned, "%Y-%m-%d").date()
			except ValueError as exc:
				raise ValueError("Task due_date must be in YYYY-MM-DD format.") from exc
		raise ValueError("Task due_date must be a date or YYYY-MM-DD string.")

	def build_plan(
		self,
		owner_data: Dict[str, Any],
		pet_data: Dict[str, Any],
		tasks_data: List[Dict[str, Any]],
		constraints_data: Dict[str, Any],
	) -> DailyPlan:
		"""Construct domain objects from input payloads and generate a daily plan."""
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
			day_name=str(constraints_data.get("day_name", "monday")),
		)

		return self.scheduler.generate_plan(owner, pet, tasks, constraints)

