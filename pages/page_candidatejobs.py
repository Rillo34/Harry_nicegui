from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer
# from niceGUI.components.comp_candidatejobs_table import CandidateJobsTable
from niceGUI.components.comp_jobselector import JobSelector
from niceGUI.components.comp_candidatejobs_table import CandidateJobsTable
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
    

    async def get_jobs_from_dir_api():
        joblist = await API_client.get_jobs_from_directory()
        JobList(joblist, callbacks=callbacks)
        print("FROM API:", joblist)

    async def on_status_change(job_id, new_status):  #Behöver skrivas om
        ui_controller.job_id = job_id
        ui_controller.job_state = new_status
        await API_client.job_status_update(job_id, new_status)
        print(f"Status updated for job_id={job_id} to {new_status}")
    
    async def on_reeval(new_requirements):  #Behöver skrivas om
        print("ska utvärdera igen")
        candidates = await API_client.reeval_new_requirements(ui_controller.job_id, new_requirements)
        return candidates
    
    async def get_all_jobs():  #Behöver skrivas om
        print("ska utvärdera igen")
        jobs = await API_client.get_all_jobs()
        job_short_list = [
            {"job_id": job["job_id"], "title": job["title"], "customer": job["customer"]}
            for job in jobs
        ]
        print("job short list", job_short_list)
        return job_short_list
    
    async def display_table(job_id):
        candidates = await API_client.get_candidates_job(job_id)
        callbacks = { "on_status_change": on_status_change, "status_options": status_options, "on_reeval": on_reeval } 
        print(candidates)
        candidate_job_table = CandidateJobsTable(
            candidates=candidates,
            callbacks=callbacks
        )
    
    job_list = await get_all_jobs()
    
    jobselector = JobSelector(job_list, display_table)
    job_id = ui.context.client.request.query_params.get('job_id')
    if job_id:
        print("Loading job from query:", job_id)
        await self.display_table(job_id)
        ui_controller.job_id = job_id
    print("Job id:", job_id)
    # candidates = get_test_data()
    
    

# @ui.page('/candidatejobs')
# async def candidate_jobs_page():
#     drawer = LeftDrawer()
#     print("In candidatejobs_page")
#     candidates = get_test_data()
#     candidate_job_table = CandidateJobsTable(API_client, candidates=candidates)
#     # candidate_job_table = CandidateJobsTable(candidates=candidates)