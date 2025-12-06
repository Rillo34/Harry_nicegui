from nicegui import ui

class LeftDrawer:
    def __init__(self):
        # Left drawer (start closed, enable swipe via .props)
        drawer = ui.left_drawer(value=False).classes('bg-gray-100 w-64 p-4')
        drawer.props('swipe-open')  # enable swipe gesture
        with drawer:
            # ui.label('Navigation').classes('text-xl font-bold mb-4')
            ui.button('HOME', icon='home', on_click=lambda: ui.notify('HOME')).classes('w-full justify-start mb-2 text-md bg-orange text-black')
            ui.button('CandidateJob', icon='upload', on_click=lambda: ui.navigate.to('/candidatejobs')).classes('w-full justify-start mb-2 text-md')
            ui.button('Candidates', icon='people', on_click=lambda: ui.notify('Candidates')).classes('w-full justify-start mb-2 text-md')
            # ui.button('Jobs', icon='work', on_click=lambda: ui.notify('Jobs')).classes('w-full justify-start mb-2 text-md')
            ui.button('Jobs', icon='work', on_click=lambda: ui.navigate.to('/jobs')).classes('w-full justify-start mb-2 text-md')
            ui.button('Job automate', icon='work', on_click=lambda: ui.navigate.to('/jobs-automate')).classes('w-full justify-start mb-2 text-md')
            ui.button('Candidate Availability', icon='calendar_today', on_click=lambda: ui.notify('Candidate availability')).classes('w-full justify-start mb-2 text-md')
            ui.button('UC1 - Req Matrix', icon='file export', on_click=lambda: ui.navigate.to('/reqmatrix')).classes('w-full justify-start mb-2 text-md')
            ui.button('UC2 - Company profile and match', icon='enterprise', on_click=lambda: ui.navigate.to('/companyjobfit')).classes('w-full justify-start mb-2 text-md')
        
            ui.button('Pipeline', icon='schema', on_click=lambda: ui.notify('Pipeline')).classes('w-full justify-start mb-2 text-md')
            ui.button('Data Model', icon='account_tree', on_click=lambda: ui.navigate.to('/datamodel')).classes('w-full justify-start mb-2 text-md')
            ui.button('Dashboard', icon='dashboard', on_click=lambda: ui.notify('Dashboard')).classes('w-full justify-start mb-2 text-md')
            ui.button('Test Data', icon='manage', on_click=lambda: ui.notify('Test data')).classes('w-full justify-start mb-2 text-md')
            ui.button('Data validate', icon='data', on_click=lambda: ui.navigate.to('/datavalidation')).classes('w-full justify-start mb-2 text-md')
            

        # Top header with toggle button
        with ui.header().classes('bg-blue-600 text-white py-2 w-700'):
            with ui.row().classes('items-center'):
                ui.button(icon='menu', on_click=drawer.toggle).props('flat color=white')
                ui.label('Harry').classes('text-md font-medium ml-2')
        

#
