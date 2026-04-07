from nicegui import ui
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import os
import sys
import json

# Assuming backend models are in a separate module
from backend.models import RequirementPayload, JobRequest

class JobList:
    def __init__(self, jobs, callbacks):
        job_objects = [JobRequest(**j) for j in jobs]
        self.on_status_change = callbacks["on_status_change"] 
        self.status_options = callbacks["status_options"]
        self.edit_job_callback = callbacks.get("edit_job")
        self.jobs_map = {j.job_id: j for j in job_objects}
        self.jobs_list = []
        self.hidden_columns = ["job_id"]

        # self.controller = ui.get_app_state().ui_controller

        for job in job_objects:
            job_dict = job.model_dump(exclude_none=False)
            job_dict['musthave'] = [r.model_dump(exclude_none=True) for r in job.requirements if r.ismusthave]
            job_dict['desirable'] = [r.model_dump(exclude_none=True) for r in job.requirements if not r.ismusthave]
            job_dict['expanded'] = False
            self.jobs_list.append(job_dict)
        print("--------------\nInitialized JobList with jobs:")  # Debug: Verify initialization
        print("Jobs list:", self.jobs_list)  # Debug: Verify jobs_list
        print("--------------")

        self.valid_states = ["1-Open", "2-In Progress", "3-Offered", "4-Contracted"]

        # self.preferred_column_order = [
        #     'job_id', 'customer', 'title', 'contact_person', 'start_date', 'end_date', 'job_hours', 'duration', 'due_date',
        #     'days_left', 'candidates', 'highest_candidate_status', 'assigned_to', 'state', 'details', 'actions'
        # ]
        exclude = { "musthave", "desirable", "description", "requirements", "expanded", "start_month", "end_month", "shortlist_size", "due_date", "assigned_to", "summary" }

        self.all_columns = [
            {
                "name": k,
                "label": k.replace("_", " ").title(),
                "field": k,
                "sortable": True,
                "align": "left",
            }
            for k in self.jobs_list[0].keys()
            if k not in exclude
        ]
        self.all_columns += [
            {"name": "details", "label": "Details", "field": "details", "sortable": False, "align": "center"},
            {"name": "actions", "label": "", "field": "actions", "sortable": False, "align": "center"},
        ]
        self.selected_columns = []
        self.columns = [col for col in self.all_columns if col['name'] not in self.hidden_columns]
        self._build_ui()
    
# -----------------------------
# API CALLS
# -----------------------------

    async def editing_job(self, row):
        print("row for contract dialog:", row)
        job_id = row.job_id if row else "new"
        def year_month_list(year: int): 
                return [f"{year}-{m:02d}" for m in range(1, 13)]

        def to_year_month(value):
            if value is None:
                return None
            if isinstance(value, (date, datetime)):
                return value.strftime("%Y-%m")
            if isinstance(value, str):
                return datetime.fromisoformat(value).strftime("%Y-%m")
            return None
        
        with ui.dialog() as dialog:
            job_title = row.title if row else "New Job"
            job_description= row.description if row else ""
            job_total_hours = row.total_hours if row else 100
            job_customer = row.customer if row else ""
            job_job_type = row.job_type if row else ""
            job_start_date = to_year_month(row.start_date) if row else None
            job_end_date = to_year_month(row.end_date) if row else None
            job_assigned_to = row.assigned_to if row else ""
            year_month_list = year_month_list(2025) + year_month_list(2026)
            async def save_and_close():
                data = {
                    "description": job_description.value,
                    "total_hours": job_total_hours.value,
                    "customer": job_customer.value,
                    "job_type": job_job_type.value,
                    "start_month": job_start_date.value,
                    "end_month": job_end_date.value,
                    "assigned_to": job_assigned_to.value,
                }
                await self.edit_job_callback(job_id, data)
                dialog.close()
            
            with ui.card().classes('p-4 w-96'):
                ui.label("Editing job").classes("text-lg font-bold mb-4")
                job_description = ui.input(
                    label="Job description",
                    value=job_description
                ).classes("w-full")
                job_customer = ui.input(
                    label="Customer",
                    value=job_customer
                ).classes("w-full")
                with ui.grid(columns=2).classes("w-full gap-2 mt-4"):
                    job_total_hours = ui.number(
                        label="Job hours",
                        value=job_total_hours,
                        step=10,
                        min=0
                    ).classes("w-full")
                    job_job_type = ui.select(
                        options=["permanent", "consulting"],  # Replace with actual job types
                        label="Job type",
                        value=job_job_type
                    ).classes("w-full")

                # Bättre layout för selects
                with ui.grid(columns=2).classes("w-full gap-2 mt-4"):
                    job_start_date = ui.select(
                        options=year_month_list,
                        label="Start month",
                        value=job_start_date
                    ).classes("w-full")
                    job_end_date = ui.select(
                        options=year_month_list,
                        label="End month",
                        value=job_end_date
                    ).classes("w-full")
                job_assigned_to = ui.input(
                    label="Assigned to",
                    value=job_assigned_to
                ).classes("w-full mt-4")
                # Knappar
                with ui.row().classes("justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close)
                    ui.button(
                        "Save",
                        on_click=lambda: save_and_close()
                    ).classes("bg-blue-500 text-white")
            dialog.open()


    def _build_ui(self):
        with ui.row().classes('items-center p-2').style('width: auto; background-color: #f5f5f5; border-radius: 8px;'):
            ui.label('Job List').style('width: 150px').classes('text-xl font-bold text-gray-800')
            search_input = ui.input(label='Search Jobs').props('clearable outlined dense').style('margin-left: 20px; width: 250px;')
            ui.select(
                [col['name'] for col in self.all_columns],
                multiple=True,
                label='Hide Columns',
                value=self.hidden_columns,
                on_change=self._update_columns
            ).props('outlined dense').style('margin-left: 20px; width: 250px;')

        self.table = ui.table(
            columns=[col for col in self.columns if col['name'] not in ['musthave', 'desirable']],
            rows=self.jobs_list if self.jobs_list else [{"job_id": "no-data", "title": "No jobs available", "customer": "", "days_left": "N/A"}],
            row_key="job_id",
            pagination={'sortBy': 'job_id', 'descending': False, 'rowsPerPage': 15}
        ).classes("table-fixed w-full max-w-full")

        self.table.bind_filter_from(search_input, 'value')
        status_options = self.status_options
        with self.table:
            
            self.table.add_slot(
                "body-cell-details",
                r'''
                <q-td :props="props" style="text-align: center;">
                    <q-btn dense flat round :icon="props.row.expanded ? 'expand_less' : 'expand_more'" color="primary" @click.stop="$parent.$emit('toggle_expand', props.row.job_id)" />
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
                                <div style="margin-bottom: 10px;">
                                    <strong>Summary:</strong>
                                    <div class="whitespace-normal break-words overflow-wrap-anywhere">
                                        {{ props.row.summary || 'None' }}
                                    </div>
                                </div>
                            </div>
                        </q-td>
                    </q-tr>
                '''
            )
            self.table.on('menu_action', self._on_action)
            self.table.on('status_change', self._on_status_change)
            self.table.on('rowClick', lambda e: print(f"Row clicked: {e.args}"))
            self.table.on('toggle_expand', self._on_toggle_expand)

    def update_jobs(self, new_jobs):
        print("\n\nUpdating jobs with new data:\n")  # Debug: Verify incoming data
        job_objects = [JobRequest(**j) for j in new_jobs]
        self.jobs_map = {j.job_id: j for j in job_objects}
        self.jobs_list = []
        for job in job_objects:
            job_dict = job.model_dump(exclude_none=False)
            job_dict['musthave'] = [r.model_dump(exclude_none=True) for r in job.requirements if r.ismusthave]
            job_dict['desirable'] = [r.model_dump(exclude_none=True) for r in job.requirements if not r.ismusthave]
            job_dict['expanded'] = False
            self.jobs_list.append(job_dict)
        print("Updated jobs list:", self.jobs_list)  # Debug: Verify updated jobs_list
        self.table.rows = self.jobs_list
        self.table.update()
    
    def _update_columns(self, e):
        self.hidden_columns = e.value if e.value else []
        self.columns = [
            col for col in self.all_columns
            if col['name'] not in self.hidden_columns
        ]
        self.table.columns = [col for col in self.columns if col['name'] not in ['musthave', 'desirable']]
        self.table.update()

    def _on_toggle_expand(self, event):
        job_id = event.args
        ui.notify(f"Toggling details for job_id: {job_id}")
        for row in self.table.rows:
            if row['job_id'] == job_id:
                row['expanded'] = not row['expanded']
                break
        self.table.update()

    async def _on_status_change(self, event):
        payload = event.args 
        print(payload)
        job_id = payload.get('job_id')
        job_state = payload.get('new_status')
        await self.on_status_change(job_id, job_state)

    async def _on_action(self, event):
        print("--- _on_action triggered ---")
        print(f"Event args: {event.args}")
        payload = event.args
        action = payload.get('action')
        row_id = payload.get('row_id')
        print("action:", action)
        print("row_id", row_id)
        row = self.jobs_map.get(row_id)
        print("job_id : ", row.job_id)
        if not row:
            print(f"Could not find job with ID: {row_id}")
            return
        print("Clicked on:", row)
        if action == 'candidatejob':
            # self.controller.job_id = row.job_id
            ui.navigate.to(f'/candidatejobs?job_id={row.job_id}')
            ui.notify(f"Navigating to candidate job {row.title}", type='info')
        elif action == 'edit':
            ui.notify(f"Editing {row.title}", type='info')
            await self.editing_job(row)
        elif action == 'delete':
            ui.notify(f"Deleting {row.title}", type='negative')
    


