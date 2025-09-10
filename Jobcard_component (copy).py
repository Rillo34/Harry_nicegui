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

# --- Del 2: JobCardView-klass ---
class JobCardView:
    def __init__(self, job: JobRequest):
        self.job = job.dict(exclude_none=True)
        self.job['musthave'] = [req for req in self.job['requirements'] if req['ismusthave']]
        self.job['desirable'] = [req for req in self.job['requirements'] if not req['ismusthave']]
        self.menu_visible = False
        self._build_ui()

    def _build_ui(self):
        self.card_container = ui.element('div').classes("w-full flex justify-center")
        self._render_card()

    def _render_card(self):
        self.card_container.clear()
        with self.card_container:
            with ui.card().props(f'draggable="true" id="job-card-{self.job["job_id"]}"').classes(
                "w-[220px] h-[240px] p-1 leading-none bg-white rounded-md shadow-sm border border-gray-200 cursor-pointer"
            ).on('click', lambda: self._toggle_menu()):

                # Header: Title and State
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label(self.job["title"]).classes("text-xs font-semibold text-gray-800 leading-none")
                    ui.badge(self.job["state"], color="blue" if self.job["state"] == "Open" else "gray").classes("text-xs font-medium leading-none")

                # Key Info
                ui.label(f"Status: {self.job['state']}").classes("text-xs text-gray-700 leading-none")
                ui.label(f"Customer: {self.job['customer']}").classes("text-xs text-gray-600 leading-none")
                ui.label(f"Contact: {self.job['contact_person']}").classes("text-xs text-gray-600 leading-none")

                # Secondary Info
                with ui.expansion("Details").classes("w-full text-xs text-gray-600 leading-none max-h-[60px] overflow-auto"):
                    ui.label(f"Description: {self.job['description']}").classes("text-xs leading-none")
                    ui.label(f"Start: {self.job['start_date']}").classes("text-xs leading-none")
                    ui.label(f"Duration: {self.job['duration']}").classes("text-xs leading-none")

                # Requirements
                with ui.row():
                    ui.label("Requirements:").classes("text-xs font-medium text-gray-700 mr-1 leading-none")
                    with ui.element('div').classes("flex flex-col"):
                        for req in self.job["musthave"]:
                            ui.label(f"{req['reqname']} (M)").classes("text-xs text-gray-600 leading-none")
                        for req in self.job["desirable"]:
                            ui.label(f"{req['reqname']} (D)").classes("text-xs text-gray-600 leading-none")

                # Candidates
                with ui.row():
                    if self.job["candidates"]:
                        ui.html(f'''
                            <q-chip color="light-blue-3" text-color="black" icon="person" class="text-xs">
                                {len(self.job["candidates"])} Candidate{'s' if len(self.job["candidates"]) > 1 else ''}
                            </q-chip>
                        ''')
                    else:
                        ui.label("No candidates").classes("text-xs italic text-gray-500 leading-none")

                # Meny (dold initialt)
                with ui.element('div').bind_visibility_from(self, 'menu_visible'):
                    with ui.column().classes('bg-white shadow-md rounded-md p-1'):
                        ui.button('Visa detaljer', on_click=lambda: self._handle_action('details')).classes('text-xs text-gray-700')
                        ui.button('Redigera', on_click=lambda: self._handle_action('edit')).classes('text-xs text-gray-700')
                        ui.button('Ta bort', on_click=lambda: self._handle_action('delete')).classes('text-xs text-gray-700')

    def _toggle_menu(self):
        self.menu_visible = not self.menu_visible

    def _handle_action(self, action):
        job_title = self.job.get('title', 'Okänt')
        print(f"{action.capitalize()} action performed for {job_title} (ID: {self.job['job_id']})")
        self.menu_visible = False  # Stäng menyn efter action
        if action == 'details':
            ui.notify(f"Visar detaljer för {job_title}", type='info')
        elif action == 'edit':
            ui.notify(f"Redigerar {job_title}", type='warning')
        elif action == 'delete':
            ui.notify(f"Tar bort {job_title}", type='negative')

# --- Del 3: Exempeldata och applikationsstart ---
def get_initial_data() -> JobRequest:
    return JobRequest(
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
    )

@ui.page('/')
def main_page():
    ui.label('Job Card View').classes('text-2xl font-bold text-gray-800 p-4')
    job = get_initial_data()
    JobCardView(job=job)

ui.run(port=8004, reload=False)  # Använder reload=False för stabilare felsökning