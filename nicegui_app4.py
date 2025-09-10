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

# --- Del 2: JobCard-klass (mindre version) ---
class JobCard:
    def __init__(self, job: JobRequest, parent: ui.element):
        self.job = job.dict(exclude_none=True)
        self.job['musthave'] = [req for req in self.job['requirements'] if req['ismusthave']]
        self.job['desirable'] = [req for req in self.job['requirements'] if not req['ismusthave']]
        self.parent = parent
        self.card = None
        self._build_ui()

    def _build_ui(self):
        self.card = ui.card().props(f'draggable="true" id="job-card-{self.job["job_id"]}"').classes("w-full p-1 bg-white rounded shadow-sm border border-gray-200 cursor-move text-xs h-24 overflow-hidden")
        with self.card:
            ui.label(self.job["title"]).classes("font-bold text-sm truncate")
            ui.label(f"Status: {self.job['state']}").classes("text-gray-600 text-xs")
            ui.label(f"Customer: {self.job['customer']}").classes("text-gray-600 text-xs truncate")
            with ui.column().classes("gap-0 mt-1"):
                if self.job['musthave']:
                    ui.label(f"{self.job['musthave'][0]['reqname']} (M)").classes("text-gray-600 text-xs truncate")
                if len(self.job['musthave']) > 1 or self.job['desirable']:
                    ui.label("...").classes("text-gray-600 text-xs")

    def _handle_dragstart(self, e):
        e.args['dataTransfer']['setData']('text/plain', self.job['job_id'])

# --- Del 3: PipelineView-klass ---
class PipelineView:
    def __init__(self):
        self.swimlanes = {
            'backlog': [],
            'assigned': [],
            'submitted': [],
            'contracted': []
        }
        self.jobs = [get_job1(), get_job2(), get_job3(), get_job4()]
        self.swimlanes['backlog'] = self.jobs
        self.card_map = {}
        self.drop_zones = {}
        self._build_ui()

    def _build_ui(self):
        self.container = ui.element('div').classes('w-full border border-gray-300 rounded-lg overflow-hidden')
        self._render_swimlanes()

    def _render_swimlanes(self):
        self.container.clear()
        with self.container:
            with ui.row().classes('w-full'):
                for swimlane in ['backlog', 'assigned', 'submitted', 'contracted']:
                    with ui.column().classes('p-2 border-r border-gray-300 flex-1 min-h-96 bg-gray-50'):
                        ui.label(swimlane.capitalize()).classes('text-md font-bold mb-2 text-gray-800 text-center')
                        drop_zone = ui.element('div').classes('w-full min-h-80').props('droppable="true"').on('drop', lambda e, s=swimlane: self._handle_drop(e, s)).on('dragover', lambda e: e.prevent_default()).on('drop', lambda e: e.prevent_default())  # Prevent default to ensure drop
                        self.drop_zones[swimlane] = drop_zone
                        with drop_zone:
                            for job in self.swimlanes[swimlane]:
                                card = JobCard(JobRequest(**job), drop_zone)
                                self.card_map[job['job_id']] = card

    def _handle_drop(self, e, new_swimlane):
        job_id = e.args['dataTransfer']['getData']('text/plain')
        old_swimlane = next((s for s in self.swimlanes if any(j['job_id'] == job_id for j in self.swimlanes[s])), None)
        if old_swimlane and old_swimlane != new_swimlane:
            job = next(j for j in self.swimlanes[old_swimlane] if j['job_id'] == job_id)
            self.swimlanes[old_swimlane].remove(job)
            self.swimlanes[new_swimlane].append(job)
            print(f"Moved {job['title']} from {old_swimlane} to {new_swimlane}")
            card = self.card_map[job_id]
            card.card.move(self.drop_zones[new_swimlane])
            card.parent = self.drop_zones[new_swimlane]

def get_job1() -> dict:
    return {
        'job_id': 'J1',
        'title': 'Auror',
        'description': 'Protect the wizarding world from dark forces.',
        'customer': 'Ministry of Magic',
        'contact_person': 'Kingsley Shacklebolt',
        'state': 'Open',
        'start_date': '2025-11-01',
        'duration': 'Permanent',
        'requirements': [
            {'reqname': 'Combat Skills', 'status': 'YES', 'ismusthave': True, 'source': 'Job Spec'},
            {'reqname': 'Leadership', 'status': 'YES', 'ismusthave': True, 'source': 'Job Spec'},
            {'reqname': 'Dark Arts Knowledge', 'status': 'MAYBE', 'ismusthave': False, 'source': 'Interview'}
        ],
        'candidates': [
            {'candidate_id': 'Nr1', 'name': 'Harry Potter', 'combined_score': 0.95, 'status': 'Interviewed'},
            {'candidate_id': 'Nr2', 'name': 'Hermione Granger', 'combined_score': 0.98, 'status': 'Offered'}
        ]
    }

def get_job2() -> dict:
    job = get_job1()
    job['job_id'] = 'J2'
    job['title'] = 'Magizoologist'
    job['description'] = 'Study magical creatures.'
    return job

def get_job3() -> dict:
    job = get_job1()
    job['job_id'] = 'J3'
    job['title'] = 'Potion Master'
    job['description'] = 'Brew potions.'
    return job

def get_job4() -> dict:
    job = get_job1()
    job['job_id'] = 'J4'
    job['title'] = 'Quidditch Coach'
    job['description'] = 'Train Quidditch players.'
    return job

@ui.page('/')
def main_page():
    ui.label('Pipeline View').classes('text-2xl font-bold p-4')
    PipelineView()

ui.run(port=8004, reload=False)