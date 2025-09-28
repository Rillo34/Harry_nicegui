from nicegui import ui
from models import RequirementPayload

class RequirementSection:
    def __init__(self, controller):
        self.controller = controller
        # self.container = container
        self.list_of_requirements = []
        self._setup_ui()

    def _setup_ui(self):
        with ui.card().classes('shadow-lg p-4 w-96 t-4'):         
            ui.label('Add requirements').classes('text-lg font-bold')
            with ui.row().classes('w-full items-center mt-2'):
                self.requirement_input = ui.input(placeholder='Skriv in ett krav...').classes('flex-grow')
                self.is_must_have = ui.switch(value=False).classes('mx-2').props('color=green')
                ui.label('Must-Have').classes('mr-4 text-sm text-green-700')
                ui.button('Lägg till', on_click=self._handle_add).classes('bg-blue-500 text-white')
            self.requirements_container = ui.column().classes('mt-4 w-full border rounded p-2 min-h-[50px]')
            self.refresh_requirements()

    def _handle_add(self):
        requirement = self.requirement_input.value.strip()
        if requirement:
            req = RequirementPayload(
                reqname=requirement,
                isActive=True,
                ismusthave=self.is_must_have.value,
                source="USER"
            )
            self.list_of_requirements.append(requirement)
            self.controller.add_requirement(req)
            self.refresh_requirements()
            ui.notify(f'Added "{requirement}"', type='positive')
            self.requirement_input.value = ''
            self.requirement_input.update()

    def remove_requirement(self, req_name):
        self.controller.requirements = [req for req in self.controller.requirements if req.reqname != req_name]
        ui.notify(f'Removed requirement', type='info')
        self.refresh_requirements()

    def toggle_requirement(self, req_name):
        for req in self.controller.requirements:
            if req.reqname == req_name:
                req.ismusthave = not req.ismusthave
                ui.notify(f'Updated status to {"Must-Have" if req.ismusthave else "Desirable"}', type='info')
                self.refresh_requirements()
                return
        ui.notify(f'Error updating requirement: {req_name}', type='negative')

    def refresh_requirements(self):
        print(f"Refreshing requirements: {len(self.controller.requirements)} items")
        self.requirements_container.clear()
        with self.requirements_container:
            # print("controllerns requirements: ", self.controller.requirements)
            for req in self.controller.requirements:
                # print(f"Rendering requirement: {req.reqname}, must_have={req.ismusthave}")
                with ui.row().classes('w-full items-center border-b p-1'):
                    ui.switch(value=req.ismusthave, on_change=lambda e, r=req: self.toggle_requirement(r.reqname)).classes('mr-2').props('color=green')
                    ui.label(req.reqname).classes('flex-grow ' + ('font-bold text-green-700' if req.ismusthave else 'text-gray-600'))
                    ui.label('Must-Have' if req.ismusthave else 'Desirable').classes('mr-4 text-sm ' + ('text-green-700' if req.ismusthave else 'text-gray-500'))
                    ui.button(icon='delete', on_click=lambda e, r=req: self.remove_requirement(r.reqname)).props('flat round size=sm color=red').classes('ml-auto')