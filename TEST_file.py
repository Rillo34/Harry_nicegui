from nicegui import events, ui
import api_fe
import uuid
import asyncio
import sys
import os
import comp_candidate_table1
from comp_requirements import RequirementSection
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from models import RequirementPayload, EvaluateResponse, CandidateResultLong, RequirementResult


controller = api_fe.UploadController()
list_of_cvs = []
# Initialize with sample data to test UI rendering
controller.requirements = []
list_of_requirements = []


def main_page():
    requirements_section = RequirementSection(controller, ui.card().classes('shadow-lg p-4 w-96 t-4'))  # Instantiate here


ui.page('/')(main_page)
ui.run(port=8005)
