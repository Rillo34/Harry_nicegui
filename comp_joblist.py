from nicegui import ui
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import os
import sys
from . import fe_testfile
import json

# Assuming backend models are in a separate module
from backend.models import RequirementPayload, JobRequest

class JobList:
    def __init__(self, jobs: List[dict], api_client):
        print("Initial jobs:", jobs)  # Debug: Verify input data
        job_objects = [JobRequest(**j) for j in jobs]
        self.jobs_map = {j.job_id: j for j in job_objects}
        self.jobs_list = []
        self.api_client = api_client
        self.controller = api_client.controller


        for job in job_objects:
            job_dict = job.model_dump(exclude_none=True)
            job_dict['musthave'] = [r.model_dump(exclude_none=True) for r in job.requirements if r.ismusthave]
            job_dict['desirable'] = [r.model_dump(exclude_none=True) for r in job.requirements if not r.ismusthave]
            if job.due_date:
                days_left = (job.due_date - date.today()).days
                job_dict['days_left'] = f"{days_left}d" if days_left >= 0 else f"{-days_left}d"
            else:
                job_dict['days_left'] = "N/A"
            job_dict['expanded'] = False
            # job_dict['status'] = job_dict.get('status', job_dict.get('state', '1-Open')) if job_dict.get('status', job_dict.get('state', '1-Open')) in ["1-Open", "2-In Progress", "3-Offered", "4-Contracted"] else "1-Open"
            self.jobs_list.append(job_dict)
        # print("Jobs list:", self.jobs_list)  # Debug: Verify jobs_list

        self.valid_states = ["1-Open", "2-In Progress", "3-Offered", "4-Contracted"]

        self.preferred_column_order = [
            'job_id', 'customer', 'title', 'contact_person', 'start_date', 'duration', 'due_date',
            'days_left', 'candidates', 'highest_candidate_status', 'assigned_to', 'state', 'details', 'actions'
        ]

        self.all_columns = [
            {"name": "job_id", "label": "Job ID", "field": "job_id", "sortable": True, "style": "max-width: 100px; white-space: nowrap;", "align": "left"},
            {"name": "customer", "label": "Customer", "field": "customer", "sortable": True, "style": "max-width: 150px; white-space: normal;", "align": "left"},
            {"name": "title", "label": "Title", "field": "title", "sortable": True, "style": "max-width: 200px; white-space: normal;", "align": "left"},
            {"name": "contact_person", "label": "Contact Person", "field": "contact_person", "sortable": True, "style": "max-width: 150px; white-space: normal;", "align": "left"},
            {"name": "start_date", "label": "Start Date", "field": "start_date", "sortable": True, "style": "max-width: 120px; white-space: nowrap;", "align": "left"},
            {"name": "duration", "label": "Duration", "field": "duration", "sortable": True, "style": "max-width: 100px; white-space: nowrap;", "align": "left"},
            {"name": "due_date", "label": "Due Date", "field": "due_date", "sortable": True, "style": "max-width: 120px; white-space: nowrap;", "align": "left"},
            {"name": "days_left", "label": "Days Left", "field": "days_left", "sortable": True, "style": "max-width: 100px; white-space: nowrap;", "align": "left"},
            {"name": "candidates", "label": "Candidates", "field": "candidates", "sortable": True, "style": "max-width: 100px; white-space: nowrap;", "align": "left"},
            {"name": "highest_candidate_status", "label": "Top Candidate Status", "field": "highest_candidate_status", "sortable": True, "style": "max-width: 150px; white-space: normal;", "align": "left"},
            {"name": "assigned_to", "label": "Assigned To", "field": "assigned_to", "sortable": True, "style": "max-width: 150px; white-space: normal;", "align": "left"},
            {"name": "state", "label": "State", "field": "state", "sortable": True, "style": "max-width: 130px; white-space: nowrap;", "align": "left"},
            {"name": "details", "label": "Details", "field": "details", "sortable": False, "style": "max-width: 100px;", "align": "center"},
            {"name": "actions", "label": "", "field": "actions", "sortable": False, "style": "width: 50px;", "align": "center"}
        ]

        self.selected_columns = []
        self.columns = [col for col in self.all_columns if col['name'] not in self.selected_columns]

        self._build_ui()

    def _build_ui(self):
        with ui.row().classes('items-center p-2').style('width: auto; background-color: #f5f5f5; border-radius: 8px;'):
            ui.label('Job List').style('width: 150px').classes('text-xl font-bold text-gray-800')
            search_input = ui.input(label='Search Jobs').props('clearable outlined dense').style('margin-left: 20px; width: 250px;')
            ui.select(
                [col['name'] for col in self.all_columns],
                multiple=True,
                label='Hide Columns',
                value=self.selected_columns,
                on_change=self._update_columns
            ).props('outlined dense').style('margin-left: 20px; width: 250px;')

        self.table = ui.table(
            columns=[col for col in self.columns if col['name'] not in ['musthave', 'desirable']],
            rows=self.jobs_list if self.jobs_list else [{"job_id": "no-data", "title": "No jobs available", "customer": "", "days_left": "N/A"}],
            row_key="job_id",
            pagination={'sortBy': 'job_id', 'descending': False, 'rowsPerPage': 15}
        ).classes("table-fixed w-full max-w-full")

        self.table.bind_filter_from(search_input, 'value')
        status_options = self.controller.job_states_name_list

        with self.table:
            
            self.table.add_slot(
                "body-cell-details",
                r'''
                <q-td :props="props" style="text-align: center;">
                    <q-btn dense flat round :icon="props.row.expanded ? 'expand_less' : 'expand_more'" color="primary" @click="$parent.$emit('toggle_expand', props.row.job_id)" />
                </q-td>
                '''
            )
            self.table.add_slot(
                "body",
                r'''
                <q-tr :props="props" class="hover:bg-gray-100">
                    <q-td v-for="col in props.cols" :key="col.name" :props="props" :style="col.style">
                        <template v-if="col.name === 'details'">
                            <q-btn dense flat round :icon="props.row.expanded ? 'expand_less' : 'expand_more'" color="primary" @click="$parent.$emit('toggle_expand', props.row.job_id)" />
                        </template>
                        <template v-else-if="col.name === 'actions'">
                            <q-btn dense flat round icon="more_vert" color="grey-7" size="sm">
                                <q-menu anchor="top right" self="top right">
                                    <q-list dense style="min-width: 150px">
                                        <q-item clickable v-close-popup
                                                @click="$parent.$emit('menu_action', {action: 'candidatejob', row_id: props.row.job_id})">
                                            <q-item-section>Candidate Job</q-item-section>
                                        </q-item>
                                        <q-item clickable v-close-popup
                                                @click="$parent.$emit('menu_action', {action: 'edit', row_id: props.row.job_id})">
                                            <q-item-section>Edit/Details</q-item-section>
                                        </q-item>
                                        <q-item clickable v-close-popup
                                                @click="$parent.$emit('menu_action', {action: 'delete', row_id: props.row.job_id})">
                                            <q-item-section>Delete</q-item-section>
                                        </q-item>
                                    </q-list>
                                </q-menu>
                            </q-btn>
                        </template>
                        <template v-else-if="col.name === 'days_left'">
                            <span :style="props.row.days_left === 'N/A' ? '' : (parseInt(props.row.days_left) < 0 ? 'color: red; font-weight: bold;' : parseInt(props.row.days_left) < 7 ? 'color: orange; font-weight: bold;' : 'color: green; font-weight: bold;')">
                                {{ props.row.days_left || 'N/A' }}
                            </span>
                        </template>
                        <template v-else-if="col.name === 'state'">
                            <q-select dense outlined
                                v-model="props.row.state"
                                :options="''' + str(status_options) + r'''"                  
                                @update:model-value="$parent.$emit('status_change', {job_id: props.row.job_id, new_status: props.row.state})"
                                style="min-width: 150px"
                            />
                        </template>                        
                        <template v-else>
                            {{ props.row[col.field] || 'N/A' }}
                        </template>

                    </q-tr>
                    <q-tr v-if="props.row.expanded" :props="props">
                        <q-td :colspan="props.cols.length" style="padding: 0;">
                            <div class="q-pa-md" style="font-size: 14px; line-height: 1.6; width: 100%; background-color: #fafafa; border-top: 1px solid #e0e0e0; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);">
                                <div style="margin-bottom: 10px;"><strong>Description:</strong> {{ props.row.description || 'None' }}</div>
                                <div style="margin-bottom: 10px;"><strong>Must-Have Requirements:</strong></div>
                                <ul style="margin: 0 0 10px 20px; padding: 0; list-style-type: disc;">
                                    <li v-for="req in props.row.musthave" :key="req.reqname" style="margin-bottom: 5px;">
                                        {{ req.reqname }}
                                    </li>
                                    <li v-if="!props.row.musthave || !props.row.musthave.length">None</li>
                                </ul>
                                <div style="margin-bottom: 10px;"><strong>Desirable Requirements:</strong></div>
                                <ul style="margin: 0 0 10px 20px; padding: 0; list-style-type: disc;">
                                    <li v-for="req in props.row.desirable" :key="req.reqname" style="margin-bottom: 5px;">
                                        {{ req.reqname }}
                                    </li>
                                    <li v-if="!props.row.desirable || !props.row.desirable.length">None</li>
                                </ul>
                            </div>
                        </q-td>
                    </q-tr>
                '''
            )
            self.table.on('menu_action', self._on_action)
            self.table.on('toggle_expand', self._on_toggle_expand)
            self.table.on('status_change', self._on_status_change)
            self.table.on('rowClick', lambda e: print(f"Row clicked: {e.args}"))

    def _update_columns(self, e):
        self.selected_columns = e.value if e.value else []
        self.columns = [
            col for col in self.all_columns
            if col['name'] not in self.selected_columns
        ]
        self.columns = sorted(
            self.columns,
            key=lambda col: self.preferred_column_order.index(col['name']) if col['name'] in self.preferred_column_order else len(self.preferred_column_order)
        )
        self.table.columns = [col for col in self.columns if col['name'] not in ['musthave', 'desirable']]
        self.table.update()

    def _on_toggle_expand(self, event):
        job_id = event.args
        print(f"Toggle expand for job_id: {job_id}")
        for job in self.jobs_list:
            if job['job_id'] == job_id:
                job['expanded'] = not job['expanded']
                break
        print(f"Jobs list after toggle: {self.jobs_list}")
        self.table.update()

    async def _on_status_change(self, event):
        payload = event.args 
        print(payload)
        self.controller.job_id = payload.get('job_id')
        self.controller.job_state = payload.get('new_status')
        await self.api_client.api_post_job_status_update()
        print(f"Status updated for job_id: {self.controller.job_id} to {self.controller.job_state}")

    def _on_action(self, event):
        print("--- _on_action triggered ---")
        print(f"Event args: {event.args}")
        payload = event.args
        action = payload.get('action')
        row_id = payload.get('row_id')
        row = self.jobs_map.get(row_id)
        if not row:
            print(f"Could not find job with ID: {row_id}")
            return
        print("Clicked on:", row)
        if action == 'candidatejob':
            self.controller.job_id = row.job_id
            ui.navigate.to(f'/candidatejobs?job_id={row.job_id}')
            ui.notify(f"Navigating to candidate job {row.title}", type='info')
        elif action == 'edit':
            ui.notify(f"Editing {row.title}", type='warning')
        elif action == 'delete':
            ui.notify(f"Deleting {row.title}", type='negative')

# @ui.page('/')
# def main_page():
#     initial_jobs = fe_testfile.get_jobrequest()
#     print("Initial jobs from fe_testfile:", initial_jobs)
#     if not initial_jobs:
#         ui.label("No jobs available").classes("text-red-500")
#     JobList(jobs=initial_jobs)
#     status_options = ['1-Open', '2-In Progress', '3-Offered', '4-Contracted']
#     ui.select(options=status_options, label='Test dropdown')  # ← Testa 

# ui.run(port=8005, reload=False)