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

    # ✅ Hämta status-options en gång
    if not ui_controller.candidate_states_name_list: 
        states = await API_client.get_candidate_states() 
        ui_controller.set_candidate_states(states) 
    status_options = ui_controller.candidate_states_name_list

    # -------------------------
    # Callbacks
    # -------------------------
    async def on_status_change(job_id, new_status):
        """Uppdatera job-status via API"""
        await API_client.job_status_update(job_id, new_status)
        print(f"Status updated for job_id={job_id} to {new_status}")

    async def on_reeval(job_id, new_requirements):
        """Re-evaluera kandidater för ett jobb"""
        print(f"Re-evaluating job {job_id}")
        candidates = await API_client.reeval_new_requirements(job_id, new_requirements)
        return candidates

    async def get_job_selector_list():
        """Hämta listan med jobb till job-selector"""
        return await API_client.get_job_selector_list()

    
    jobselector_container = ui.column()  # ligger ovanför tabellen
    table_container = ui.column()        # här hamnar tabellen

    async def display_table(job_id):
        """Rendera tabellen för ett specifikt job_id"""
        table_container.clear()  # ta bort tidigare tabell
        candidates = await API_client.get_candidates_job(job_id)
        callbacks = {
            "on_status_change": lambda new_status, jid=job_id: on_status_change(jid, new_status),
            "on_reeval": lambda new_req, jid=job_id: on_reeval(jid, new_req),
            "status_options": status_options
        }
        job_details = await API_client.get_job(job_id)
        job_info_label1.text = (
            f"Job: {job_details['title']} | Customer: {job_details['customer']}")
        job_info_label2.text = f"Description: {job_details['description']}"
        print ("Job details for job_id", job_id, ":", job_details)
        # Rendera tabellen
        with table_container:
            CandidateJobsTable(
                candidates=candidates,
                callbacks=callbacks
            )

    # -------------------------
    # Job-selector
    # -------------------------
    with jobselector_container:
        job_list = await get_job_selector_list()
        with ui.row().classes("items-center gap-4"):  # rad med lite mellanrum
            # JobSelector i vänsterkolumn
            with ui.column().classes("flex-auto"):
                jobselector = JobSelector(job_list, display_table)
            
            # Label med jobbinformation i högerkolumn
            with ui.column().classes("flex-auto"):
                job_info_label1 = ui.label("").classes("text-md font-semibold")
                job_info_label2 = ui.label("").classes("text-md")


    # -------------------------
    # Direktbesök med ?job_id=...
    # -------------------------
    job_id_from_query = ui.context.client.request.query_params.get("job_id")
    if job_id_from_query:
        print("Loading job from query:", job_id_from_query)
        await display_table(job_id_from_query)
    # print("Job id:", job_id)
    # candidates = get_test_data()
    
    

# @ui.page('/candidatejobs')
# async def candidate_jobs_page():
#     drawer = LeftDrawer()
#     print("In candidatejobs_page")
#     candidates = get_test_data()
#     candidate_job_table = CandidateJobsTable(API_client, candidates=candidates)
#     # candidate_job_table = CandidateJobsTable(candidates=candidates)