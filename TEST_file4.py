# NYTT ISOLERAT TEST
from nicegui import ui

class ControllerTest:
    def __init__(self):
        self.company_id = "Initial"
        # Lägg till all annan data som din riktiga controller har!

ctrl = ControllerTest()

@ui.page('/test')
def test_page():
    # Använd BARA EN BINDNING
    ui.label().bind_text(
        ctrl, 
        'company_id', 
        forward=lambda id: f"Company ID: {id}"
    ).classes('text-lg')

ui.run(port=8003)