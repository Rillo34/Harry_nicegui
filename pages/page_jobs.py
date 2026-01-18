from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.components.comp_joblist import JobList
from niceGUI.app_state import API_client, ui_controller

@ui.page('/jobs')
async def jobs_page():
    drawer = LeftDrawer()
    joblist = await API_client.get_all_jobs()

    if not ui_controller.job_states_name_list: 
        states = await API_client.get_datamodel_jobs() 
        ui_controller.set_job_states(states) 
        status_options = ui_controller.job_states_name_list
    else:
        status_options = ui_controller.job_states_name_list

    async def on_status_change(job_id, new_status):
        ui_controller.job_id = job_id
        ui_controller.job_state = new_status
        await API_client.job_status_update(job_id, new_status)
        print(f"Status updated for job_id={job_id} to {new_status}")
    
    callbacks = { "on_status_change": on_status_change, "status_options": status_options } 
    JobList(joblist, callbacks=callbacks)
