# app_state.py
from niceGUI.api_fe import APIController, UploadController

ui_controller = UploadController()
API_client = APIController(ui_controller)
