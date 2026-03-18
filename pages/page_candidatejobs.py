from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer
# from niceGUI.components.comp_candidatejobs_table import CandidateJobsTable
from niceGUI.components.comp_jobselector import JobSelector
from niceGUI.dev.comp_candidatejobs_table_dev import CandidateJobsTable
from backend.models import CandidateResultLong
from niceGUI.app_state import API_client, ui_controller
from datetime import date

import json
from backend.models import CandidateResultLong, RequirementResult


@ui.page('/candidatejobs')
async def candidate_jobs_page():
    drawer = LeftDrawer()

    if not ui_controller.candidate_states_name_list: 
        states = await API_client.get_candidate_states() 
        ui_controller.set_candidate_states(states) 
        status_options = ui_controller.candidate_states_name_list
    else:
        status_options = ui_controller.candidate_states_name_list
    
    async def on_status_change(job_id, new_status):  #Behöver skrivas om
        ui_controller.job_id = job_id
        ui_controller.job_state = new_status
        await API_client.job_status_update(job_id, new_status)
        print(f"Status updated for job_id={job_id} to {new_status}")
    
    async def on_reeval(new_requirements):  #Behöver skrivas om
        print("ska utvärdera igen")
        candidates = await API_client.reeval_new_requirements(ui_controller.job_id, new_requirements)
        return candidates
    
    async def get_job_selector_list():  #Behöver skrivas om
        print("ska utvärdera igen")
        job_sel_list = await API_client.get_job_selector_list()
        return job_sel_list
    
    table_container = ui.column()  # <-- här hamnar tabellen

    async def display_table(job_id):
        table_container.clear()  # 🧹 Ta bort tidigare tabell
        candidates = await API_client.get_candidates_job(job_id)
        callbacks = {
            "on_status_change": on_status_change,
            "status_options": status_options,
            "on_reeval": on_reeval,
        }

        with table_container:
            CandidateJobsTable(
                candidates=candidates,
                callbacks=callbacks
            )


    job_list = await get_job_selector_list()
    jobselector = JobSelector(job_list, display_table)
    job_id = ui.context.client.request.query_params.get('job_id')
    if job_id:
        print("Loading job from query:", job_id)
        await display_table(job_id)
        ui_controller.job_id = job_id
    # print("Job id:", job_id)
    # candidates = get_test_data()
    
    

# @ui.page('/candidatejobs')
# async def candidate_jobs_page():
#     drawer = LeftDrawer()
#     print("In candidatejobs_page")
#     candidates = get_test_data()
#     candidate_job_table = CandidateJobsTable(API_client, candidates=candidates)
#     # candidate_job_table = CandidateJobsTable(candidates=candidates)