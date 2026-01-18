from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.components.comp_joblist import JobList
from niceGUI.app_state import API_client, ui_controller

@ui.page('/datavalidation')
async def datavalidation_page():
    drawer = LeftDrawer()
    ui.label('Printing variables in ui_controller:')
    for key, value in ui_controller.__dict__.items():
        ui.label(f"{key}: {value}")

    def clear_controller():
        ui_controller.__dict__.clear()
        ui.notify('Controller data raderad')
        
    ui.button('Erase  controller-data', on_click=clear_controller) 
   
