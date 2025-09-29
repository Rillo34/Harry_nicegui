from nicegui import ui
from comp_left_drawer import LeftDrawer
from comp_joblist import JobList
from comp_requirements import RequirementSection
from comp_file_upload import FileUploadSection
# from comp_candidate_table1 import CandidateTable, get_initial_data
from comp_candidate_table1_new import CandidateTable, get_initial_data

from api_fe import APIController, UploadController
from models import JobRequest

ui_controller = UploadController()
API_client = APIController(ui_controller)
list_of_cvs = []
# Initialize with sample data to test UI rendering
ui_controller.requirements = []
list_of_requirements = []


@ui.page('/')
def home_page():
    ui.label('Welcome to Harry')
    drawer = LeftDrawer()
    # Main content area
    with ui.column().classes("p-4"):
        ui.image("Harry.jpg")
        ui.label("Welcome!").classes("text-xl")
        ui.label("Swipe from the left or use the menu button to open the drawer.")

@ui.page('/jobs')
def jobs_page():
    drawer = LeftDrawer()
    job_list = API_client.get_all_jobs()
    print("joblist: ", job_list)
    joblist_display = JobList(job_list)


@ui.page('/candidatejobs')
def candidate_jobs_page():
    drawer = LeftDrawer()
    # Hela sidan som row
    with ui.row().classes('w-full h-screen items-start'):

        # Vänster kolumn: filuppladdning + knappar
        with ui.column().classes('w-96 p-4'):
            file_upload_section = FileUploadSection(ui_controller)
            Eval_button = ui.button('Initial evaluate', icon='send') \
                .classes('mt-4 bg-blue-500 text-white') \
                .on('click', lambda e: initial_evaluate())
            requirements_section = RequirementSection(ui_controller)

        # Höger kolumn: kandidater
        with ui.column().classes('flex-1 p-4'):
            # Översta rad med label, job-card, knappar
            # with ui.row().classes("w-full justify-between gap-2"):
            #     ui.label('Candidates').classes('text-lg font-bold mb-2')
            #     with ui.card().classes('shadow-md p-4 w-1/4 mt-4') as job_card:
            #         ui.label(ui_controller.job_id)
            #     shortlist_size = ui.select(
            #         options=[1, 3, 5, 10, 20],
            #         value=ui_controller.shortlist_size,
            #         label='Shortlist size',
            #         on_change=lambda e: resize(e.value)
            #     ).classes("w-[150px] mt-2")
            #     Reeval_button = ui.button('Re-evaluate', icon='send').classes('mt-4 bg-blue-500 text-white') \
            #         .on('click', lambda e: re_evaluate()) \
            #         .props('enabled')

            # Tabellen placeras direkt i kolumnen
            initial_candidate_data = get_initial_data()
            candidate_ui_table = CandidateTable(initial_candidate_data)

    # Async-funktion för att hämta kandidater
    async def initial_evaluate():
        print("in initial eval")
        await API_client.files_to_backend()
        print("nr of candidates: ", len(ui_controller.candidates))
        candidate_ui_table.update(ui_controller.candidates)
        ui.notify(f"Updated with {len(ui_controller.candidates)} candidates")
        requirements_section.refresh_requirements()
        Eval_button.props('disabled') 
        Reeval_button.props(remove='disabled')
    
    async def resize(shortlist_size):
        print("in resize")
        ui_controller.shortlist_size = shortlist_size
        await API_client.api_resize()
        print("nr of candidates: ", len(ui_controller.candidates))
        candidate_ui_table.update(ui_controller.candidates)
        ui.notify(f"Updated with {len(ui_controller.candidates)} candidates")


    async def re_evaluate():
        print("in re_evaluate")
        ui_controller.shortlist_size = shortlist_size
        await API_client.api_reevaluate()
        print("nr of candidates: ", len(ui_controller.candidates))
        candidate_ui_table.update(ui_controller.candidates)
        ui.notify(f"Updated with {len(ui_controller.candidates)} candidates")
    



ui.run(port=8005, reload=False)