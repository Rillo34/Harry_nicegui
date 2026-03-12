from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer
# from niceGUI.components.comp_candidatejobs_table import CandidateJobsTable
from niceGUI.dev.comp_candidatejobs_table_dev import CandidateJobsTable
from backend.models import CandidateResultLong
from niceGUI.app_state import API_client, ui_controller
from datetime import date

import json
from backend.models import CandidateResultLong, RequirementResult

def get_test_data():
    raw_json = """
    [
        {
            "candidate_id": "69_VM",
            "name": "Raz Domb",
            "assignment": "Data Engineering Tech Lead",
            "years_exp": "2011-Present",
            "location": "Prague, Czech Republic",
            "education": "Industrial engineering majoring in information systems",
            "internal": false,
            "available_from": null,
            "combined_score": 0.62,
            "summary": "The candidate has extensive experience...",
            "requirements": [
                {
                    "reqname": "CFO or senior financial leadership",
                    "status": "NO",
                    "ismusthave": true,
                    "source": "JD"
                },
                 {
                    "reqname": "aksjhdakshdg",
                    "status": "MAYBE",
                    "ismusthave": true,
                    "source": "JD"
                },
                 {
                    "reqname": "C leadership",
                    "status": "YES",
                    "ismusthave": false,
                    "source": "JD"
                }
            ],
            "availability": null,
            "status": null
        }
    ]
    """

    # 🔥 JSON → Python (null → None, true → True, false → False)
    data = json.loads(raw_json)

    # 🔥 Konvertera till dina Pydantic‑modeller
    candidates = [
        CandidateResultLong(
            **{
                **c,
                "requirements": (
                    [RequirementResult(**r) for r in c["requirements"]]
                    if c.get("requirements") else None
                )
            }
        )
        for c in data
    ]

    return candidates


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
    
    callbacks = { "on_status_change": on_status_change, "status_options": status_options } 
    print("In candidatejobs_page")

    job_id = ui.context.client.request.query_params.get('job_id')
    print("Job id:", job_id)
    # candidates = get_test_data()
    candidates = await API_client.get_candidates_job(job_id)
    print("Candidate i candidate_jobs_page:")
    print(candidates)
    candidate_job_table = CandidateJobsTable(
        candidates=candidates,
        callbacks=callbacks
    )
    

# @ui.page('/candidatejobs')
# async def candidate_jobs_page():
#     drawer = LeftDrawer()
#     print("In candidatejobs_page")
#     candidates = get_test_data()
#     candidate_job_table = CandidateJobsTable(API_client, candidates=candidates)
#     # candidate_job_table = CandidateJobsTable(candidates=candidates)