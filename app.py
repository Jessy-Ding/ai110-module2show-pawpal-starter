import re
from pathlib import Path

import pandas as pd
import streamlit as st
from pawpal_system import Owner, PawPalController, Pet

DATA_FILE = Path("data.json")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

st.markdown(
    """
<style>
    :root {
        --bg-soft: #f5f7f4;
        --card: #ffffff;
        --ink: #1f2937;
        --accent: #0f766e;
        --accent-soft: #e6fffa;
        --line: #d1d5db;
    }
    .stApp {
        background: linear-gradient(180deg, var(--bg-soft) 0%, #ffffff 45%);
    }
    .hero {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 4px rgba(17, 24, 39, 0.06);
    }
    .hero h1 {
        margin: 0;
        color: var(--ink);
        letter-spacing: 0.2px;
    }
    .hero p {
        margin: 0.4rem 0 0 0;
        color: #4b5563;
    }
    .section-title {
        color: var(--ink);
        font-weight: 700;
        margin-top: 0.5rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


def is_valid_time(value: str) -> bool:
    """Validate HH:MM time strings (24-hour clock)."""
    return bool(re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", value))


def is_valid_window(value: str) -> bool:
    """Validate HH:MM-HH:MM windows with start <= end."""
    parts = value.split("-", 1)
    if len(parts) != 2:
        return False
    start, end = parts[0].strip(), parts[1].strip()
    if not is_valid_time(start) or not is_valid_time(end):
        return False
    return start <= end


def _priority_style(priority_value: str) -> str:
    """Return CSS style for priority color-coding."""
    palette = {
        "high": ("#fee2e2", "#991b1b"),
        "medium": ("#fef3c7", "#92400e"),
        "low": ("#dcfce7", "#166534"),
    }
    normalized = str(priority_value).lower()
    for key in ("high", "medium", "low"):
        if key in normalized:
            background, foreground = palette[key]
            return f"background-color: {background}; color: {foreground}; font-weight: 700;"
    background, foreground = ("#e5e7eb", "#111827")
    return f"background-color: {background}; color: {foreground}; font-weight: 700;"


def _completed_row_style(row: pd.Series) -> list[str]:
    """Gray out completed rows using Done/Completed flags when present."""
    completed_flag = False
    if "Done" in row.index:
        completed_flag = bool(row["Done"])
    elif "Completed" in row.index:
        completed_flag = bool(row["Completed"])

    if completed_flag:
        return ["background-color: #f3f4f6; color: #6b7280;"] * len(row)
    return [""] * len(row)


def render_priority_table(rows: list[dict]) -> None:
    """Render dataframe with priority-highlighted cells when Priority column exists."""
    if not rows:
        st.info("No data to display.")
        return

    df = pd.DataFrame(rows)
    styler = df.style.apply(_completed_row_style, axis=1)

    if "Priority" in df.columns:
        styler = styler.map(_priority_style, subset=["Priority"])
        st.dataframe(styler, use_container_width=True, hide_index=True)
        return
    st.dataframe(styler, use_container_width=True, hide_index=True)


def priority_badge(priority: str) -> str:
    """Return emoji-enhanced priority label."""
    normalized = (priority or "").strip().lower()
    if normalized == "high":
        return "🔴 high"
    if normalized == "medium":
        return "🟡 medium"
    if normalized == "low":
        return "🟢 low"
    return priority


def status_badge(is_completed: bool) -> str:
    """Return emoji-enhanced completion status."""
    return "✅ done" if is_completed else "⏳ pending"


if "owner" not in st.session_state:
    if DATA_FILE.exists():
        try:
            st.session_state.owner = Owner.load_from_json(str(DATA_FILE))
        except (ValueError, OSError, TypeError, KeyError, IndexError):
            st.session_state.owner = Owner(name="Jordan")
            st.warning("Detected invalid saved data. Started with a clean session.")
    else:
        st.session_state.owner = Owner(name="Jordan")
if "controller" not in st.session_state:
    st.session_state.controller = PawPalController()

owner: Owner = st.session_state.owner
controller: PawPalController = st.session_state.controller

st.markdown(
    """
<div class="hero">
    <h1>🐾 PawPal+ Care Planner</h1>
    <p>Plan pet care tasks with smart sorting, recurrence handling, and conflict-aware scheduling.</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Owner Profile")
    owner_name = st.text_input("Owner name", value=owner.name)
    updated_owner_name = owner_name.strip() or owner.name
    if updated_owner_name != owner.name:
        owner.name = updated_owner_name
        owner.save_to_json(str(DATA_FILE))

    st.markdown("### Add Pet")
    with st.form("add_pet_form", clear_on_submit=True):
        new_pet_name = st.text_input("Pet name")
        new_species = st.selectbox("Species", ["dog", "cat", "other"])
        add_pet_submitted = st.form_submit_button("Add pet")

    if add_pet_submitted:
        cleaned_name = new_pet_name.strip()
        if not cleaned_name:
            st.error("Pet name is required.")
        elif owner.get_pet(cleaned_name):
            st.warning(f"Pet '{cleaned_name}' already exists.")
        else:
            owner.add_pet(Pet(name=cleaned_name, species=new_species))
            owner.save_to_json(str(DATA_FILE))
            st.success(f"Added pet '{cleaned_name}'.")

    st.markdown("### Session Snapshot")
    st.caption(f"Owner: {owner.name}")
    st.caption(f"Pets tracked: {len(owner.pets)}")

if not owner.pets:
    st.info("No pets yet. Add your first pet from the sidebar to start planning.")
    st.stop()

all_tasks = controller.scheduler.retrieve_all_tasks(owner, include_completed=True)
all_conflicts = controller.scheduler.detect_task_time_conflicts(all_tasks)
total_minutes = sum(task.duration_minutes for task in all_tasks)

top_col1, top_col2, top_col3, top_col4 = st.columns(4)
top_col1.metric("Pets", len(owner.pets))
top_col2.metric("Tasks", len(all_tasks))
top_col3.metric("Total Task Minutes", total_minutes)
top_col4.metric("Conflicts", len(all_conflicts))

tab_tasks, tab_planner, tab_overview = st.tabs(["Task Console", "Daily Planner", "Overview"])

with tab_tasks:
    st.markdown("<div class='section-title'>Manage Tasks</div>", unsafe_allow_html=True)

    pet_names = [pet.name for pet in owner.pets]
    selected_pet_name = st.selectbox("Pet", pet_names, key="task_pet_selector")
    selected_pet = owner.get_pet(selected_pet_name)

    add_col1, add_col2 = st.columns([1.4, 1])

    with add_col1:
        with st.form("add_task_form", clear_on_submit=True):
            task_description = st.text_input("Task description", value="Morning walk")
            col_a, col_b, col_c = st.columns(3)
            duration = col_a.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            task_time = col_b.text_input("Start time (HH:MM)", value="")
            priority = col_c.selectbox("Priority", ["high", "medium", "low"], index=0)
            col_d, col_e = st.columns(2)
            task_frequency = col_d.text_input("Frequency", value="daily")
            task_type = col_e.text_input("Task type", value="general")
            preferred_window = st.text_input("Preferred window (optional HH:MM-HH:MM)", value="")
            add_task_submitted = st.form_submit_button("Add task")

        if add_task_submitted and selected_pet is not None:
            cleaned_time = task_time.strip()
            cleaned_window = preferred_window.strip()
            if cleaned_time and not is_valid_time(cleaned_time):
                st.error("Start time must be in HH:MM format (example: 08:30).")
            elif cleaned_window and not is_valid_window(cleaned_window):
                st.error("Preferred window must be HH:MM-HH:MM with valid 24-hour times.")
            else:
                try:
                    task = controller.add_task(
                        {
                            "description": task_description,
                            "duration_minutes": int(duration),
                            "time": cleaned_time or None,
                            "priority": priority,
                            "frequency": task_frequency,
                            "task_type": task_type,
                            "pet_name": selected_pet.name,
                            "preferred_window": cleaned_window or None,
                        }
                    )
                    selected_pet.add_task(task)
                    owner.save_to_json(str(DATA_FILE))
                    st.success(f"Added '{task.description}' to {selected_pet.name}.")
                except ValueError as exc:
                    st.error(str(exc))

    with add_col2:
        status_filter_label = st.selectbox(
            "Status filter",
            ["All", "Pending only", "Completed only"],
            key="task_status_filter",
        )
        status_filter_map = {
            "All": None,
            "Pending only": False,
            "Completed only": True,
        }

        filtered_pet_tasks = controller.scheduler.filter_tasks_by_status_or_pet(
            selected_pet.tasks if selected_pet else [],
            is_completed=status_filter_map[status_filter_label],
            pet_name=selected_pet.name if selected_pet else None,
        )
        sorted_pet_tasks = controller.scheduler.sort_tasks_by_time(filtered_pet_tasks)
        pet_conflicts = controller.scheduler.detect_task_time_conflicts(sorted_pet_tasks)

        st.metric("Visible tasks", len(sorted_pet_tasks))
        st.metric("Visible minutes", sum(task.duration_minutes for task in sorted_pet_tasks))
        st.metric("Conflicts", len(pet_conflicts))

        pending_tasks = [task for task in selected_pet.tasks if not task.is_completed] if selected_pet else []
        if pending_tasks:
            pending_options = [
                f"{idx + 1}. {(task.time or '--:--')} | {task.description}" for idx, task in enumerate(pending_tasks)
            ]
            selected_pending_label = st.selectbox("Mark complete", pending_options, key="mark_complete_selector")
            if st.button("Mark complete", key="mark_complete_button"):
                selected_index = int(selected_pending_label.split(".", 1)[0]) - 1
                task_to_complete = pending_tasks[selected_index]
                next_task = controller.scheduler.complete_task_with_recurrence(selected_pet, task_to_complete)
                if next_task is None:
                    st.success(f"Completed '{task_to_complete.description}'.")
                else:
                    next_due = next_task.due_date.isoformat() if next_task.due_date else "N/A"
                    st.success(
                        f"Completed '{task_to_complete.description}'. "
                        f"Created next recurring task due on {next_due}."
                    )
                owner.save_to_json(str(DATA_FILE))
                st.rerun()

        editable_tasks = selected_pet.tasks if selected_pet else []
        if editable_tasks:
            edit_options = [
                f"{idx + 1}. {(task.time or '--:--')} | {task.description}" for idx, task in enumerate(editable_tasks)
            ]
            selected_edit_label = st.selectbox("Edit task", edit_options, key="edit_task_selector")
            edit_index = int(selected_edit_label.split(".", 1)[0]) - 1
            task_to_edit = editable_tasks[edit_index]

            with st.form("edit_task_form"):
                edit_description = st.text_input("Description", value=task_to_edit.description)
                edit_duration = st.number_input(
                    "Duration (minutes)",
                    min_value=1,
                    max_value=240,
                    value=int(task_to_edit.duration_minutes),
                    key="edit_duration",
                )
                edit_time = st.text_input("Start time (HH:MM)", value=task_to_edit.time or "", key="edit_time")
                edit_priority = st.selectbox(
                    "Priority",
                    ["high", "medium", "low"],
                    index=["high", "medium", "low"].index(task_to_edit.priority.lower())
                    if task_to_edit.priority.lower() in {"high", "medium", "low"}
                    else 1,
                    key="edit_priority",
                )
                edit_frequency = st.text_input("Frequency", value=task_to_edit.frequency, key="edit_frequency")
                edit_task_type = st.text_input("Task type", value=task_to_edit.task_type, key="edit_task_type")
                edit_window = st.text_input(
                    "Preferred window (HH:MM-HH:MM)",
                    value=task_to_edit.preferred_window or "",
                    key="edit_window",
                )
                edit_done = st.checkbox("Completed", value=task_to_edit.is_completed, key="edit_done")

                save_col, delete_col = st.columns(2)
                save_clicked = save_col.form_submit_button("Save changes")
                delete_clicked = delete_col.form_submit_button("Delete task")

            if save_clicked:
                cleaned_edit_time = edit_time.strip()
                cleaned_edit_window = edit_window.strip()

                if not edit_description.strip():
                    st.error("Description cannot be empty.")
                elif cleaned_edit_time and not is_valid_time(cleaned_edit_time):
                    st.error("Start time must be in HH:MM format (example: 08:30).")
                elif cleaned_edit_window and not is_valid_window(cleaned_edit_window):
                    st.error("Preferred window must be HH:MM-HH:MM with valid 24-hour times.")
                else:
                    task_to_edit.description = edit_description.strip()
                    task_to_edit.duration_minutes = int(edit_duration)
                    task_to_edit.time = cleaned_edit_time or None
                    task_to_edit.priority = edit_priority
                    task_to_edit.frequency = edit_frequency.strip() or "daily"
                    task_to_edit.task_type = edit_task_type.strip() or "general"
                    task_to_edit.preferred_window = cleaned_edit_window or None
                    task_to_edit.is_completed = edit_done
                    owner.save_to_json(str(DATA_FILE))
                    st.success("Task updated.")
                    st.rerun()

            if delete_clicked:
                deleted_task = editable_tasks.pop(edit_index)
                owner.save_to_json(str(DATA_FILE))
                st.success(f"Deleted '{deleted_task.description}'.")
                st.rerun()

    if selected_pet and sorted_pet_tasks:
        if pet_conflicts:
            st.warning(
                f"{len(pet_conflicts)} scheduling conflict(s) found. Planning still works, but some tasks overlap."
            )
            st.caption("Tip: change one start time or move a lower-priority task to a later slot.")
            st.table(
                [
                    {
                        "Task A": left.description,
                        "Time A": left.time or "--:--",
                        "Task B": right.description,
                        "Time B": right.time or "--:--",
                    }
                    for left, right in pet_conflicts
                ]
            )

        render_priority_table(
            [
                {
                    "Pet": task.pet_name,
                    "Task": task.description,
                    "Time": task.time or "--:--",
                    "Duration": task.duration_minutes,
                    "Priority": priority_badge(task.priority),
                    "Frequency": task.frequency,
                    "Done": task.is_completed,
                    "Status": status_badge(task.is_completed),
                }
                for task in sorted_pet_tasks
            ]
        )
    else:
        st.info("No tasks available for this pet under the selected filter.")

with tab_planner:
    st.markdown("<div class='section-title'>Generate Daily Plan</div>", unsafe_allow_html=True)

    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    available_minutes = p_col1.number_input("Available minutes", min_value=1, max_value=24 * 60, value=90)
    include_completed = p_col2.checkbox("Include completed", value=False)
    plan_scope = p_col3.selectbox("Plan scope", ["All pets"] + [pet.name for pet in owner.pets])
    status_scope = p_col4.selectbox("Status", ["All", "Pending only", "Completed only"])

    status_scope_map = {"All": None, "Pending only": False, "Completed only": True}
    selected_scope_pet = None if plan_scope == "All pets" else plan_scope

    slot_col1, slot_col2, slot_col3 = st.columns([1, 1, 1.4])
    slot_duration = slot_col1.number_input("Find slot for (min)", min_value=5, max_value=240, value=30)
    slot_start = slot_col2.text_input("Window start", value="08:00")
    slot_end = slot_col3.text_input("Window end", value="22:00")

    slot_source_tasks = controller.scheduler.retrieve_all_tasks(
        owner,
        include_completed=include_completed,
        pet_name=selected_scope_pet,
    )

    if st.button("Suggest Next Available Slot"):
        if not is_valid_time(slot_start) or not is_valid_time(slot_end):
            st.error("Window start/end must be valid HH:MM values.")
        else:
            next_slot = controller.scheduler.find_next_available_slot(
                tasks=slot_source_tasks,
                duration_minutes=int(slot_duration),
                day_start=slot_start,
                day_end=slot_end,
            )
            if next_slot is None:
                st.warning("No available slot found in the selected time window.")
            else:
                st.success(f"Next available {int(slot_duration)}-minute slot: {next_slot}")

    if st.button("Build Today's Plan", type="primary"):
        planned_tasks = controller.scheduler.plan_tasks_for_day(
            owner,
            available_minutes=int(available_minutes),
            include_completed=include_completed,
            pet_name=selected_scope_pet,
            status=status_scope_map[status_scope],
            sort_by_time=True,
        )

        if not planned_tasks:
            st.info("No tasks fit the selected planning constraints.")
        else:
            sorted_planned_tasks = controller.scheduler.sort_tasks_by_time(planned_tasks)
            planned_conflicts = controller.scheduler.detect_task_time_conflicts(sorted_planned_tasks)
            used_minutes = sum(task.duration_minutes for task in sorted_planned_tasks)
            remaining = int(available_minutes) - used_minutes

            st.success(
                f"Planned {len(sorted_planned_tasks)} task(s). "
                f"Used {used_minutes} min, Remaining {remaining} min."
            )

            if planned_conflicts:
                st.warning(
                    f"{len(planned_conflicts)} overlap warning(s) in today's plan. "
                    "Planning still completed successfully."
                )
                st.caption("Tip: adjust start times or move lower-priority tasks to avoid overlap.")
                st.table(
                    [
                        {
                            "Task A": left.description,
                            "Pet A": left.pet_name or "Unknown",
                            "Time A": left.time or "--:--",
                            "Task B": right.description,
                            "Pet B": right.pet_name or "Unknown",
                            "Time B": right.time or "--:--",
                        }
                        for left, right in planned_conflicts
                    ]
                )

            render_priority_table(
                [
                    {
                        "Pet": task.pet_name,
                        "Task": task.description,
                        "Time": task.time or "--:--",
                        "Duration": task.duration_minutes,
                        "Priority": priority_badge(task.priority),
                    }
                    for task in sorted_planned_tasks
                ]
            )

with tab_overview:
    st.markdown("<div class='section-title'>System Overview</div>", unsafe_allow_html=True)

    st.table([{"Pet": pet.name, "Species": pet.species, "Task count": len(pet.tasks)} for pet in owner.pets])

    if all_tasks:
        sorted_all_tasks = controller.scheduler.sort_tasks_by_time(all_tasks)
        render_priority_table(
            [
                {
                    "Pet": task.pet_name,
                    "Task": task.description,
                    "Time": task.time or "--:--",
                    "Duration": task.duration_minutes,
                    "Priority": priority_badge(task.priority),
                    "Completed": task.is_completed,
                    "Status": status_badge(task.is_completed),
                }
                for task in sorted_all_tasks
            ]
        )
    else:
        st.info("No tasks in the system yet.")
