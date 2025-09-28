from nicegui import events, ui
import api_fe
import uuid
import asyncio
import sys
import os
from typing import List, Optional, Literal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from models import RequirementPayload, EvaluateResponse, CandidateResultLong, RequirementResult


controller = api_fe.UploadController()
list_of_cvs = []
# Initialize with sample data to test UI rendering
controller.requirements = []
list_of_requirements = []

def main_page():
    table = None  # placeholder so inner functions can modify it

    def refresh_candidates(candidates: List[CandidateResultLong], _):
        print(f"Refreshing candidates: {len(candidates)} items")

        def get_icon_and_color(status: str):
            return {
                'YES': ('check_circle', 'green'),
                'MAYBE': ('help', 'orange'),
                'NO': ('cancel', 'red'),
            }.get(status, ('help', 'grey'))

        def build_expansion_html(requirements: List[RequirementResult]) -> str:
            must_haves = []
            desirables = []

            for r in requirements:
                icon, color = get_icon_and_color(r.status)
                html_row = '''
                <div class="flex items-center gap-2 q-mb-xs">
                <q-icon name="{icon}" color="{color}" size="18px" />
                <span>{reqname}</span>
                <q-tooltip>{status} ({source})</q-tooltip>
                </div>
                '''.format(
                    icon=icon,
                    color=color,
                    reqname=r.reqname,
                    status=r.status,
                    source=r.source
                )
                if r.ismusthave:
                    must_haves.append(html_row)
                else:
                    desirables.append(html_row)

            return '''
            <q-expansion-item label="Visa krav" expand-separator icon="info">
            <div class="text-green-700 text-bold q-mb-sm">Must-Haves</div>
            {must_haves}
            <div class="text-blue-700 text-bold q-mt-md q-mb-sm">Desirables</div>
            {desirables}
            </q-expansion-item>
            '''.format(
                must_haves=''.join(must_haves),
                desirables=''.join(desirables)
            )

        # Skapa tabellrader
        rows = []
        for c in candidates:
            rows.append({
                'Name': c.name or '',
                'Score': round(c.combined_score * 100),
                'Assignment': c.assignment or '',
                'Location': c.location or '',
                'Education': c.education or '',
                'Experience': c.years_exp or '',
                'Details': build_expansion_html(c.requirements or []),
            })

        # Definiera kolumner
        columns = [
            {'name': 'Name', 'label': 'Name', 'field': 'Name'},
            {'name': 'Score', 'label': 'Score', 'field': 'Score'},
            {'name': 'Assignment', 'label': 'Assignment', 'field': 'Assignment'},
            {'name': 'Location', 'label': 'Location', 'field': 'Location'},
            {'name': 'Education', 'label': 'Education', 'field': 'Education'},
            {'name': 'Experience', 'label': 'Experience', 'field': 'Experience'},
            {'name': 'Details', 'label': '', 'field': 'Details'},
        ]

        table.columns = columns
        table.rows = rows
        table.update()

        # Lägg till slot för HTML-rendering av expandable
        table.add_slot('body-cell-Details', '''
        <q-td :props="props">
        <div v-html="props.row['Details']"></div>
        </q-td>
        ''')




    def refresh_requirements():
        print(f"Refreshing requirements: {len(controller.requirements)} items")
        requirements_container.clear()
        with requirements_container:
            print("controllerns requirements: ", controller.requirements)
            for req in controller.requirements:
                print(f"Rendering requirement: {req.reqname}, must_have={req.ismusthave}")
                with ui.row().classes('w-full items-center border-b p-1'):
                    ui.switch(value=req.ismusthave, on_change=lambda e, r=req: toggle_requirement(r.reqname)).classes('mr-2').props('color=green')
                    ui.label(req.reqname).classes('flex-grow ' + ('font-bold text-green-700' if req.ismusthave else 'text-gray-600'))
                    ui.label('Must-Have' if req.ismusthave else 'Desirable').classes('mr-4 text-sm ' + ('text-green-700' if req.ismusthave else 'text-gray-500'))
                    ui.button(icon='delete', on_click=lambda e, r=req: remove_requirement(r.reqname)).props('flat round size=sm color=red').classes('ml-auto')

    def add_requirement(requirement, must_have=False):
        new_text = requirement.strip()
        print(f"Adding requirement: {new_text}, must_have={must_have}")
        if new_text:
            req = RequirementPayload(
                reqname=new_text,
                isActive=True,
                ismusthave=True,
                source="USER"
            )
            list_of_requirements.append(new_text)
            print("listan \n", list_of_requirements)
            print("anropar controllern \n")
            controller.add_requirement(req)
            # Fallback: append locally even if backend fails (for testing)
            refresh_requirements()
            ui.notify(f'Added "{new_text}"', type='positive')

    def remove_requirement(req_name):
        print(f"Removing requirement: {req_name}")
        # controller.remove_requirement(req)
        controller.requirements = [req for req in controller.requirements if req.reqname != req_name]
        ui.notify(f'Removed requirement', type='info')
        refresh_requirements()
       

    def toggle_requirement(req_name):
        print(f"Toggling requirement: {req_name}")
        for req in controller.requirements:
            if req.reqname == req_name:
                req.ismusthave = not req.ismusthave
                ui.notify(f'Updated status to {"Must-Have" if req.ismusthave else "Desirable"}', type='info')
                refresh_requirements()
                return
        ui.notify(f'Error updating requirement: {req_name}', type='negative')
            

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

    async def handle_send_to_backend():
        response = controller.send_to_backend()
        print("Raw response:", response)   
        response_data = EvaluateResponse(**response.json())
        new_requirements = response_data.updated_requirements
        print("new requirements : \n", new_requirements)
        controller.requirements = new_requirements
        candidates = response_data.candidates        
        refresh_requirements()
        refresh_candidates(candidates, new_requirements)

    
    with ui.row().classes('w-full h-screen flex flex-row'):
        # LEFT PANEL (fixed width)
        with ui.column().classes('flex-none w-96 h-full overflow-auto p-4 bg-gray-50 border-r'):
            with ui.expansion('File upload', icon='folder').classes('w-full'):
                with ui.card().classes('shadow-lg p-4 w-full'):
                    ui.label('Ladda upp fil').classes('text-lg font-bold')
                    ui.upload(on_upload=handle_jd_upload, auto_upload=True)

                with ui.card().classes('shadow-lg p-4 w-full mt-4'):
                    ui.label('Ladda upp flera filer').classes('text-lg font-bold')
                    ui.upload(on_multi_upload=handle_cv_upload, auto_upload=True, multiple=True)

                ui.button('Skicka till Backend', icon='send').classes(
                    'mt-4 bg-blue-500 text-white w-full'
                ).on('click', handle_send_to_backend)

            with ui.card().classes('shadow-lg p-4 w-full mt-4'):
                ui.label('Välj Shortlist Size').classes('text-lg font-bold')
                shortlist_size = ui.select(
                    options=[10, 20, 30, 40, 50],
                    value=20,
                    label='Antal kandidater'
                ).classes('w-full mt-2')

            with ui.card().classes('shadow-lg p-4 w-full mt-4'):
                ui.label('Lägg till krav').classes('text-lg font-bold')
                with ui.row().classes('w-full items-center mt-2'):
                    requirement_input = ui.input(placeholder='Skriv in ett krav...').classes('flex-grow')
                    is_must_have = ui.switch(value=False).classes('mx-2').props('color=green')
                    ui.label('Must-Have').classes('mr-4 text-sm text-green-700')
                    def handle_add():
                        add_requirement(requirement_input.value, is_must_have.value)
                        requirement_input.value = ''
                        requirement_input.update()
                    ui.button('Lägg till', on_click=handle_add).classes('bg-blue-500 text-white')
                requirements_container = ui.column().classes(
                    'mt-4 w-full border rounded p-2 min-h-[50px]'
                )
                refresh_requirements()

        # RIGHT MAIN CONTENT (flex-grow)
        with ui.column().classes('flex-grow h-full overflow-auto p-4'):
            with ui.card().classes('shadow-lg p-4 w-full h-full'):
                ui.label('Candidates').classes('text-lg font-bold mb-2')
                table = ui.table(columns=[], rows=[]).classes('w-full h-full')



ui.page('/')(main_page)
# ui.run(port=8005)