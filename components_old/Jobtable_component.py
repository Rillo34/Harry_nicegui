import sys
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel
from nicegui import ui

# --- Del 1: Nödvändiga modeller ---
class RequirementPayload(BaseModel):
    reqname: str
    status: str
    ismusthave: bool
    source: str

class CandidatePayload(BaseModel):
    candidate_id: str
    name: Optional[str] = None
    combined_score: Optional[float] = None
    status: Optional[str] = None

class JobRequest(BaseModel):
    job_id: str
    title: str
    description: str
    customer: str
    contact_person: str
    state: str
    start_date: str
    duration: str
    requirements: List[RequirementPayload]
    candidates: Optional[List[CandidatePayload]] = []

# --- Del 2: JobTable-klass ---
class JobTable:
    def __init__(self, jobs: List[JobRequest]):
        self.jobs_map = {j.job_id: j.dict(exclude_none=True) for j in jobs}
        self.jobs_list = []
        for job in self.jobs_map.values():
            job_copy = job.copy()
            job_copy['musthave'] = [req for req in job['requirements'] if req['ismusthave']]
            job_copy['desirable'] = [req for req in job['requirements'] if not req['ismusthave']]
            self.jobs_list.append(job_copy)
        
        self.columns = [
            {
                "name": field,
                "label": field.replace("_", " ").capitalize(),
                "field": field,
                "sortable": True,
                "style": "max-width: 200px; white-space: normal; word-wrap: break-word;"
            }
            for field in JobRequest.__fields__.keys() if field not in ['requirements', 'candidates']
        ]
        self.columns.extend([
            {
                "name": "musthave",
                "label": "Must-have",
                "field": "musthave",
                "sortable": False
            },
            {
                "name": "desirable",
                "label": "Desirable",
                "field": "desirable",
                "sortable": False
            },
            {
                "name": "candidates",
                "label": "Candidates",
                "field": "candidates",
                "sortable": False
            },
            {
                "name": "actions",
                "label": "",
                "field": "actions",
                "sortable": False
            }
        ])

        self.req_names: List[str] = sorted({
            req["reqname"]
            for job in self.jobs_list
            for req in job["requirements"]
        })
        self.state_options: List[str] = sorted({
            job["state"]
            for job in self.jobs_list
        })
        self.filters: Dict[str, List[str]] = {req_name: [] for req_name in self.req_names}
        self.state_filter: List[str] = []
        self._build_ui()

    def _build_ui(self):
        with ui.card().classes("w-full mb-4"):
            ui.label("Filter by Requirements and State").classes("text-lg font-bold")
            self.filter_container = ui.row().classes("flex flex-wrap gap-4")
            with self.filter_container:
                self._render_filters()

        self.table = ui.table(
            columns=self.columns,
            rows=self.jobs_list,
            row_key="job_id",
            pagination={'sortBy': 'title', 'descending': False}
        ).classes("w-full max-w-[1400px]")

        with self.table:
            self.table.add_slot(
                "body-cell-musthave",
                r'''
                <q-td :props="props">
                    <div class="flex flex-wrap gap-1">
                        <q-icon
                            v-for="req in props.row.musthave"
                            :name="req.status === 'YES' ? 'check_circle' : req.status === 'NO' ? 'cancel' : 'help'"
                            :color="req.status === 'YES' ? 'green' : req.status === 'NO' ? 'red' : 'yellow-8'"
                            size="sm"
                        >
                            <q-tooltip>{{ req.reqname }}: {{ req.status }}</q-tooltip>
                        </q-icon>
                    </div>
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-desirable",
                r'''
                <q-td :props="props">
                    <div class="flex flex-wrap gap-1">
                        <q-icon
                            v-for="req in props.row.desirable"
                            :name="req.status === 'YES' ? 'check_circle' : req.status === 'NO' ? 'cancel' : 'help'"
                            :color="req.status === 'YES' ? 'green' : req.status === 'NO' ? 'red' : 'yellow-8'"
                            size="sm"
                        >
                            <q-tooltip>{{ req.reqname }}: {{ req.status }}</q-tooltip>
                        </q-icon>
                    </div>
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-candidates",
                r'''
                <q-td :props="props">
                    <q-chip
                        v-if="props.row.candidates.length > 0"
                        color="light-blue-3"
                        text-color="black"
                        icon="person"
                    >
                        {{ props.row.candidates.length }} Candidate{{ props.row.candidates.length > 1 ? 's' : '' }}
                        <q-tooltip>
                            <div v-for="cand in props.row.candidates">
                                {{ cand.name || 'Unknown' }} ({{ cand.status || 'No status' }})
                            </div>
                        </q-tooltip>
                    </q-chip>
                    <span v-else>No candidates</span>
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
                                    <q-item-section>Visa detaljer</q-item-section>
                                </q-item>
                                <q-item clickable v-close-popup
                                        @click="console.log('Emitting edit for ' + props.row.job_id); $parent.$emit('menu_action', {action: 'edit', row_id: props.row.job_id})">
                                    <q-item-section>Redigera</q-item-section>
                                </q-item>
                                <q-item clickable v-close-popup
                                        @click="console.log('Emitting delete for ' + props.row.job_id); $parent.$emit('menu_action', {action: 'delete', row_id: props.row.job_id})">
                                    <q-item-section>Ta bort</q-item-section>
                                </q-item>
                            </q-list>
                        </q-menu>
                    </q-btn>
                </q-td>
                '''
            )
            self.table.on('menu_action', self._on_action)
            self.table.on('rowClick', lambda e: print(f"Row clicked: {e.args}"))  # Debug row click

    def _on_action(self, event):
        """Hanterar händelser från åtgärdsmenyn."""
        print("--- _on_action triggered ---")
        print(f"Event args: {event.args}")
        payload = event.args
        action = payload.get('action')
        row_id = payload.get('row_id')

        row = self.jobs_map.get(row_id)
        if not row:
            print(f"Kunde inte hitta jobb med ID: {row_id}")
            return

        job_title = row.get('title', 'Okänt')
        print(f"Action: {action} på jobb: {job_title} (ID: {row_id})")

        if action == 'details':
            ui.notify(f"Visar detaljer för {job_title}", type='info')
        elif action == 'edit':
            ui.notify(f"Redigerar {job_title}", type='warning')
        elif action == 'delete':
            ui.notify(f"Tar bort {job_title}", type='negative')

    def _render_filters(self):
        for req_name in self.req_names:
            with ui.column():
                ui.label(req_name).classes("text-sm")
                ui.select(
                    ["YES", "NO", "MAYBE"], multiple=True, value=self.filters[req_name],
                    on_change=lambda e, rn=req_name: self._update_filter(rn, e.value)
                ).classes("w-40").props('dense options-dense')
        with ui.column():
            ui.label("Job State").classes("text-sm")
            ui.select(
                self.state_options, multiple=True, value=self.state_filter,
                on_change=lambda e: self._update_state_filter(e.value)
            ).classes("w-40").props('dense options-dense')

    def _update_filter(self, req_name: str, values: List[str]):
        self.filters[req_name] = values
        self.apply_filters()

    def _update_state_filter(self, values: List[str]):
        self.state_filter = values
        self.apply_filters()

    def apply_filters(self):
        filtered_rows = []
        for job in self.jobs_list:
            include = True
            # Apply requirement filters
            for req_name, selected_statuses in self.filters.items():
                if selected_statuses:
                    req_status = next(
                        (req["status"] for req in job["requirements"] if req["reqname"] == req_name), None
                    )
                    if req_status not in selected_statuses:
                        include = False
                        break
            # Apply state filter
            if self.state_filter and job["state"] not in self.state_filter:
                include = False
            if include:
                filtered_rows.append(job)
        self.table.rows = filtered_rows

# --- Del 3: Exempeldata och applikationsstart ---
def get_initial_data() -> List[JobRequest]:
    return [
        JobRequest(
            job_id='J1',
            title='Auror',
            description='Protect the wizarding world from dark forces.',
            customer='Ministry of Magic',
            contact_person='Kingsley Shacklebolt',
            state='Open',
            start_date='2025-11-01',
            duration='Permanent',
            requirements=[
                RequirementPayload(reqname='Combat Skills', status='YES', ismusthave=True, source='Job Spec'),
                RequirementPayload(reqname='Leadership', status='YES', ismusthave=True, source='Job Spec'),
                RequirementPayload(reqname='Dark Arts Knowledge', status='MAYBE', ismusthave=False, source='Interview')
            ],
            candidates=[
                CandidatePayload(candidate_id='Nr1', name='Harry Potter', combined_score=0.95, status='Interviewed'),
                CandidatePayload(candidate_id='Nr2', name='Hermione Granger', combined_score=0.98, status='Offered')
            ]
        ),
        JobRequest(
            job_id='J2',
            title='Magizoologist',
            description='Study and care for magical creatures.',
            customer='Newt Scamander Enterprises',
            contact_person='Newt Scamander',
            state='Closed',
            start_date='2025-12-01',
            duration='2 years',
            requirements=[
                RequirementPayload(reqname='Creature Knowledge', status='YES', ismusthave=True, source='Job Spec'),
                RequirementPayload(reqname='Field Experience', status='NO', ismusthave=True, source='Job Spec'),
                RequirementPayload(reqname='Research Skills', status='YES', ismusthave=False, source='Interview')
            ],
            candidates=[
                CandidatePayload(candidate_id='Nr3', name='Luna Lovegood', combined_score=0.90, status='Hired')
            ]
        )
    ]

@ui.page('/')
def main_page():
    ui.label('Job Table').classes('text-2xl font-bold p-4')
    initial_jobs = get_initial_data()
    JobTable(jobs=initial_jobs)

ui.run(port=8004, reload=False)  # Använder reload=False för stabilare felsökning