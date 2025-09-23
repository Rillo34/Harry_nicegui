from nicegui import ui
from comp_left_drawer import LeftDrawer


@ui.page('/')
def home_page():
    ui.label('Välkommen till startsidan!')
    drawer = LeftDrawer()
    # Top header with toggle button
    # with ui.header().classes('bg-blue-600 text-white py-2 w-700'):
    #     with ui.row().classes('items-center'):
    #         ui.button(icon='menu', on_click=drawer.toggle).props('flat color=white')
    #         ui.label('Harry').classes('text-lg font-medium ml-2')
    # Main content area
    # with ui.column().classes("p-4"):
    #     ui.image("Harry.jpg")
    #     ui.label("Welcome!").classes("text-xl")
    #     ui.label("Swipe from the left or use the menu button to open the drawer.")


# 
ui.run(port=8005)
