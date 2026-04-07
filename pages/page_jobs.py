from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.components.comp_joblist import JobList
from niceGUI.app_state import API_client, ui_controller

@ui.page('/jobs')
async def jobs_page():
    drawer = LeftDrawer()

    if not ui_controller.job_states_name_list: 
        states = await API_client.get_job_states() 
        ui_controller.set_job_states(states) 
        status_options = ui_controller.job_states_name_list
    else:
        status_options = ui_controller.job_states_name_list
    

    async def get_jobs_from_dir_api():
        joblist = await API_client.get_jobs_from_directory()
        JobList(joblist, callbacks=callbacks)
        print("FROM API:", joblist)

    async def on_status_change(job_id, new_status):
        await API_client.job_status_update(job_id, new_status)
        print(f"Status updated for job_id={job_id} to {new_status}")

    async def update_job_table():
        updated_joblist = await API_client.get_all_jobs()
        old_jobs.update_jobs(updated_joblist)
        print("Job table updated with latest data from API.")

    async def on_edit_job(job_id, job_data):
        print(f"Editing job_id={job_id} with data: {job_data}")
        response = await API_client.edit_job(job_id, job_data)
        print(f"Edit job response: {response}")
        await update_job_table()
        # Optionally refresh the job list here
    
    callbacks = {"on_status_change": on_status_change, "status_options": status_options, "edit_job": on_edit_job} 
    joblist = await API_client.get_all_jobs()
    print("Initial joblist from API:\n", joblist)
    old_jobs = JobList(joblist, callbacks)
    ui.button("Get jobs from directory", on_click = get_jobs_from_dir_api)

