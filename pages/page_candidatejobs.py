from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.components.comp_joblist import JobList
from niceGUI.app_state import API_client, ui_controller

@ui.page('/candidatejobs')
async def candidate_jobs_page():
    drawer = LeftDrawer()
    print("In candidatejobs_page")
    ui.label("Candidate Jobs Page - Under Construction")