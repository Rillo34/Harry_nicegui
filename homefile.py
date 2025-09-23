from nicegui import ui
from comp_left_drawer import LeftDrawer
from comp_joblist import JobList
from api_fe import APIController

API_client = APIController()

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
    # joblist_display = JobList([])

# 
ui.run(port=8005)
