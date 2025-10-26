from nicegui import ui
import uuid

class Requirement:
    def __init__(self, text):
        self.id = str(uuid.uuid4())
        self.text = text
        self.must_have = False  # False = Desirable, True = Must-Have

requirements = [
    Requirement("Complete project proposal"),
    Requirement("Review documentation"),
    Requirement("Test application"),
]

def add_requirement():
    new_text = new_requirement_input.value.strip()
    if new_text:
        requirements.append(Requirement(new_text))
        new_requirement_input.value = ''
        refresh_list()

def delete_requirement(req_id):
    global requirements
    requirements = [req for req in requirements if req.id != req_id]
    refresh_list()

def toggle_requirement(req_id):
    for req in requirements:
        if req.id == req_id:
            req.must_have = not req.must_have
            break
    refresh_list()

def refresh_list():
    requirement_list.clear()
    with requirement_list:
        for req in requirements:
            with ui.card().classes('w-full'):
                with ui.row().classes('items-center w-full'):
                    ui.switch(value=req.must_have, on_change=lambda e, r=req: toggle_requirement(r.id)).classes('mr-2').props('color=green')
                    ui.label(req.text).classes('flex-grow ' + ('font-bold text-green-700' if req.must_have else 'text-gray-600'))
                    ui.label('Must-Have' if req.must_have else 'Desirable').classes('mr-4 text-sm ' + ('text-green-700' if req.must_have else 'text-gray-500'))
                    ui.button(icon='delete', color='red', on_click=lambda e, r=req: delete_requirement(r.id)).classes('ml-2')

ui.label('Requirements List').classes('text-2xl mb-4')

new_requirement_input = ui.input(placeholder='Enter new requirement').classes('w-full mb-4')
ui.button('Add Requirement', on_click=add_requirement).classes('mb-4')

requirement_list = ui.column().classes('w-full')

refresh_list()

ui.run(port=8001)