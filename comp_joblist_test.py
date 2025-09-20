from nicegui import ui
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime, date
import uuid
from faker import Faker

fake = Faker()

# Models
class CandidatePayload(BaseModel):
    candidate_id: str
    name: str
    status: str

class RequirementPayload(BaseModel):
    reqname: str
    isActive: Optional[bool] = None
    ismusthave: bool
    source: Literal["USER", "JD"]

class JobRequest(BaseModel):
    job_id: str
    title: str
    description: str
    customer: str
    contact_person: str
    state: str
    assigned_to: str
    start_date: Optional[date] = None
    duration: str
    requirements: List[RequirementPayload]
    candidates: Optional[List[CandidatePayload]] = []
    created_at: datetime
    model_config = {
        "from_attributes": True
    }

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
            self.jobs_list.append(job_copy)

        # Define table columns
        priority_fields = ["job_id", "title", "customer", "contact_person", "start_date", "duration", "state"]
        other_fields = [f for f in JobRequest.__fields__ if f not in priority_fields and f not in ["requirements", "candidates" "created_at", "description"]]
        excluded_fields = ["description"]
        ordered_fields = [f for f in priority_fields + other_fields if f not in excluded_fields]
        
        self.columns = [
            {
                "name": field,
                "label": field.replace("_", " ").capitalize(),
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
        ui.label('Job List').classes('text-2xl font-bold p-4')
        
        self.table = ui.table(
            columns=self.columns,
            rows=self.jobs_list,
            row_key="job_id",
            pagination={'sortBy': 'created_at', 'descending': True}
        ).classes("w-full max-w-[1800px]")

        with self.table:
            self.table.add_slot(
                "body-cell-musthave",
                r'''
                <q-td :props="props">
                    <div class="text-sm" style="text-align: left;">
                        <span v-for="req in props.row.musthave" :key="req.reqname">
                            {{ req.reqname }}<span v-if="props.row.musthave[props.row.musthave.length - 1] !== req">, </span>
                        </span>
                        <span v-if="!props.row.musthave.length">None</span>
                    </div>
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-desirable",
                r'''
                <q-td :props="props">
                    <div class="text-sm" style="text-align: left;">
                        <span v-for="req in props.row.desirable" :key="req.reqname">
                            {{ req.reqname }}<span v-if="props.row.desirable[props.row.desirable.length - 1] !== req">, </span>
                        </span>
                        <span v-if="!props.row.desirable.length">None</span>
                    </div>
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-candidate_count",
                r'''
                <q-td :props="props" style="background-color: #e3f2fd; text-align: left;">
                    {{ props.row.candidate_count }}
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-highest_status",
                r'''
                <q-td :props="props" style="background-color: #fff3e0; text-align: left;">
                    {{ props.row.highest_status }}
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

# Example data with more candidates and varied statuses
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

@ui.page('/')
def main_page():
    initial_jobs = get_initial_jobs()
    JobList(jobs=initial_jobs)

# if __name__ == '__main__':
ui.run(port=8005, reload=False)