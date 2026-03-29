import streamlit as st
from pawpal_system import Owner, PawPalController, Pet, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")

# Persist domain objects across reruns using session_state.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name)
if "controller" not in st.session_state:
    st.session_state.controller = PawPalController()

owner: Owner = st.session_state.owner
controller: PawPalController = st.session_state.controller
owner.name = owner_name

st.caption(f"Session owner: {owner.name} | Pets in memory: {len(owner.pets)}")

st.markdown("### Add a Pet")
with st.form("add_pet_form"):
    new_pet_name = st.text_input("Pet name")
    new_species = st.selectbox("Species", ["dog", "cat", "other"], key="add_pet_species")
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted:
    cleaned_name = new_pet_name.strip()
    if not cleaned_name:
        st.error("Pet name is required.")
    elif owner.get_pet(cleaned_name):
        st.warning(f"Pet '{cleaned_name}' already exists.")
    else:
        owner.add_pet(Pet(name=cleaned_name, species=new_species))
        st.success(f"Added pet '{cleaned_name}'.")

if owner.pets:
    st.write("Pets:")
    st.table([{"name": pet.name, "species": pet.species} for pet in owner.pets])
else:
    st.info("No pets added yet.")

st.markdown("### Tasks")
st.caption("Schedule tasks by creating real Task objects through your controller.")

if owner.pets:
    pet_names = [pet.name for pet in owner.pets]
    selected_pet_name = st.selectbox("Choose pet for task", pet_names)
    selected_pet = owner.get_pet(selected_pet_name)

    with st.form("add_task_form"):
        task_description = st.text_input("Task description", value="Morning walk")
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        task_time = st.text_input("Start time (optional HH:MM)", value="")
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        task_frequency = st.text_input("Frequency", value="daily")
        task_type = st.text_input("Task type", value="general")
        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted and selected_pet is not None:
        try:
            task = controller.add_task(
                {
                    "description": task_description,
                    "duration_minutes": int(duration),
                    "time": task_time.strip() or None,
                    "priority": priority,
                    "frequency": task_frequency,
                    "task_type": task_type,
                    "pet_name": selected_pet.name,
                }
            )
            selected_pet.add_task(task)
            st.success(f"Added task to {selected_pet.name}.")
        except ValueError as exc:
            st.error(str(exc))

    if selected_pet is not None and selected_pet.tasks:
        status_filter_label = st.selectbox(
            "Filter tasks by status",
            ["All", "Pending only", "Completed only"],
            key="task_status_filter",
        )
        status_filter_map = {
            "All": None,
            "Pending only": False,
            "Completed only": True,
        }
        filtered_pet_tasks = controller.scheduler.filter_tasks_by_status_or_pet(
            selected_pet.tasks,
            is_completed=status_filter_map[status_filter_label],
            pet_name=selected_pet.name,
        )
        sorted_pet_tasks = controller.scheduler.sort_tasks_by_time(filtered_pet_tasks)

        pet_conflicts = controller.scheduler.detect_task_time_conflicts(sorted_pet_tasks)
        pet_conflict_warnings = controller.scheduler.get_conflict_warnings(sorted_pet_tasks)

        total_task_minutes = sum(task.duration_minutes for task in sorted_pet_tasks)
        st.success(
            f"Showing {len(sorted_pet_tasks)} task(s) for {selected_pet.name} "
            f"({total_task_minutes} total minutes)."
        )

        if pet_conflict_warnings:
            st.warning(
                f"{len(pet_conflict_warnings)} scheduling conflict(s) found. "
                "Planning still works, but this schedule has overlaps."
            )
            st.caption("Tip: change one start time or move a lower-priority task to a later slot.")
            st.table(
                [
                    {
                        "task_a": left.description,
                        "pet_a": left.pet_name or "Unknown",
                        "time_a": left.time or "--:--",
                        "task_b": right.description,
                        "pet_b": right.pet_name or "Unknown",
                        "time_b": right.time or "--:--",
                    }
                    for left, right in pet_conflicts
                ]
            )

        st.write(f"Tasks for {selected_pet.name} (sorted by time):")
        st.table(
            [
                {
                    "description": task.description,
                    "time": task.time or "--:--",
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "frequency": task.frequency,
                    "is_completed": task.is_completed,
                }
                for task in sorted_pet_tasks
            ]
        )
    else:
        st.info("No tasks yet for this pet.")
else:
    st.info("Add a pet first, then you can add tasks.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate today's task list from the scheduler using pets/tasks in memory.")

available_minutes = st.number_input(
    "Available minutes today",
    min_value=1,
    max_value=24 * 60,
    value=60,
)
include_completed = st.checkbox("Include completed tasks", value=False)

if st.button("Generate schedule"):
    if not owner.pets:
        st.warning("Please add at least one pet before generating a schedule.")
    else:
        today_tasks = controller.scheduler.plan_tasks_for_day(
            owner,
            available_minutes=int(available_minutes),
            include_completed=include_completed,
        )
        if not today_tasks:
            st.info("No tasks fit within the available time.")
        else:
            sorted_today_tasks = controller.scheduler.sort_tasks_by_time(today_tasks)
            today_conflicts = controller.scheduler.detect_task_time_conflicts(sorted_today_tasks)
            today_conflict_warnings = controller.scheduler.get_conflict_warnings(sorted_today_tasks)

            planned_minutes = sum(task.duration_minutes for task in sorted_today_tasks)
            remaining_minutes = int(available_minutes) - planned_minutes
            st.success(
                f"Planned {len(sorted_today_tasks)} task(s), {planned_minutes} minutes used, "
                f"{remaining_minutes} minutes remaining."
            )

            if today_conflict_warnings:
                st.warning(
                    f"{len(today_conflict_warnings)} overlap warning(s) in today's plan. "
                    "Planning still worked, but some tasks overlap."
                )
                st.caption("Tip: change one start time or move a lower-priority task to a later slot.")
                st.table(
                    [
                        {
                            "task_a": left.description,
                            "pet_a": left.pet_name or "Unknown",
                            "time_a": left.time or "--:--",
                            "task_b": right.description,
                            "pet_b": right.pet_name or "Unknown",
                            "time_b": right.time or "--:--",
                        }
                        for left, right in today_conflicts
                    ]
                )

            st.write("Today's Schedule:")
            st.table(
                [
                    {
                        "pet": task.pet_name,
                        "time": task.time or "--:--",
                        "task": task.description,
                        "duration_minutes": task.duration_minutes,
                        "priority": task.priority,
                    }
                    for task in sorted_today_tasks
                ]
            )
