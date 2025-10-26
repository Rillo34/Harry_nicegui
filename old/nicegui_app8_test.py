from nicegui import events, ui
import api_fe
import uuid
import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from models import RequirementPayload, EvaluateResponse


controller = api_fe.UploadController()
list_of_cvs = []
# Initialize with sample data to test UI rendering
controller.requirements = []
list_of_requirements = []

def main_page():
    
    def refresh_candidates(candidates, requirements):
        print(f"Refreshing candidates: {len(candidates)} items")
        rows = []

        def format_with_icons(reqs, must_have=True):
            icon_map = {
                'YES': ('check_circle', 'green'),
                'MAYBE': ('help', 'orange'),
                'NO': ('cancel', 'red'),
            }
            html_rows = []
            for r in reqs:
                if r.ismusthave == must_have:
                    icon, color = icon_map.get(r.status, ('help', 'grey'))
                    html = '''
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
                    html_rows.append(html)
            return ''.join(html_rows)

        for c in candidates:
            row = {
                'Name': c.name,
                'Score': round(c.combined_score * 100),
                'Assignment': c.assignment,
                'Location': c.location,
                'Education': c.education,
                'Experience': c.years_exp,
                "Must-Have": format_with_icons(c.requirements or [], must_have=True),
                "Desirable": format_with_icons(c.requirements or [], must_have=False)
            }
            rows.append(row)

        columns = [{'name': key, 'label': key, 'field': key} for key in rows[0].keys()]
        table.columns = columns
        table.rows = rows
        table.update()

        # 🔧 Lägg till HTML-rendering för kravkolumner
        for col in ["Must-Have", "Desirable"]:
            table.add_slot(f'body-cell-{col}', f'''
            <q-td :props="props">
                <div v-html="props.row['{col}']"></div>
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
                reqname = new_text,
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
        file_section_expansion.expanded = False 
        file_section_expansion.update()
        candidates = response_data.candidates        
        if candidates:  # Check if candidates list is not empty
            refresh_requirements()
            refresh_candidates(candidates, new_requirements)
        else:
            ui.notify('No candidates returned from backend', type='warning')
            print("No candidates returned from backend")

        
    with ui.row().classes('w-full h-screen'):
        with ui.column().classes('w-96 p-4'):
            file_section_expansion = ui.expansion('File upload', icon='folder').classes('w-96')
            with file_section_expansion:
                # Job description upload
                with ui.card().classes('shadow-lg p-4 w-96'):
                    ui.label('Ladda upp fil').classes('text-lg font-bold')
                    ui.upload(on_upload=handle_jd_upload, auto_upload=True)

                # CV upload
                with ui.card().classes('shadow-lg p-4 w-96'):
                    ui.label('Ladda upp flera filer').classes('text-lg font-bold')
                    ui.upload(on_multi_upload=handle_cv_upload, auto_upload=True, multiple=True)

                # Send to backend button
                ui.button('Skicka till Backend', icon='send').classes('mt-4 bg-blue-500 text-white').on('click', handle_send_to_backend)

            # Shortlist size
            with ui.card().classes('shadow-lg p-4 w-96 mt-4'):
                ui.label('Välj Shortlist Size').classes('text-lg font-bold')
                shortlist_size = ui.select(
                    options=[10, 20, 30, 40, 50],
                    value=20,
                    label='Antal kandidater'
                ).classes('w-full mt-2')

            # Requirements list
            with ui.card().classes('shadow-lg p-4 w-96 mt-4'):
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
                requirements_container = ui.column().classes('mt-4 w-full border rounded p-2 min-h-[50px]')
                refresh_requirements()

        with ui.column().classes('w-400 p-4'):
            with ui.card().classes('shadow-lg p-4 w-full mt-4'):
                ui.label('Candidates').classes('text-lg font-bold mb-2')
                table = ui.table(columns=[], rows=[]).classes('w-full min-h-[200px]')
                table.add_slot('body-cell-name', r'''<q-td :props="props" v-html="props.value.replace(/\n/g, '<br>')" />''')
                table.add_slot('body-cell-Requirements', '''<q-td :props="props" v-html="props.value"></q-td>''')


ui.page('/')(main_page)
# ui.run(port=8005)
