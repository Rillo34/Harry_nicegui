from nicegui import ui
from .comp_left_drawer import LeftDrawer
# from comp_joblist import JobList
from .comp_joblist import JobList
from .comp_requirements import RequirementSection
from .comp_file_upload import FileUploadSection, ReqMatrixUploadSection  
# from comp_candidate_table1 import CandidateTable, get_initial_data
from .comp_candidatejobs_table_dev import CandidateJobsTable, get_initial_data
from .comp_jobcard_cand_jobs import JobCardCandidateJobs
from .comp_user_admin_dev import UserAdminDevComponent, CompanySummaryJobMatch
import pandas as pd
import niceGUI.comp_cons_avail_dev

from .api_fe import APIController, UploadController
from backend.models import JobRequest, CompanyProfile, CompanyJobFit
from .comp_cons_avail_dev import DataTable

ui_controller = UploadController()
API_client = APIController(ui_controller)
list_of_cvs = []
import asyncio
# Initialize with sample data to test UI rendering
ui_controller.requirements = []
list_of_requirements = []


@ui.page('/')
def home_page():
    ui.label('Welcome to Harry - your AI-powered recruitment assistant').classes("text-xl")
    drawer = LeftDrawer()
    # Main content area
    with ui.column().classes("p-4"):
        ui.icon('smart_toy').classes('text-9xl text-blue-600 mb-4')
        ui.label("Swipe from the left or use the menu button to open the drawer.")


@ui.page('/candidatejobs')
async def candidate_jobs_page(job_id: str = None):
    print("Job ID from query:", job_id)
    drawer = LeftDrawer()
    if not ui_controller.job_id:
        candidates = get_initial_data()
    else:
        ui_controller.job_id = job_id
        response = await API_client.api_get_candidates_job()
        candidates = response.candidates
    candidatejobstable = CandidateJobsTable(API_client, candidates)
    # if job_id:
    #     ui_controller.job_id = job_id
    #     await API_client.api_get_candidates_job()
    # ui.label(f"Job ID: {job_id}")

    # for key, value in ui_controller.__dict__.items():
    #     print(f"{key}: {value}")

    # with ui.row().classes('w-full h-screen items-start overflow-hidden'):
    #     # Vänster kolumn: filuppladdning + knappar
    #     with ui.column().classes('w-96 p-4 h-full overflow-auto'):
    #         # with ui.card().classes('shadow-md p-4 w-1/4 mt-4') as job_card:
    #         #     ui.label(f'Job ID: {ui_controller.job_id}').classes('text-sm font-medium text-gray-700 mb-1')
    #         #     ui.label(f'Description: {ui_controller.job_description}').classes('text-sm font-medium text-gray-700 mb-1')
    #         #     ui.label(f'Customer: {ui_controller.customer}').classes('text-sm font-medium text-gray-700 mb-1')
    #         job_section = JobCardCandidateJobs(ui_controller)
    #         file_upload_section = FileUploadSection(ui_controller)
    #         Eval_button = ui.button('Initial evaluate', icon='send') \
    #             .classes('mt-4 bg-blue-500 text-white') \
    #             .on('click', lambda e: initial_evaluate())
    #         requirements_section = RequirementSection(ui_controller)

    #     # Höger kolumn: kandidater
    #     with ui.column().classes('flex-1 p-4 h-full overflow-auto'):
    #         with ui.row().classes("w-full justify-between gap-2"):
    #             ui.label('Candidates').classes('text-lg font-bold mb-2')
    #             # with ui.card().classes('shadow-md p-4 w-1/4 mt-4') as job_card:
    #             ui.space().classes("ml-auto")

    #             with ui.row().classes("items-center gap-2"):
    #                 checkbox_1 = ui.checkbox(text="Include internal candidates", on_change=lambda e: get_internal_candidates())
    #                 shortlist_size = ui.select(
    #                     options=[1, 3, 5, 10, 20],
    #                     value=ui_controller.shortlist_size,
    #                     label='Shortlist size',
    #                     on_change=lambda e: resize(e.value)
    #                 ).classes("w-[150px]")

    #                 Reeval_button = (
    #                     ui.button('Re-evaluate', icon='send')
    #                     .classes('bg-blue-500 text-white')
    #                     .on('click', lambda e: re_evaluate())
    #                     .props('enabled')
    #                 )

    #         # Tabellen placeras direkt i kolumnen
    #         if job_id:
    #             candidates_data = ui_controller.candidates
    #         else:
    #             candidates_data = get_initial_data()
    #         with ui.element().classes("w-full overflow-auto"):
    #             candidate_ui_table = CandidateJobsTable(candidates_data)

    # Async-funktion för att hämta kandidater
    # async def initial_evaluate():
    #     print("in initial eval")
    #     await API_client.files_to_backend()
    #     print("nr of candidates: ", len(ui_controller.candidates))
    #     candidate_ui_table.update(ui_controller.candidates)
    #     ui.notify(f"Updated with {len(ui_controller.candidates)} candidates")
    #     requirements_section.refresh_requirements()
    #     Eval_button.props('disabled') 
    #     Reeval_button.props(remove='disabled')
    
    # async def resize(shortlist_size):
    #     print("in resize")
    #     ui_controller.shortlist_size = shortlist_size
    #     await API_client.api_resize()
    #     print("nr of candidates: ", len(ui_controller.candidates))
    #     candidate_ui_table.update(ui_controller.candidates)
    #     ui.notify(f"Updated with {len(ui_controller.candidates)} candidates")

    # async def re_evaluate():
    #     print("in re_evaluate")
    #     ui_controller.shortlist_size = shortlist_size
    #     await API_client.api_reevaluate()
    #     print("nr of candidates: ", len(ui_controller.candidates))
    #     candidate_ui_table.update(ui_controller.candidates)
    #     ui.notify(f"Updated with {len(ui_controller.candidates)} candidates")
    
    # async def get_internal_candidates():
    #     print("in get_internal_candidates")
    #     await API_client.api_get_internal_candidates()
    #     print("nr of candidates: ", len(ui_controller.candidates))
    #     candidate_ui_table.update(ui_controller.candidates)
    #     ui.notify(f"Updated with {len(ui_controller.candidates)} candidates")
    

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
    print("In jobs_page")
    # data_model_response = await API_client.get_datamodel_jobs()
    # print("data_model_response: ", data_model_response)
    # df = pd.DataFrame(data_model_response)
    # ui_controller.job_states_name_list = df['name'].tolist()
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
    

        
@ui.page('/allocations')
async def allocations_page():
    
    contracts = await API_client.get_contracts()
    print("contracts: ", contracts)
    allocation_response = await API_client.get_allocations()
    print("allocation_response: ", allocation_response)
    drawer = LeftDrawer()   
    # with ui.column().classes('w-full'):
    #     with ui.tabs().classes('w-full') as tabs:
    #         contract_base_tab = ui.tab('Contracts')
    #         allocation_tab = ui.tab('Allocations % (edit)')
    #         candidate_tab = ui.tab('Alloc summary %')
    #         contract_tab = ui.tab('Contracts summary hours')
    #     with ui.tab_panels(tabs, value = contract_tab).classes('w-full'):
    #         is_allocation_table = False
    #         with ui.tab_panel(contract_base_tab):
    #             df = niceGUI.comp_cons_avail_dev.get_contract_total_hours_df(allocation_df, contract_df)
    #             contract_df["remains"] = df["remains"]
    #             contract_table = DataTable(contract_df)
    #         with ui.tab_panel(allocation_tab):
    #             df = niceGUI.comp_cons_avail_dev.get_allocations_perc_df(allocation_df)
    #             allocation_table = DataTable(df)
    #             allocation_table.add_allocation_buttons()
    #             allocation_table.add_delete_and_copy_buttons()

    #         with ui.tab_panel(candidate_tab):
    #             df = niceGUI.comp_cons_avail_dev.get_candidate_perc_df(allocation_df)
    #             candidate_summary_table = DataTable(df)
    #         with ui.tab_panel(contract_tab):
    #             df = niceGUI.comp_cons_avail_dev.get_contract_total_hours_df(allocation_df, contract_df)
    #             # df = df[['contract_id', 'remains']]
    #             new_contract_df = (
    #                 contract_df
    #                 .drop(columns=["remains"], errors="ignore")
    #                 .merge(
    #                     df[['contract_id', 'remains']],
    #                     on='contract_id',
    #                     how='right'
    #                 )
    #             )
    #             contract_summary_table = DataTable(df)       



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

@ui.page('/adminpanel')
async def admin_panel_page():
    drawer = LeftDrawer()
    ui.label('Admin panel')
    ui.label('Settings for competence fit (from values):')
    df = pd.DataFrame({ 'OK': [50], 'GOOD': [65], 'EXCELLENT': [80], }) 
    def update(r, c, value): 
        df.iat[r, c] = value 
        ui.notify(f'Set ({r}, {c}) to {value}') 
    with ui.grid(rows=len(df.index) + 1).classes('grid-flow-col'): 
        for c, col in enumerate(df.columns): 
            ui.label(col).classes('font-bold') 
            for r, value in enumerate(df[col]): 
                ui.number( value=value, on_change=lambda e, r=r, c=c: update(r, c, e.value) ) 



ui.run(port=8009, reload=False)