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
        with ui.expansion('FILE UPLOAD', icon='folder').classes('w-96 font-bold'):
            with ui.card().classes('shadow-lg p-4 bg-gray-50 border border-gray-300 rounded'):
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.icon('folder').classes('text-lg text-blue-600')
                    ui.label('Upload Files').classes('text-md font-bold text-blue-800')

                with ui.column().classes('gap-4'):
                    # Job description upload
                    with ui.column().classes('border rounded p-3 bg-white'):
                        ui.label('Upload JD').classes('text-sm font-medium text-gray-700 mb-1')
                        ui.upload(on_upload=self.handle_jd_upload, auto_upload=True)

                    # CV upload
                    with ui.column().classes('border rounded p-3 bg-white'):
                        ui.label('Upload CVs').classes('text-sm font-medium text-gray-700 mb-1')
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
