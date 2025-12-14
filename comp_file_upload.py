from nicegui import ui, events
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime, date
import uuid
import os
import sys
from faker import Faker
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from backend.models import CandidatePayload, RequirementPayload, JobRequest
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


class ReqMatrixUploadSection:
    def __init__(self, api_client):
        self.api_client = api_client   # ✅ spara på instansen
        # with ui.expansion('FILE UPLOAD', icon='folder').classes('w-96 font-bold'):
        with ui.card().classes('shadow-lg p-4 bg-gray-50 border border-gray-300 rounded'):

            ui.label('Upload Requirement Matrix').classes('text-sm font-medium text-gray-700 mb-1')
            ui.upload(on_upload=self.handle_rm_upload, auto_upload=True)
            ui.label('Upload CV').classes('text-sm font-medium text-gray-700 mb-1')
            ui.upload(on_upload=self.handle_cv_upload, auto_upload=True)
            Eval_button = ui.button('Populate matrix', icon='send') \
                .classes('mt-4 bg-blue-500 text-white') \
                .on('click', lambda e: self.populate_req_matrix())

            # ui.label('Upload CVs to match matrix').classes('text-sm font-medium text-gray-700 mb-1')
            # ui.upload(on_multi_upload=self.handle_cv_upload, auto_upload=True, multiple=True)
                    
    async def handle_rm_upload(self, e: events.UploadEventArguments):
        self.api_client.controller.uploaded_req_matrix = e
        ui.notify(f'req_matrix uploaded: {e.name}')
    
    async def handle_cv_upload(self, e: events.MultiUploadEventArguments):
        self.api_client.controller.uploaded_cvs_req_matrix = e
        ui.notify(f'cv uploaded: {e.name}')
    
    async def populate_req_matrix(self):
        print("skickar till fylla i")
        resultat = await self.api_client.requirement_matrix_eval()
        ui.label('Uploaded {resultat}').classes('text-sm font-medium text-gray-700 mb-1')



    # async def handle_cv_upload(self, e: events.MultiUploadEventArguments):
    #     cv_files = []
    #     cv_files = [
    #         ('cvs', (name, content, mime))
    #         for name, content, mime in zip(e.names, e.contents, e.types)
    #     ]
    #     self.controller.uploaded_cvs_req_matrix = cv_files
