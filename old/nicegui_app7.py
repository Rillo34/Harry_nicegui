from nicegui import events, ui
import api_fe
import uuid

controller = api_fe.UploadController()
list_of_cvs = []
requirements_list = []

class Requirement:
    def __init__(self, reqname, ismusthave=True):
        self.id = str(uuid.uuid4())
        self.reqname = reqname
        self.ismusthave = ismusthave

def main_page():
    # Define refresh_requirements with access to requirements_container
    def refresh_requirements():
        requirements_container.clear()
        with requirements_container:
            for req in requirements_list:
                with ui.row().classes('w-full items-center border-b p-1'):
                    ui.switch(value=req.ismusthave, on_change=lambda e, r=req: toggle_requirement(r.id)).classes('mr-2').props('color=green')
                    ui.label(req.reqname).classes('flex-grow ' + ('font-bold text-green-700' if req.ismusthave else 'text-gray-600'))
                    ui.label('Must-Have' if req.ismusthave else 'Desirable').classes('mr-4 text-sm ' + ('text-green-700' if req.ismusthave else 'text-gray-500'))
                    ui.button(icon='delete', on_click=lambda e, r=req: remove_requirement(r.id)).props('flat round size=sm color=red').classes('ml-auto')
            # controller.requirements = requirements_list

    def add_requirement(requirement):
        new_req = requirement.strip()
        print(new_req)
        if new_req:
            payload_data = {
                "reqname": new_req,
                "isActive": True,
                "ismusthave": True,  # Default to Must-Have
                "source": "USER"
            }
            controller.add_requirement(payload_data)
            refresh_requirements()

    def remove_requirement(req_id):
        global requirements_list
        requirements_list = [req for req in requirements_list if req.id != req_id]
        refresh_requirements()

    def toggle_requirement(req_id):
        for req in requirements_list:
            if req.id == req_id:
                req.ismusthave = not req.ismusthave
                break
        refresh_requirements()

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
            def handle_add():
                add_requirement(requirement_input.value)
                requirement_input.value = ''
                requirement_input.update()
            ui.button('Lägg till', on_click=handle_add).classes('bg-blue-500 text-white')
        requirements_container = ui.column().classes('mt-4 w-full border rounded p-2 min-h-[50px]')
        refresh_requirements()

def handle_jd_upload(e: events.UploadEventArguments):
    controller.uploaded_job_description = e
    ui.notify(f'Job description uploaded: {e.name}')
    print(f'Jobbeskrivning sparad: {e.name}')

def handle_cv_upload(e: events.MultiUploadEventArguments):
    cv_files = []
    for name, fileobj, mimetype in zip(e.names, e.contents, e.types):
        print("Filnamn:", name)
        print("Filobjekt:", fileobj)
        print("MIME-typ:", mimetype)
        print("Innehåll (första 100 bytes):", fileobj.read(100))
        fileobj.seek(0)
        print("---")
    cv_files = [
        ('cvs', (name, content, mime))
        for name, content, mime in zip(e.names, e.contents, e.types)
    ]
    controller.uploaded_cvs = cv_files

def handle_send_to_backend():
    success, message = controller.send_to_backend()
    ui.notify(message, color='green' if success else 'red')

ui.page('/')(main_page)
ui.run(port=8001)