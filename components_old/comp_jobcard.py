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
        self.job = job.model_dump(exclude_none=True)
        self.job['musthave'] = [req for req in self.job['requirements'] if req['ismusthave']]
        self.job['desirable'] = [req for req in self.job['requirements'] if not req['ismusthave']]
        self._build_ui()

    def _build_ui(self):
        self.card_container = ui.element('div').classes("w-full flex justify-center")
        self._render_card()

    def _render_card(self):
        self.card_container.clear()
        with self.card_container:
            with ui.card().props(f'draggable="true" id="job-card-{self.job["job_id"]}"').classes(
                "w-[220px] h-[240px] p-1 leading-none bg-white rounded-md shadow-sm border border-gray-200"
            ):
                # Table layout
                with ui.element('table').classes("w-full text-xs border-collapse"):
                    # Header row with title, badge, and menu button
                    with ui.element('tr'):
                        with ui.element('td').classes("font-bold text-gray-800 pr-2"):
                            ui.label(self.job["title"])
                            ui.badge(self.job["state"], color="blue" if self.job["state"] == "Open" else "gray").classes("text-xs font-medium ml-1")
                        with ui.element('td').classes("text-right"):
                            with ui.row().classes('w-full items-center'):
                                result = ui.label().classes('mr-auto')  # Placeholder, not used here
                                with ui.button(icon='menu').classes("text-gray-500 text-xs").props('flat dense') as menu_button:
                                    with ui.menu() as menu:
                                        ui.menu_item('Visa detaljer', on_click=lambda: self._handle_action('details'))
                                        ui.menu_item('Redigera', on_click=lambda: self._handle_action('edit'))
                                        ui.menu_item('Ta bort', on_click=lambda: self._handle_action('delete'))
                                        ui.separator()
                                        ui.menu_item('Close', menu.close)

                    # Status row
                    with ui.element('tr'):
                        with ui.element('td').classes("text-gray-700").props('colspan=2'):
                            ui.html(f"Status: {self.job['state']}")
                    # Customer row
                    with ui.element('tr'):
                        with ui.element('td').classes("text-gray-600").props('colspan=2'):
                            ui.html(f"Customer: {self.job['customer']}")
                    # Contact row
                    with ui.element('tr'):
                        with ui.element('td').classes("text-gray-600").props('colspan=2'):
                            ui.html(f"Contact: {self.job['contact_person']}")

                    # Details section
                    with ui.element('tr'):
                        with ui.element('td').classes("text-gray-600").props('colspan=2'):
                            with ui.expansion("Details").classes("w-full text-xs leading-none"):
                                ui.label(f"Description: {self.job['description']}")
                                ui.label(f"Start: {self.job['start_date']}")
                                ui.label(f"Duration: {self.job['duration']}")

                    # # Requirements row
                    # with ui.element('tr'):
                    #     with ui.element('td').classes("text-gray-700 font-medium pr-1"):
                    #         ui.html("Requirements:")
                    #     with ui.element('td').classes("text-gray-600"):
                    #         with ui.element('div').classes("flex flex-col"):
                    #             for req in self.job["musthave"]:
                    #                 ui.label(f"{req['reqname']} (M)")
                    #             for req in self.job["desirable"]:
                    #                 ui.label(f"{req['reqname']} (D)")

                    # Candidates row
                    with ui.element('tr'):
                        with ui.element('td').classes("text-gray-600").props('colspan=2'):
                            if self.job["candidates"]:
                                ui.html(f'''
                                    <q-chip color="light-blue-3" text-color="black" icon="person" class="text-xs">
                                        {len(self.job["candidates"])} Candidate{'s' if len(self.job["candidates"]) > 1 else ''}
                                    </q-chip>
                                ''')
                            else:
                                ui.label("No candidates").classes("italic")

    def _handle_action(self, action):
        job_title = self.job.get('title', 'Okänt')
        print(f"{action.capitalize()} action performed for {job_title} (ID: {self.job['job_id']})")
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