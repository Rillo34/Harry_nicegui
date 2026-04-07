from nicegui import ui
from pydantic import BaseModel
from typing import List, Optional

# --- 1. MODELLER & TESTDATA (Samma som innan) ---
class Requirement(BaseModel):
    reqname: str
    ismusthave: bool

class JobRequest(BaseModel):
    job_id: str
    title: str
    customer: str
    state: str
    days_left: int
    description: str
    requirements: List[Requirement]
    summary: Optional[str] = "Ingen sammanfattning."

test_jobs = [
    JobRequest(job_id="101", title="Senior Python Utvecklare", customer="TechCorp AB", state="1-Open", days_left=12, description="Backend-fokus.", requirements=[]),
    JobRequest(job_id="102", title="Frontend Designer", customer="DesignStudio", state="2-In Progress", days_left=-2, description="UI-fokus.", requirements=[]),
    JobRequest(job_id="103", title="DevOps Engineer", customer="CloudNine", state="1-Open", days_left=5, description="AWS & Docker.", requirements=[]),
]

# --- 2. KOMPONENTEN (Samma som innan) ---
def job_card(job: JobRequest, status_options: List[str]):
    accent_color = "#ef4444" if job.days_left < 0 else "#3b82f6"
    with ui.card().classes('w-full mb-4 p-0 shadow-sm border-l-4 overflow-hidden').style(f'border-color: {accent_color}'):
        with ui.row().classes('w-full items-center p-4 gap-6'):
            ui.label(str(job.days_left)).classes('text-2xl font-bold w-12')
            with ui.column().classes('flex-grow gap-0'):
                ui.label(job.title).classes('text-lg font-bold')
                ui.label(job.customer).classes('text-sm text-gray-500')
            ui.select(status_options, value=job.state).props('dense outlined').classes('w-44')

# --- 3. HUVUDSIDA MED SÖKLOGIK ---
@ui.page('/')
def main_page():
    ui.query('body').style('background-color: #f1f5f9;')
    status_options = ["1-Open", "2-In Progress", "3-Offered", "4-Contracted"]

    with ui.column().classes('w-full max-w-5xl mx-auto py-12 px-6'):
        ui.label('Rekryteringsöversikt').classes('text-4xl font-black mb-8')

        # SÖKFÄLTET
        # Vi använder 'on_change' för att trigga uppdateringen
        search_input = ui.input(placeholder='Sök på titel eller kund...') \
            .props('outlined bg-white rounded prepend-icon=search') \
            .classes('w-full mb-6 shadow-sm')

        # CONTAINER FÖR LISTAN
        # Vi skapar en tom kolumn som vi kan fylla på dynamiskt
        list_container = ui.column().classes('w-full')

        # FUNKTION FÖR ATT UPPDATERA LISTAN
        def update_list():
            search_query = search_input.value.lower()
            list_container.clear() # Töm listan först
            
            with list_container:
                # Filtrera jobben baserat på sökordet
                filtered_jobs = [
                    j for j in test_jobs 
                    if search_query in j.title.lower() or search_query in j.customer.lower()
                ]
                
                if not filtered_jobs:
                    ui.label('Inga jobb matchar din sökning...').classes('text-gray-400 mt-4')
                else:
                    for job in filtered_jobs:
                        job_card(job, status_options)

        # Koppla sökfältet till funktionen
        search_input.on('update:model-value', update_list)

        # Kör funktionen en gång direkt för att visa alla jobb vid start
        update_list()

ui.run()