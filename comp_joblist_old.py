from nicegui import ui
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime, date
import uuid
import os
import sys
from faker import Faker
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from models import CandidatePayload, RequirementPayload, JobRequest
fake = Faker()


class JobList:
    def __init__(self, jobs: List[JobRequest]):
        self.status_order = {
            "Contacted": 1,
            "Interview": 2,
            "Offered": 3,
            "Hired": 4
        }
        self.jobs_map = {j.job_id: j.dict(exclude_none=True) for j in jobs}
        self.jobs_list = []
        for job in self.jobs_map.values():
            job_copy = job.copy()
            job_copy['musthave'] = [req for req in job['requirements'] if req['ismusthave']]
            job_copy['desirable'] = [req for req in job['requirements'] if not req['ismusthave']]
            candidates = job.get('candidates', [])
            job_copy['candidate_count'] = len(candidates)
            if candidates:
                max_level = max(self.status_order.get(c['status'], 0) for c in candidates)
                job_copy['highest_status'] = next((k for k, v in self.status_order.items() if v == max_level), "Unknown")
            else:
                job_copy['highest_status'] = "None"
            # Calculate days left until due_date
            if job_copy.get('due_date'):
                days_left = (job_copy['due_date'] - date.today()).days
                job_copy['days_left'] = f"{days_left}d" if days_left >= 0 else f"{-days_left}d"
            else:
                job_copy['days_left'] = "None"
            self.jobs_list.append(job_copy)

        # Define table columns
        excluded_fields = ["description", "requirements", "candidates", "created_at", "due_date"]
        ordered_fields = [f for f in JobRequest.__fields__ if f not in excluded_fields]
        ordered_fields.extend(["candidate_count", "highest_status", "days_left"])  # Add custom fields
        
        self.columns = [
            {
                "name": field,
                "label": field.replace("_", " ").capitalize() if field != "days_left" else "Days Left",
                "field": field,
                "sortable": True,
                "style": "max-width: 200px; white-space: normal; word-wrap: break-word;",
                "align": "left"
            }
            for field in ordered_fields
        ]
        self.columns.extend([
            {
                "name": "musthave",
                "label": "Must-have",
                "field": "musthave",
                "sortable": False,
                "style": "max-width: 250px; white-space: normal; word-wrap: break-word;",
                "align": "left"
            },
            {
                "name": "desirable",
                "label": "Desirable",
                "field": "desirable",
                "sortable": False,
                "style": "max-width: 250px; white-space: normal; word-wrap: break-word;",
                "align": "left"
            },
            {
                "name": "actions",
                "label": "",
                "field": "actions",
                "sortable": False,
                "align": "left"
            }
        ])

        self._build_ui()

    def _build_ui(self):
        with ui.row().classes('items-center p-2').style('width: auto'):
            ui.label('Job List').style('width: 150px').classes('text-xl font-bold')
            search_input = ui.input(label='Search').props('clearable').style('margin-left: 20px; width: 250px')
            
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
                "body-cell-candidate_count",
                r'''
                <q-td :props="props" style="background-color: #f5f5f5; text-align: left;">
                    {{ props.row.candidate_count }}
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-highest_status",
                r'''
                <q-td :props="props" style="background-color: #f5f5f5; text-align: left;">
                    {{ props.row.highest_status }}
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

# Example data with updated JobRequest model and candidates
def get_initial_jobs() -> List[JobRequest]:
    return [
        JobRequest(
            job_id=str(uuid.uuid4()),
            title="Senior Software Engineer",
            description="Develop and maintain web applications.",
            customer="TechCorp",
            contact_person="John Doe",
            state="Open",
            assigned_to="Jane Smith",
            start_date=fake.date_between(start_date='today', end_date='+1y'),
            duration="12 months",
            due_date=fake.date_between(start_date='+10d', end_date='+30d'),  # Green
            requirements=[
                RequirementPayload(reqname="Python", isActive=True, ismusthave=True, source="JD"),
                RequirementPayload(reqname="JavaScript", isActive=True, ismusthave=True, source="JD"),
                RequirementPayload(reqname="Cloud Experience", isActive=None, ismusthave=False, source="JD"),
                RequirementPayload(reqname="Agile Methodology", isActive=True, ismusthave=False, source="USER"),
            ],
            candidates=[
                CandidatePayload(candidate_id="cand1", name="Alice Johnson", status="Contacted"),
                CandidatePayload(candidate_id="cand2", name="Bob Wilson", status="Interview"),
                CandidatePayload(candidate_id="cand3", name="Charlie Davis", status="Hired"),
                CandidatePayload(candidate_id="cand4", name="Diana Evans", status="Offered"),
            ],
            created_at=fake.date_time_this_year(),
        ),
        JobRequest(
            job_id=str(uuid.uuid4()),
            title="Data Scientist",
            description="Analyze data and build predictive models.",
            customer="DataInc",
            contact_person="Emma Brown",
            state="In Progress",
            assigned_to="Mark Taylor",
            start_date=None,
            duration="6 months",
            due_date=fake.date_between(start_date='+2d', end_date='+5d'),  # Yellow
            requirements=[
                RequirementPayload(reqname="Machine Learning", isActive=True, ismusthave=True, source="JD"),
                RequirementPayload(reqname="SQL", isActive=False, ismusthave=True, source="JD"),
                RequirementPayload(reqname="Data Visualization", isActive=True, ismusthave=False, source="JD"),
            ],
            candidates=[
                CandidatePayload(candidate_id="cand5", name="Eve Foster", status="Offered"),
                CandidatePayload(candidate_id="cand6", name="Frank Green", status="Interview"),
            ],
            created_at=fake.date_time_this_year(),
        ),
        JobRequest(
            job_id=str(uuid.uuid4()),
            title="Project Manager",
            description="Oversee project execution and team coordination.",
            customer="GrowEasy",
            contact_person="Frank Green",
            state="Pending",
            assigned_to="Lisa White",
            start_date=fake.date_between(start_date='today', end_date='+6m'),
            duration="9 months",
            due_date=fake.date_between(start_date='-10d', end_date='-1d'),  # Red
            requirements=[
                RequirementPayload(reqname="PMP Certification", isActive=True, ismusthave=True, source="JD"),
                RequirementPayload(reqname="Scrum Master", isActive=None, ismusthave=False, source="USER"),
            ],
            candidates=[
                CandidatePayload(candidate_id="cand7", name="George Harris", status="Contacted"),
                CandidatePayload(candidate_id="cand8", name="Hannah Lee", status="Contacted"),
            ],
            created_at=fake.date_time_this_year(),
        ),
    ]
def get_initial_jobs2() -> List[JobRequest]:
    return [{"job_id":"job_1","title":"Frontend Developer","description":"Develop UI components using React.","customer":"Acme Inc","contact_person":"Alice","start_date":"2025-10-19","duration":"contract","due_date":null,"requirements":[{"reqname":"React","isActive":false,"ismusthave":false,"source":"JD"},{"reqname":"TypeScript","isActive":true,"ismusthave":true,"source":"JD"},{"reqname":"Python","isActive":false,"ismusthave":false,"source":"JD"},{"reqname":"React","isActive":false,"ismusthave":true,"source":"JD"},{"reqname":"TypeScript","isActive":false,"ismusthave":true,"source":"USER"}],"state":"1","candidates":[],"assigned_to":"recruiter1","created_at":"2025-09-21T13:19:58.788076"},{"job_id":"job_2","title":"Backend Engineer","description":"Build backend services with Python.","customer":"Acme Inc","contact_person":"Bob","start_date":"2025-10-05","duration":"permanent","due_date":null,"requirements":[{"reqname":"SQL","isActive":false,"ismusthave":true,"source":"USER"},{"reqname":"Docker","isActive":false,"ismusthave":true,"source":"JD"}],"state":"1","candidates":[],"assigned_to":"admin","created_at":"2025-09-21T13:19:58.788474"},{"job_id":"job_3","title":"Data Analyst","description":"Analyze data and generate insights.","customer":"Acme Inc","contact_person":"Charlie","start_date":"2025-10-20","duration":"permanent","due_date":null,"requirements":[{"reqname":"FastAPI","isActive":null,"ismusthave":false,"source":"JD"},{"reqname":"Kubernetes","isActive":false,"ismusthave":true,"source":"USER"}],"state":"1","candidates":[],"assigned_to":"admin","created_at":"2025-09-21T13:19:58.788571"},{"job_id":"job_4","title":"DevOps Specialist","description":"Manage infrastructure and CI/CD.","customer":"Acme Inc","contact_person":"Diana","start_date":"2025-10-13","duration":"permanent","due_date":null,"requirements":[{"reqname":"SQL","isActive":null,"ismusthave":false,"source":"USER"},{"reqname":"FastAPI","isActive":null,"ismusthave":true,"source":"JD"},{"reqname":"AWS","isActive":true,"ismusthave":true,"source":"JD"}],"state":"1","candidates":[],"assigned_to":"recruiter1","created_at":"2025-09-21T13:19:58.788670"},{"job_id":"job_5","title":"Product Manager","description":"Define product strategy and roadmap.","customer":"Acme Inc","contact_person":"Ethan","start_date":"2025-09-25","duration":"permanent","due_date":null,"requirements":[{"reqname":"AWS","isActive":true,"ismusthave":false,"source":"JD"},{"reqname":"Python","isActive":true,"ismusthave":true,"source":"USER"},{"reqname":"SQL","isActive":false,"ismusthave":false,"source":"JD"},{"reqname":"TypeScript","isActive":false,"ismusthave":false,"source":"JD"}],"state":"1","candidates":[],"assigned_to":"recruiter2","created_at":"2025-09-21T13:19:58.788761"}]

@ui.page('/')
def main_page():
    initial_jobs = get_initial_jobs2()
    JobList(jobs=initial_jobs)

ui.run(port=8005, reload=False)