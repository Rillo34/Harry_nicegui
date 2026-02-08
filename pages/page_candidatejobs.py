from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.components.comp_joblist import JobList
from niceGUI.components.comp_candidatejobs_table import CandidateJobsTable
from backend.models import CandidateResultLong
from niceGUI.app_state import API_client, ui_controller
from datetime import date

def get_test_data():
    candidates = [
    CandidateResultLong(**{
        "candidate_id": "C-10231",
        "name": "Anna Lindström",
        "assignment": "Data Engineer – Retail Analytics Platform",
        "years_exp": "8",
        "location": "Stockholm",
        "education": "MSc Computer Science",
        "internal": False,
        "available_from": date(2026, 3, 1),
        "available_in": "3w",
        "combined_score": 0.87,
        "summary": "Experienced data engineer with strong background in cloud-native data pipelines.",
        "requirements": [
            {"reqname": "Python", "status": "YES", "ismusthave": True, "source": "JD"},
            {"reqname": "Azure Data Factory", "status": "YES", "ismusthave": True, "source": "JD"},
            {"reqname": "Databricks", "status": "MAYBE", "ismusthave": False, "source": "JD"}
        ],
        "availability": "3w",
        "status": "Available"
    }),
    CandidateResultLong(**{
        "candidate_id": "C-20488",
        "name": "Johan Ek",
        "assignment": "Fullstack Developer – Internal Tools",
        "years_exp": "5",
        "location": "Göteborg",
        "education": "BSc Software Engineering",
        "internal": True,
        "available_from": date(2026, 2, 20),
        "available_in": "2w",
        "combined_score": 0.72,
        "summary": "Fullstack developer with solid experience in TypeScript, React and backend APIs.",
        "requirements": [
            {"reqname": "React", "status": "YES", "ismusthave": True, "source": "JD"},
            {"reqname": "Node.js", "status": "YES", "ismusthave": True, "source": "JD"},
            {"reqname": "Docker", "status": "NO", "ismusthave": False, "source": "JD"}
        ],
        "availability": "2w",
        "status": "Internal"
    }),
    CandidateResultLong(**{
        "candidate_id": "C-30912",
        "name": "Sara Holm",
        "assignment": "Business Analyst – Finance Transformation",
        "years_exp": "6",
        "location": "Malmö",
        "education": "MSc Industrial Engineering",
        "internal": False,
        "available_from": date(2026, 4, 15),
        "available_in": "9w",
        "combined_score": 0.61,
        "summary": "Business analyst with experience in financial processes and ERP transitions.",
        "requirements": [
            {"reqname": "Process Mapping", "status": "YES", "ismusthave": True, "source": "JD"},
            {"reqname": "SQL", "status": "MAYBE", "ismusthave": False, "source": "JD"},
            {"reqname": "SAP FI/CO", "status": "NO", "ismusthave": True, "source": "JD"}
        ],
        "availability": "9w",
        "status": "Active"
    })
]   
    return candidates


    

@ui.page('/candidatejobs')
async def candidate_jobs_page():
    drawer = LeftDrawer()
    print("In candidatejobs_page")
    ui.label("Candidate Jobs Page - Under Construction")
    candidates = get_test_data()
    candidate_job_table = CandidateJobsTable(candidates)