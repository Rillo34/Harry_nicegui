import sys
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel
from nicegui import ui

class JobCardCandidateJobs:
    def __init__(self, controller):
        self.controller = controller
        self._setup_ui()

    def _setup_ui(self):
        with ui.expansion('JOB', icon='work').classes('w-96 font-bold'):
            with ui.card().classes('shadow-lg p-4 bg-gray-50 border border-gray-300 rounded'):
            #    ui.label(f'ID: {self.controller.job_id}').classes('text-sm font-medium text-gray-700 mb-1')
            #    ui.label(f'State: {self.controller.job_state}').classes('text-sm font-medium text-gray-700 mb-1')
            #    ui.label(f'Cand status: {self.controller.highest_candidate_status}').classes('text-sm font-medium text-gray-700 mb-1')
            #    ui.label(f'Description: {self.controller.job_description}').classes('text-sm font-medium text-gray-700 mb-1')
            #    ui.label(f'Customer: {self.controller.customer}').classes('text-sm font-medium text-gray-700 mb-1')
               ui.label().bind_text_from(self.controller, 'customer', lambda v: f'Customer: {v}').classes('text-sm font-medium text-gray-700')
               ui.label().bind_text_from(self.controller, 'start_date', lambda v: f'Start: {v}').classes('text-sm font-medium text-gray-700')
               ui.label().bind_text_from(self.controller, 'job_state', lambda v: f'State: {v}').classes('text-sm font-medium text-gray-700')
               ui.label().bind_text_from(self.controller, 'highest_candidate_status', lambda v: f'Cand status: {v}').classes('text-sm font-medium text-gray-700')
               ui.label().bind_text_from(self.controller, 'job_description', lambda v: f'Description: {v}').classes('text-sm font-medium text-gray-700')

                