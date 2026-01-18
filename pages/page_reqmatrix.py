from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.components.comp_joblist import JobList
from niceGUI.app_state import API_client, ui_controller

@ui.page('/jobs')
async def reqmatrix_page():
    drawer = LeftDrawer()
    print("In jobs_page")
    # data_model_response = await API_client.get_datamodel_jobs()
    # print("data_model_response: ", data_model_response)
    # df = pd.DataFrame(data_model_response)
    # ui_controller.job_states_name_list = df['name'].tolist()
    job_list = await API_client.get_all_jobs()
    print("joblist: ", job_list)
    joblist_display = JobList(job_list, API_client)
