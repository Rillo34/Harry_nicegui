from nicegui import ui, events
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime, date
import uuid
import os
import sys
from faker import Faker
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from models import CandidatePayload, RequirementPayload, JobRequest
fake = Faker()


class FileUploadSection:
    def __init__(self, controller):
        self.controller = controller  # ✅ Spara controller som instansvariabel
        with ui.column().classes('w-1/3 p-4'):
            file_section_expansion = ui.expansion('FILE UPLOAD', icon='folder').classes('w-96 font-bold')
            with file_section_expansion:
                # Job description upload
                with ui.card().classes('shadow-lg p-4 w-96'):
                    ui.label('Upload JD').classes('text-sm font-medium')
                    ui.upload(on_upload=self.handle_jd_upload, auto_upload=True)
                # CV upload
                with ui.card().classes('shadow-lg p-4 w-96'):
                    ui.label('Upload CVs').classes('text-sm font-medium')
                    # ui.upload(on_multi_upload=self.handle_cv_upload, auto_upload=True, multiple=True)     
                    ui.upload(on_multi_upload=self.handle_cv_upload, auto_upload=True, multiple=True)   

    async def handle_jd_upload(self, e: events.UploadEventArguments):
        self.controller.uploaded_job_description = e
        ui.notify(f'Job description uploaded: {e.name}')
        print(f'Jobbeskrivning sparad: {e.name}')

    async def handle_cv_upload(self, e: events.MultiUploadEventArguments):
        cv_files = []
        cv_files = [
            ('cvs', (name, content, mime))
            for name, content, mime in zip(e.names, e.contents, e.types)
        ]
        self.controller.uploaded_cvs = cv_files
