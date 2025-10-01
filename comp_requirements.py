from nicegui import ui
from models import RequirementPayload

class RequirementSection:
    def __init__(self, controller):
        self.controller = controller
        # self.container = container
        self.list_of_requirements = []
        self._setup_ui()

    def _setup_ui(self):
        with ui.expansion('REQUIREMENT SECTION', icon='edit').classes('w-96 font-bold'):
            with ui.card().classes('shadow-lg p-4 bg-gray-50 border border-gray-300 rounded'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('edit').classes('text-lg text-black-3200')
                    ui.label('EDIT REQUIREMENTS').classes('text-md font-bold text-black-800')

                with ui.row().classes('w-full items-center mt-2'):
                    self.requirement_input = ui.input(placeholder='Type requirement...').classes('flex-grow')
                    self.is_must_have = ui.switch(value=False).classes('mx-2').props('color=green')
                    ui.label('Must-Have').classes('mr-4 text-sm text-green-700')
                    ui.button('Add requirement', on_click=self._handle_add).classes('bg-blue-500 text-white')

                self.requirements_container = ui.column().classes('mt-4 w-full border border-gray-300 rounded p-2 bg-white')
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
                # with ui.row().classes('w-full items-center border-b p-0 min-h-[32px]'):
                #     ui.switch(value=req.ismusthave, on_change=lambda e, r=req: self.toggle_requirement(r.reqname)).classes('mr-2').props('color=green')
                    
                #     ui.label('Must-Have' if req.ismusthave else 'Desirable').classes('mr-4 text-sm ' + ('text-green-700' if req.ismusthave else 'text-gray-500'))
                #     ui.button(icon='delete', on_click=lambda e, r=req: self.remove_requirement(r.reqname)).props('flat round size=sm color=red').classes('ml-auto')
                # ui.label(req.reqname).classes('flex-grow ' + ('text-green-700' if req.ismusthave else 'text-gray-600'))
                with ui.column().classes('w-full border-b p-0'):
                    with ui.row().classes('w-full items-center justify-between min-h-[32px]'):
                        # Vänster sida (toggle + label) i en egen row
                        with ui.row().classes('items-center gap-2'):
                            ui.switch(
                                value=req.ismusthave,
                                on_change=lambda e, r=req: self.toggle_requirement(r.reqname)
                            ).props('color=green')

                            ui.label(
                                'Must-Have' if req.ismusthave else 'Desirable'
                            ).classes(
                                'text-sm ' + ('text-green-700' if req.ismusthave else 'text-gray-500')
                            )

                        # Höger sida: delete-knappen
                        ui.button(
                            icon='delete',
                            on_click=lambda e, r=req: self.remove_requirement(r.reqname)
                        ).props('flat round size=sm color=red')

                    # Rad 2: själva namnet
                    ui.label(
                        req.reqname
                    ).classes(
                        'text-sm px-1 ' + ('text-green-700' if req.ismusthave else 'text-gray-600')
                    )