from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer

@ui.page('/')
def home_page():
    ui.label('Welcome to Harry - your AI-powered recruitment assistant').classes("text-xl")
    drawer = LeftDrawer()
    # Main content area
    with ui.column().classes("p-4"):
        ui.icon('smart_toy').classes('text-9xl text-blue-600 mb-4')
        ui.label("Swipe from the left or use the menu button to open the drawer.")