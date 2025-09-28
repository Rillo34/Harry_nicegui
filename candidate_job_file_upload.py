from nicegui import events, ui
import api_fe
import uuid
import asyncio
import sys
import os
import comp_candidate_table1
from comp_left_drawer import LeftDrawer
from comp_requirements import RequirementSection
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from models import RequirementPayload, EvaluateResponse, CandidateResultLong, RequirementResult, ReEvaluateResponse, ReSize, ReSizeResponse


controller = api_fe.UploadController()
list_of_cvs = []
# Initialize with sample data to test UI rendering
controller.requirements = []
list_of_requirements = []


def main_page():
    Left_drawer = LeftDrawer()
    controller.requirements.clear()
    def refresh_candidates(candidates):
        table_container.clear()
        with table_container:
            candidate_ui_table = comp_candidate_table1.CandidateTable(candidates)

    async def handle_jd_upload(e: events.UploadEventArguments):
        controller.uploaded_job_description = e
        ui.notify(f'Job description uploaded: {e.name}')
        print(f'Jobbeskrivning sparad: {e.name}')

    async def handle_cv_upload(e: events.MultiUploadEventArguments):
        cv_files = []
        cv_files = [
            ('cvs', (name, content, mime))
            for name, content, mime in zip(e.names, e.contents, e.types)
        ]
        controller.uploaded_cvs = cv_files

    async def re_evaluate():
        response = controller.re_evaluate()
        print("in re-evaluate")
        if response:
            response_data = ReEvaluateResponse(**response.json())
            controller.job_id = response_data.job_id
            print("\n controllerns requirements i reeval efter response:\n", controller.requirements)
            candidates = response_data.candidates
            RequirementSection.refresh_requirements(requirements_section)
            refresh_candidates(candidates)
            Eval_button.props('disabled') 


    async def handle_send_to_backend():
        response = controller.send_to_backend()
        Eval_button.props('disabled') 
        Reeval_button.props(remove='disabled')
        print("Raw response:", response)   
        response_data = EvaluateResponse(**response.json())
        new_requirements = response_data.updated_requirements
        controller.requirements = new_requirements
        job_card.clear()
        controller.job_id = response_data.job.job_id
        controller.job_description = response_data.job.description
        controller.customer = response_data.job.customer
        with job_card:
            ui.label(f'Job_ID: {controller.job_id}')
            ui.label(f'Description: {controller.job_description}')
            ui.label(f'Customer: {controller.customer}')
        file_section_expansion.expanded = False 
        file_section_expansion.update()
        candidates = response_data.candidates        
        if candidates:  # Check if candidates list is not empty
            RequirementSection.refresh_requirements(requirements_section)
            refresh_candidates(candidates)
        else:
            ui.notify('No candidates returned from backend', type='warning')

    async def on_shortlist_change(e):
        controller.shortlist_size = e.value
        new_value = e.value
        response = controller.re_size()
        print("in re-size")
        if response:
            response_data = ReSizeResponse(**response.json())
            candidates = response_data.candidates
            refresh_candidates(candidates)
            Eval_button.props('disabled') 
            ui.notify(f'Shortlist size changed to {new_value}')
        else:
            print("Error in resizing")    
        # re_evaluate()  # om du vill köra direkt    

        
    with ui.row().classes('w-full h-screen'):
        # ui.label('Harry').classes('text-lg font-medium ml-2')
        with ui.column().classes('w-96 p-4'):
            file_section_expansion = ui.expansion('File upload', icon='folder').classes('w-96')
            with file_section_expansion:
                # Job description upload
                with ui.card().classes('shadow-lg p-4 w-96'):
                    ui.label('Upload JD').classes('text-lg font-bold')
                    ui.upload(on_upload=handle_jd_upload, auto_upload=True)

                # CV upload
                with ui.card().classes('shadow-lg p-4 w-96'):
                    ui.label('Upload CVs').classes('text-lg font-bold')
                    ui.upload(on_multi_upload=handle_cv_upload, auto_upload=True, multiple=True)
            
            Eval_button = ui.button('Initial evaluate', icon='send').classes('mt-4 bg-blue-500 text-white').on('click', lambda e: handle_send_to_backend())

            with ui.card().classes('shadow-lg p-4 w-96 mt-4'):
                requirements_section = RequirementSection(controller, ui.card().classes('shadow-lg p-4 w-96 t-4'))  # Instantiate here


        # with ui.column().classes('w-2/3 p-4'):
        #     with ui.card().classes('shadow-lg p-4 w-full mt-4'):
        #         with ui.row().classes("w-full justify-between gap-2"):
        #             ui.label('Candidates').classes('text-lg font-bold mb-2')
        #             job_card = ui.card().classes('shadow-md p-4 w-1/4 mt-4')
        #             # job_id_input = ui.input(label='Job-ID', value=controller.job_id).props('readonly')
        #             # ui.label('Välj Shortlist Size').classes('text-lg font-bold')
        #             shortlist_size = ui.select(
        #                 options=[1, 3, 5, 10, 20],
        #                 value=controller.shortlist_size,
        #                 label='Shortlist size',
        #                 on_change=on_shortlist_change
        #             ).classes("w-[150px] mt-2")
        #             def on_checkbox_change(e):
        #                     ui.notify(f'Checkbox is now {str(e.value)}')
        #             c1 = ui.checkbox('Include internal candidates', on_change=on_checkbox_change)
        #             # Här kan du ha en tom rad för filter senare
        #             Reeval_button =ui.button('Re-evaluate', icon='send').classes('mt-4 bg-blue-500 text-white').on('click', lambda e: re_evaluate()).props('disabled')
        #         filter_container = ui.row().classes("flex flex-wrap gap-4")
        #         table_container = ui.element('div').classes('w-full max-w-[1400px] mx-auto')                
        #         initial_candidate_data = comp_candidate_table1.get_initial_data()
        #         with table_container:
        #             candidate_ui_table = comp_candidate_table1.CandidateTable(initial_candidate_data)

ui.page('/')(main_page)
ui.run(port=8004, reload=False)


candidate_list = [CandidateResultLong(candidate_id='CAND_004', name='Sheila Myers', combined_score=0.65, summary='Would surface environment music over trip.', assignment='Special effects artist, Ball-Johnson', location='Robertville, Bahamas', internal=False, years_exp='3-5', education="Master's, Computer Science", requirements=[RequirementResult(reqname='7+ years CFO experience', status='NO', ismusthave=True, source='JD'), RequirementResult(reqname='High-growth tech experience', status='MAYBE', ismusthave=True, source='JD'), RequirementResult(reqname='M&A experience', status='NO', ismusthave=True, source='JD'), RequirementResult(reqname='Financial data translation', status='MAYBE', ismusthave=True, source='JD'), RequirementResult(reqname="Master's degree in finance", status='YES', ismusthave=True, source='JD')]), CandidateResultLong(candidate_id='CAND_002', name='Bryan Berry', combined_score=0.47, summary='Adult ask industry lay indicate early number improve.', assignment='Emergency planning/management officer, Brown, Garcia and Herrera', location='West Rachel, Saint Vincent and the Grenadines', internal=False, years_exp='0-2', education='PhD, AI & Machine Learning', requirements=[RequirementResult(reqname='7+ years CFO experience', status='YES', ismusthave=True, source='JD'), RequirementResult(reqname='High-growth tech experience', status='NO', ismusthave=True, source='JD'), RequirementResult(reqname='M&A experience', status='MAYBE', ismusthave=True, source='JD'), RequirementResult(reqname='Financial data translation', status='MAYBE', ismusthave=True, source='JD'), RequirementResult(reqname="Master's degree in finance", status='NO', ismusthave=True, source='JD')]), CandidateResultLong(candidate_id='CAND_003', name='Denise Russell', combined_score=0.44, summary='Yeah job Republican control citizen lay middle relationship understand mean how stage produce.', assignment='Geophysicist/field seismologist, Marquez, Obrien and Ramos', location='Josephstad, Saint Vincent and the Grenadines', internal=False, years_exp='15+', education="Bachelor's, Information Systems", requirements=[RequirementResult(reqname='7+ years CFO experience', status='NO', ismusthave=True, source='JD'), RequirementResult(reqname='High-growth tech experience', status='NO', ismusthave=True, source='JD'), RequirementResult(reqname='M&A experience', status='MAYBE', ismusthave=True, source='JD'), RequirementResult(reqname='Financial data translation', status='MAYBE', ismusthave=True, source='JD'), RequirementResult(reqname="Master's degree in finance", status='MAYBE', ismusthave=True, source='JD')]), CandidateResultLong(candidate_id='CAND_001', name=None, combined_score=0.37, summary=None, assignment=None, location=None, internal=False, years_exp=None, education=None, requirements=[])]
candidate1=[CandidateResultLong(candidate_id='CAND_004', name='Sheila Myers', combined_score=0.65, summary='Would surface environment music over trip.', assignment='Special effects artist, Ball-Johnson', location='Robertville, Bahamas', internal=False, years_exp='3-5', education="Master's, Computer Science", requirements=[RequirementResult(reqname='7+ years CFO experience', status='NO', ismusthave=True, source='JD'), RequirementResult(reqname='High-growth tech experience', status='MAYBE', ismusthave=True, source='JD'), RequirementResult(reqname='M&A experience', status='NO', ismusthave=True, source='JD'), RequirementResult(reqname='Financial data translation', status='MAYBE', ismusthave=True, source='JD'), RequirementResult(reqname="Master's degree in finance", status='YES', ismusthave=True, source='JD')])]
