from nicegui import ui
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import os
import sys

# Assuming backend models are in a separate module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from models import RequirementPayload, JobRequest

class JobList:
    def __init__(self, jobs: List[JobRequest]):
        self.jobs_map = {j['job_id']: j for j in jobs}
        self.jobs_list = []
        for job in self.jobs_map.values():
            job_copy = job.copy()
            job_copy['musthave'] = [req for req in job['requirements'] if req['ismusthave']]
            job_copy['desirable'] = [req for req in job['requirements'] if not req['ismusthave']]
            # Calculate days left until due_date
            if job_copy.get('due_date'):
                days_left = (job_copy['due_date'] - date.today()).days
                job_copy['days_left'] = f"{days_left}d" if days_left >= 0 else f"{-days_left}d"
            else:
                job_copy['days_left'] = "None"
            self.jobs_list.append(job_copy)

        # Define preferred column order
        self.preferred_column_order = [
            'job_id', 'customer', 'title', 'description', 'contact_person', 'start_date', 'duration',
            'due_date', 'days_left', 'candidates', 'highest_candidate_status',
            'assigned_to', 'state', 'musthave', 'desirable', 'actions'
        ]

        # Define all possible columns
        excluded_fields = ["requirements", "created_at"]
        ordered_fields = [f for f in JobRequest.__fields__ if f not in excluded_fields]
        ordered_fields.append("days_left")
        self.all_columns = [
            {
                "name": field,
                "label": field.replace("_", " ").capitalize() if field != "days_left" else "Days Left",
                "field": field,
                "sortable": field not in ["musthave", "desirable", "actions"],
                "style": "max-width: 250px; white-space: normal; word-wrap: break-word;" if field in ["musthave", "desirable"] else "max-width: 200px; white-space: normal; word-wrap: break-word;",
                "align": "left"
            }
            for field in ordered_fields
        ]
        self.all_columns.append({
            "name": "actions",
            "label": "",
            "field": "actions",
            "sortable": False,
            "align": "left"
        })

        # Sort columns by preferred order
        self.all_columns = sorted(
            self.all_columns,
            key=lambda col: self.preferred_column_order.index(col['name']) if col['name'] in self.preferred_column_order else len(self.preferred_column_order)
        )

        # Initialize with no columns hidden (empty selected_columns)
        self.selected_columns = []  # Columns to hide
        self.columns = self.all_columns  # Start with all columns in preferred order

        self._build_ui()

    def _build_ui(self):
        with ui.row().classes('items-center p-2').style('width: auto'):
            ui.label('Job List').style('width: 150px').classes('text-xl font-bold')
            search_input = ui.input(label='Search').props('clearable').style('margin-left: 20px; width: 250px')
            # Column selector with options in preferred order
            ui.select(
                [col['name'] for col in self.all_columns],
                multiple=True,
                label='Hide Columns',
                value=self.selected_columns,  # Start with no columns hidden
                on_change=self._update_columns
            ).style('margin-left: 20px; width: 250px')

        self.table = ui.table(
            columns=self.columns,
            rows=self.jobs_list,
            row_key="job_id",
            pagination={'sortBy': 'created_at', 'descending': True}
        ).classes("w-full max-w-[1800px]")
        self.table.bind_filter_from(search_input, 'value')

        with self.table:
            self.table.add_slot(
                "body-cell-musthave",
                r'''
                <q-td :props="props">
                    <div class="text-sm" style="text-align: left; line-height: 1.2;">
                        <div v-for="req in props.row.musthave" :key="req.reqname">
                            {{ req.reqname }}
                        </div>
                        <div v-if="!props.row.musthave.length">None</div>
                    </div>
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-desirable",
                r'''
                <q-td :props="props">
                    <div class="text-sm" style="text-align: left; line-height: 1.2;">
                        <div v-for="req in props.row.desirable" :key="req.reqname">
                            {{ req.reqname }}
                        </div>
                        <div v-if="!props.row.desirable.length">None</div>
                    </div>
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-candidates",
                r'''
                <q-td :props="props" style="background-color: #f5f5f5; text-align: left;">
                    {{ props.row.candidates }}
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-highest_candidate_status",
                r'''
                <q-td :props="props" style="background-color: #f5f5f5; text-align: left;">
                    {{ props.row.highest_candidate_status }}
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-assigned_to",
                r'''
                <q-td :props="props" style="background-color: #f5f5f5; text-align: left;">
                    {{ props.row.assigned_to }}
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-state",
                r'''
                <q-td :props="props" style="background-color: #f5f5f5; text-align: left;">
                    {{ props.row.state }}
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-days_left",
                r'''
                <q-td :props="props" :style="props.row.days_left === 'None' ? '' : (parseInt(props.row.days_left) < 0 ? 'background-color: #ffcdd2; text-align: left;' : parseInt(props.row.days_left) < 7 ? 'background-color: #fff9c4; text-align: left;' : 'background-color: #c8e6c9; text-align: left;')">
                    {{ props.row.days_left }}
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-actions",
                r'''
                <q-td :props="props">
                    <q-btn dense flat round icon="more_vert">
                        <q-menu>
                            <q-list style="min-width: 150px">
                                <q-item clickable v-close-popup
                                        @click="console.log('Emitting details for ' + props.row.job_id); $parent.$emit('menu_action', {action: 'details', row_id: props.row.job_id})">
                                    <q-item-section>View Details</q-item-section>
                                </q-item>
                                <q-item clickable v-close-popup
                                        @click="console.log('Emitting edit for ' + props.row.job_id); $parent.$emit('menu_action', {action: 'edit', row_id: props.row.job_id})">
                                    <q-item-section>Edit</q-item-section>
                                </q-item>
                                <q-item clickable v-close-popup
                                        @click="console.log('Emitting delete for ' + props.row.job_id); $parent.$emit('menu_action', {action: 'delete', row_id: props.row.job_id})">
                                    <q-item-section>Delete</q-item-section>
                                </q-item>
                            </q-list>
                        </q-menu>
                    </q-btn>
                </q-td>
                '''
            )
            self.table.on('menu_action', self._on_action)
            self.table.on('rowClick', lambda e: print(f"Row clicked: {e.args}"))

    def _update_columns(self, e):
        """Update table columns based on selected columns to hide, respecting preferred order."""
        self.selected_columns = e.value if e.value else []  # Selected columns are hidden
        self.columns = [
            col for col in self.all_columns
            if col['name'] not in self.selected_columns  # Exclude selected columns
        ]
        # Sort visible columns by preferred order
        self.columns = sorted(
            self.columns,
            key=lambda col: self.preferred_column_order.index(col['name']) if col['name'] in self.preferred_column_order else len(self.preferred_column_order)
        )
        self.table.columns = self.columns
        self.table.update()

    def _on_action(self, event):
        """Handle events from the action menu."""
        print("--- _on_action triggered ---")
        print(f"Event args: {event.args}")
        payload = event.args
        action = payload.get('action')
        row_id = payload.get('row_id')

        row = self.jobs_map.get(row_id)
        if not row:
            print(f"Could not find job with ID: {row_id}")
            return

        job_title = row.get('title', 'Unknown')
        print(f"Action: {action} on job: {job_title} (ID: {row_id})")

        if action == 'details':
            ui.notify(f"Showing details for {job_title}", type='info')
        elif action == 'edit':
            ui.notify(f"Editing {job_title}", type='warning')
        elif action == 'delete':
            ui.notify(f"Deleting {job_title}", type='negative')

# Sample data (all five jobs from provided input)
def get_initial_jobs() -> List[JobRequest]:
    return [
        JobRequest(
            job_id="job_1",
            title="Frontend Developer",
            description="Develop UI components using React.",
            customer="Acme Inc",
            contact_person="Alice",
            start_date=date(2025, 10, 26),
            duration="permanent",
            due_date=date(2025, 10, 1),
            requirements=[
                RequirementPayload(reqname="React", isActive=True, ismusthave=False, source="USER"),
                RequirementPayload(reqname="AWS", isActive=True, ismusthave=False, source="USER"),
                RequirementPayload(reqname="React", isActive=True, ismusthave=True, source="JD"),
                RequirementPayload(reqname="Python", isActive=True, ismusthave=True, source="USER")
            ],
            state="2-In Progress",
            candidates=2,
            highest_candidate_status="4 - Submitted",
            assigned_to="recruiter1",
            created_at=datetime(2025, 9, 22, 21, 10, 45, 344007)
        ),
        JobRequest(
            job_id="job_2",
            title="Backend Engineer",
            description="Build backend services with Python.",
            customer="Acme Inc",
            contact_person="Bob",
            start_date=date(2025, 10, 25),
            duration="6 months",
            due_date=date(2025, 10, 1),
            requirements=[
                RequirementPayload(reqname="Python", isActive=True, ismusthave=False, source="USER"),
                RequirementPayload(reqname="Python", isActive=True, ismusthave=True, source="USER"),
                RequirementPayload(reqname="AWS", isActive=True, ismusthave=False, source="JD"),
                RequirementPayload(reqname="Python", isActive=True, ismusthave=False, source="JD"),
                RequirementPayload(reqname="FastAPI", isActive=True, ismusthave=True, source="JD")
            ],
            state="3-Contracted",
            candidates=2,
            highest_candidate_status="4 - Submitted",
            assigned_to="recruiter1",
            created_at=datetime(2025, 9, 22, 21, 10, 45, 344251)
        ),
        JobRequest(
            job_id="job_3",
            title="Data Analyst",
            description="Analyze data and generate insights.",
            customer="Acme Inc",
            contact_person="Charlie",
            start_date=date(2025, 10, 6),
            duration="permanent",
            due_date=date(2025, 9, 25),
            requirements=[
                RequirementPayload(reqname="Docker", isActive=True, ismusthave=True, source="USER"),
                RequirementPayload(reqname="Python", isActive=True, ismusthave=False, source="USER")
            ],
            state="2-In Progress",
            candidates=2,
            highest_candidate_status="5 - Contracted",
            assigned_to="recruiter2",
            created_at=datetime(2025, 9, 22, 21, 10, 45, 344349)
        ),
        JobRequest(
            job_id="job_4",
            title="DevOps Specialist",
            description="Manage infrastructure and CI/CD.",
            customer="Acme Inc",
            contact_person="Diana",
            start_date=date(2025, 10, 7),
            duration="contract",
            due_date=date(2025, 10, 6),
            requirements=[
                RequirementPayload(reqname="Python", isActive=True, ismusthave=False, source="JD"),
                RequirementPayload(reqname="TypeScript", isActive=True, ismusthave=True, source="USER"),
                RequirementPayload(reqname="SQL", isActive=True, ismusthave=True, source="JD"),
                RequirementPayload(reqname="FastAPI", isActive=True, ismusthave=True, source="JD"),
                RequirementPayload(reqname="Python", isActive=True, ismusthave=True, source="USER")
            ],
            state="2-In Progress",
            candidates=2,
            highest_candidate_status="5 - Contracted",
            assigned_to="recruiter1",
            created_at=datetime(2025, 9, 22, 21, 10, 45, 344459)
        ),
        JobRequest(
            job_id="job_5",
            title="Product Manager",
            description="Define product strategy and roadmap.",
            customer="Acme Inc",
            contact_person="Ethan",
            start_date=date(2025, 10, 3),
            duration="permanent",
            due_date=date(2025, 9, 29),
            requirements=[
                RequirementPayload(reqname="Docker", isActive=True, ismusthave=False, source="JD"),
                RequirementPayload(reqname="AWS", isActive=True, ismusthave=True, source="USER")
            ],
            state="1-Open",
            candidates=2,
            highest_candidate_status="5 - Contracted",
            assigned_to="recruiter2",
            created_at=datetime(2025, 9, 22, 21, 10, 45, 344550)
        )
    ]

@ui.page('/')
def main_page():
    initial_jobs = get_initial_jobs()
    JobList(jobs=initial_jobs)

ui.run(port=8005, reload=False)