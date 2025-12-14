from nicegui import ui
from .comp_left_drawer import LeftDrawer
# from comp_joblist import JobList
from .comp_joblist import JobList
from .comp_requirements import RequirementSection
from .comp_file_upload import FileUploadSection, ReqMatrixUploadSection  
# from comp_candidate_table1 import CandidateTable, get_initial_data
from .comp_candidatejobs_table import CandidateJobsTable, get_initial_data
from .comp_jobcard_cand_jobs import JobCardCandidateJobs
from .comp_cons_datamodel import DataModelTable
from .comp_user_admin_dev import UserAdminDevComponent, CompanySummaryJobMatch
import pandas as pd

from .api_fe import APIController, UploadController
from backend.models import JobRequest, CompanyProfile, CompanyJobFit

ui_controller = UploadController()
API_client = APIController(ui_controller)
list_of_cvs = []
import asyncio
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


@ui.page('/candidatejobs')
async def candidate_jobs_page(job_id: str = None):
    print("Job ID from query:", job_id)
    drawer = LeftDrawer()
    if job_id:
        ui_controller.job_id = job_id
        await API_client.api_get_candidates_job()
    ui.label(f"Job ID: {job_id}")

    for key, value in ui_controller.__dict__.items():
        print(f"{key}: {value}")

    with ui.row().classes('w-full h-screen items-start overflow-hidden'):
        # Vänster kolumn: filuppladdning + knappar
        with ui.column().classes('w-96 p-4 h-full overflow-auto'):
            # with ui.card().classes('shadow-md p-4 w-1/4 mt-4') as job_card:
            #     ui.label(f'Job ID: {ui_controller.job_id}').classes('text-sm font-medium text-gray-700 mb-1')
            #     ui.label(f'Description: {ui_controller.job_description}').classes('text-sm font-medium text-gray-700 mb-1')
            #     ui.label(f'Customer: {ui_controller.customer}').classes('text-sm font-medium text-gray-700 mb-1')
            job_section = JobCardCandidateJobs(ui_controller)
            file_upload_section = FileUploadSection(ui_controller)
            Eval_button = ui.button('Initial evaluate', icon='send') \
                .classes('mt-4 bg-blue-500 text-white') \
                .on('click', lambda e: initial_evaluate())
            requirements_section = RequirementSection(ui_controller)

        # Höger kolumn: kandidater
        with ui.column().classes('flex-1 p-4 h-full overflow-auto'):
            with ui.row().classes("w-full justify-between gap-2"):
                ui.label('Candidates').classes('text-lg font-bold mb-2')
                # with ui.card().classes('shadow-md p-4 w-1/4 mt-4') as job_card:
                ui.space().classes("ml-auto")

                with ui.row().classes("items-center gap-2"):
                    checkbox_1 = ui.checkbox(text="Include internal candidates", on_change=lambda e: get_internal_candidates())
                    shortlist_size = ui.select(
                        options=[1, 3, 5, 10, 20],
                        value=ui_controller.shortlist_size,
                        label='Shortlist size',
                        on_change=lambda e: resize(e.value)
                    ).classes("w-[150px]")

                    Reeval_button = (
                        ui.button('Re-evaluate', icon='send')
                        .classes('bg-blue-500 text-white')
                        .on('click', lambda e: re_evaluate())
                        .props('enabled')
                    )

            # Tabellen placeras direkt i kolumnen
            if job_id:
                candidates_data = ui_controller.candidates
            else:
                candidates_data = get_initial_data()
            with ui.element().classes("w-full overflow-auto"):
                candidate_ui_table = CandidateJobsTable(candidates_data)

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
    
    async def get_internal_candidates():
        print("in get_internal_candidates")
        await API_client.api_get_internal_candidates()
        print("nr of candidates: ", len(ui_controller.candidates))
        candidate_ui_table.update(ui_controller.candidates)
        ui.notify(f"Updated with {len(ui_controller.candidates)} candidates")
    

@ui.page('/jobs-automate')
async def jobs_automate_page():
    drawer = LeftDrawer()
    container = ui.column()  # plats för resultatet

    async def get_mails_async(e):
        mail_button.delete()

        with container:
            spinner = ui.spinner('dots', size='lg', color='blue')
            label = ui.label('Fetching mails ...')

        job_list = await API_client.get_all_mails()

        spinner.delete()
        label.delete()
        print("joblist: ", job_list)
        JobList(job_list, API_client)

    mail_button = ui.button(
        'Get jobs from Harry mailbox',
        icon='outgoing_mail',
        on_click=get_mails_async
    ).classes('bg-blue-500 text-white')




@ui.page('/jobs')
async def jobs_page():
    drawer = LeftDrawer()
    data_model_response = await API_client.get_datamodel_jobs()
    print("data_model_response: ", data_model_response)
    df = pd.DataFrame(data_model_response)
    ui_controller.job_states_name_list = df['name'].tolist()
    job_list = await API_client.get_all_jobs()
    print("joblist: ", job_list)
    joblist_display = JobList(job_list, API_client)



@ui.page('/datamodel')
async def datamodel_page():
    drawer = LeftDrawer()
    data_model_response = await API_client.get_datamodel_jobs()
    print("data_model_response: ", data_model_response)
    df = pd.DataFrame(data_model_response)
    data_model_display = DataModelTable(df, API_client)
    

@ui.page('/reqmatrix')
async def reqmatrix_page():
    drawer = LeftDrawer()
    ui.label('Requirement Matrix Page')
    req_matrix_upload_section = ReqMatrixUploadSection(API_client)


@ui.page('/companyjobfit')
async def company_jobfit_page():
    drawer = LeftDrawer()
    with ui.tabs().classes('w-full') as tabs:
        summary_tab = ui.tab('Company summary and job fit')
        user_tab = ui.tab('User handling')
    with ui.tab_panels(tabs, value = summary_tab).classes('w-full'):
        with ui.tab_panel(summary_tab):
            company_summary_job_match = CompanySummaryJobMatch(API_client)
        with ui.tab_panel(user_tab):
            admin_instance = UserAdminDevComponent(API_client)
    

    # async def fetch_company_summary(company_id):
    #     print("Fetching company summary for :", company_id)
    #     company_profile = await API_client.api_get_company_summary(company_id)
    #     if company_profile:
    #         ui_controller.company_summary = company_profile.summary
    #         ui_controller.company_id = company_profile.company_id
    #         ui.notify('Company summary fetched successfully')
    #         print("Company summary:", company_profile.summary)
    #     else:
    #         ui.notify('No summary found for the given company ID')
    #         print("No summary found for company_id:", company_id)
    # with ui.row().classes('items-center gap-2'):
    #     # company_id_input = ui.input('Company name', value=str(ui_controller.company_id)).classes('w-48')
    #     fetch_nexer_button = ui.button('Fetch Nexer Summary', on_click=lambda: fetch_company_summary("nexer")).classes('bg-blue-500 text-white')
    #     fetch_structor_button = ui.button('Fetch Structor Summary', on_click=lambda: fetch_company_summary("structor")).classes('bg-blue-500 text-white')
    # summary_area = ui.textarea('Company Summary').bind_value(ui_controller, 'company_summary').classes('w-full h-48 mt-4')
    # match_button = ui.button('Match Jobs to Company', on_click=lambda: match_jobs_to_company()).classes('bg-green-500 text-white mt-4') 
    # columns = [
    #         {'name': 'job_id', 'label': 'Job_id', 'field': 'job_id', 'sortable': True, 'align': 'left'},
    #         {'name': 'job_fit', 'label': 'Job fit', 'field': 'job_fit', 'sortable': True, 'align': 'left'},
    #         {'name': 'customer', 'label': 'Customer', 'field': 'customer', 'sortable': True, 'align': 'left'},
    #         {'name': 'title', 'label': 'Title', 'field': 'title', 'sortable': True, 'align': 'left'},
    #         {'name': 'assessment', 'label': 'Assessment', 'field': 'assessment','sortable': True, 'align': 'left'},
    #         {'name': 'recruiter', 'label': 'Recruiter', 'field': 'recruiter', 'sortable': True, 'align': 'left'}
    #     ]
    # job_fit_table = ui.table(rows=[], columns=columns)
    # job_fit_table.classes('w-full h-64 text-left').props('wrap-cells').style('text-align: left; white-space: normal; word-break: break-word;')
    
    # # Lägg till din slot direkt vid deklarationen
    # job_fit_table.add_slot('body-cell-job_fit', '''
    #     <q-td key="job_fit" :props="props">
    #         <q-badge :color="props.value == 'OK' ? 'green' : 'red'">
    #             {{ props.value }}
    #         </q-badge>
    #     </q-td>
    # ''')

    # async def match_jobs_to_company():
    #     if not ui_controller.company_id:
    #         ui.notify('Please fetch the company summary first')
    #         return
    #     # jobs = await API_client.match_company_to_jobs(ui_controller.company_id)
    #     matched_results = await API_client.match_company_to_jobs(ui_controller.company_id)
    #     ui_controller.matched_results = [fit.model_dump() for fit in matched_results]
    #     job_fits = ui_controller.matched_results
    #     ui.notify(f"Matched {len(matched_results)} jobs to company profile")
    #     for result in matched_results:
    #         print(result)
    
    #     rows = [row for row in ui_controller.matched_results]
    #     job_fit_table.rows = rows
    #     job_fit_table.update()
        

       



@ui.page('/datavalidation')
async def datavalidation_page():
    drawer = LeftDrawer()
    ui.label('Printing variables in ui_controller:')
    for key, value in ui_controller.__dict__.items():
        ui.label(f"{key}: {value}")
    def clear_controller():
        ui_controller.__dict__.clear()
        ui.notify('Controller data raderad')
    ui.button('Erase  controller-data', on_click=clear_controller)    

ui.run(port=8005, reload=False)