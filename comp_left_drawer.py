from nicegui import ui

class LeftDrawer:
    def __init__(self):
        # Left drawer (start closed, enable swipe via .props)
        drawer = ui.left_drawer(value=False).classes('bg-gray-100 w-64 p-4')
        drawer.props('swipe-open')  # enable swipe gesture
        with drawer:
            # ui.label('Navigation').classes('text-xl font-bold mb-4')
            ui.button('HOME', icon='home', on_click=lambda: ui.notify('CandidateJob')).classes('w-full justify-start mb-2 text-lg bg-orange text-black')
            ui.button('CandidateJob', icon='upload', on_click=lambda: ui.navigate.to('/candidatejobs')).classes('w-full justify-start mb-2 text-lg')
            ui.button('Candidates', icon='people', on_click=lambda: ui.notify('Candidates')).classes('w-full justify-start mb-2 text-lg')
            # ui.button('Jobs', icon='work', on_click=lambda: ui.notify('Jobs')).classes('w-full justify-start mb-2 text-lg')
            ui.button('Jobs', icon='work', on_click=lambda: ui.navigate.to('/jobs')).classes('w-full justify-start mb-2 text-lg')
            ui.button('Pipeline', icon='schema', on_click=lambda: ui.notify('Pipeline')).classes('w-full justify-start mb-2 text-lg')
            ui.button('Data Model', icon='account_tree', on_click=lambda: ui.notify('Data Model')).classes('w-full justify-start mb-2 text-lg')
            ui.button('Dashboard', icon='dashboard', on_click=lambda: ui.notify('Dashboard')).classes('w-full justify-start mb-2 text-lg')
            ui.button('Test Data', icon='manage', on_click=lambda: ui.notify('Dashboard')).classes('w-full justify-start mb-2 text-lg')

        # Top header with toggle button
        with ui.header().classes('bg-blue-600 text-white py-2 w-700'):
            with ui.row().classes('items-center'):
                ui.button(icon='menu', on_click=drawer.toggle).props('flat color=white')
                ui.label('Harry').classes('text-lg font-medium ml-2')
        

#
