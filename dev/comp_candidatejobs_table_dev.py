from nicegui import ui
from typing import List, Dict
from datetime import date, timedelta
import sys, os
from typing import Dict, List, Set
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))
from nicegui import ui
from typing import List, Dict
from datetime import date
from backend.models import CandidateResultLong, RequirementResult
from nicegui import ui
from typing import List, Dict
import copy
import asyncio
from datetime import date
from niceGUI.api_fe import APIController, UploadController
import json


class CandidateJobsTable():
    def __init__(self, candidates: List[CandidateResultLong], callbacks):
        self.fictive_start_date = date(2025, 10, 1)
        # self.controller = API_client.controller
        # self.table = ui.table(columns=[], rows=[])
        self.on_status_change = callbacks["on_status_change"] 
        self.status_options = callbacks["status_options"]
        self.on_reeval = callbacks["on_reeval"]
        self.req_changed = False
        
        self.requirements = [
            {
                "reqname": r.reqname,
                "ismusthave": r.ismusthave,
                "source": r.source,
            }
            for r in candidates[0].requirements
        ]
        self.orig_requirements = copy.deepcopy(self.requirements)
        self._process_candidates(candidates)
        self._build_ui()

    async def get_api_candidates(self):
        candidates = await self.api_client.api_get_candidates_job()
        return candidates
        
    def _process_candidates(self, candidates):
        self.filter_section_expansion = None
        # starta async init   
        self.candidates_map = {c.candidate_id: c.dict(exclude_none=True) for c in candidates}
        self.candidates_list = []
        for cand in self.candidates_map.values():
            cand_copy = cand.copy()
            reqs = cand.get('requirements') or []   # <-- säkerhetskontroll
            cand_copy['musthave'] = [req for req in reqs if req['ismusthave']]
            cand_copy['desirable'] = [req for req in reqs if not req['ismusthave']]
            cand_copy['combined_score'] = round((cand_copy.get('combined_score', 0) * 100),0)
            self.candidates_list.append(cand_copy)
        
        self.original_candidates_list = self.candidates_list.copy()
        priority_fields = ["candidate_id", "name", "combined_score"]
        other_fields = [f for f in CandidateResultLong.__fields__ if f not in priority_fields and f != "requirements"]
        excluded_fields = ["available_from"]
        ordered_fields = [f for f in priority_fields + other_fields if f not in excluded_fields]
        # ordered_fields.append("job_availability")

        self.columns = [
            {
                "name": field,
                "label": field.replace("_", " ").capitalize() if field != "job_availability" else "Job Availability",
                "field": field,
                "sortable": True,
                "style": "max-width: 200px; white-space: normal; word-wrap: break-word;",
                "align": "left"
            }
            for field in ordered_fields
        ]
        self.columns.extend([
            {
                "name": "musthave",
                "label": "Must-have",
                "field": "musthave",
                "sortable": False,
                "style": "max-width: 250px; white-space: normal; word-wrap: break-word;",
                "align": "left"
            },
            {
                "name": "desirable",
                "label": "Desirable",
                "field": "desirable",
                "sortable": False,
                "style": "max-width: 250px; white-space: normal; word-wrap: break-word;",
                "align": "left"
            },
            {
                "name": "actions",
                "label": "",
                "field": "actions",
                "sortable": False,
                "align": "left"
            }
        ])

        self.musthave_req_names = sorted({
            req["reqname"] for cand in self.candidates_list for req in cand["musthave"]
        })
        self.desirable_req_names = sorted({
            req["reqname"] for cand in self.candidates_list for req in cand["desirable"]
        })
        self.filters: List[str] = []
        self.search_term = ""
        self.filter_section_expansion = None
        # Initialize visible columns (all except actions, which is always visible)
        self.visible_columns = [col["name"] for col in self.columns if col["name"] != "actions"]
        self.table = ui.table(
            columns=[],   # inga kolumner ännu
            rows=[],      # inga rader ännu
        )

    
    def _build_ui(self):
        with ui.row().classes('items-center w-full justify-between'):
            ui.label('Candidate Table').classes('text-1xl font-bold p-4')
            # ui.label(f'Job: {self.controller.job_id}, {self.controller.job_description} for {self.controller.customer}').classes('mr-2')
            COMMON = "w-64 text-sm [&_.q-field__label]:text-sm [&_.q-field__label]:font-small [&_.q-field__input]:text-sm [&_.q-field__native]:text-sm"
        
        self.filter_section_expansion = ui.expansion('REQUIREMENTS FILTER', icon='extension').classes('w-full font-bold')
        # with self.filter_section_expansion:
        self._rebuild_filters()
        self.table = ui.table(
            columns=[col for col in self.columns if col["name"] in self.visible_columns + ["actions"]],
            rows=self.candidates_list,
            row_key="candidate_id",
            pagination={'sortBy': 'combined_score', 'descending': True, 'rowsPerPage': 15}
        ).classes("table-fixed w-full max-w-full") #classes("w-full max-w-[1800px]")
        status_options = self.status_options
        print("status options: ", status_options)
        status_json = json.dumps(status_options)
        print(status_json)
        with self.table:
            self.table.add_slot('body', r'''
                <q-tr :props="props">
                    <q-td v-for="col in props.cols" :key="col.name" :props="props">
                        
                        <template v-if="col.name === 'combined_score'">
                            <q-badge
                                :color="props.row.combined_score >= 90 ? 'blue-2' : (props.row.combined_score >= 75 ? 'green-2' : (props.row.combined_score >= 60 ? 'yellow-2' : 'red-2'))"
                                class="q-pa-sm text-subtitle2 text-black" rounded
                            >
                                {{ props.row.combined_score }} %
                            </q-badge>
                        </template>

                        <template v-else-if="col.name === 'musthave' || col.name === 'desirable'">
                            <div class="flex flex-wrap gap-1">
                                <q-icon
                                    v-for="req in props.row[col.name]"
                                    :name="req.status === 'YES' ? 'check_circle' : req.status === 'NO' ? 'cancel' : 'help'"
                                    :color="req.status === 'YES' ? 'green' : req.status === 'NO' ? 'red' : 'yellow-8'"
                                    size="sm"
                                >
                                    <q-tooltip>{{ req.reqname }}: {{ req.status }}</q-tooltip>
                                </q-icon>
                            </div>
                        </template>

                        <template v-else-if="col.name === 'summary'">
                            <q-btn flat dense color="primary" 
                                :icon="props.expand ? 'keyboard_arrow_up' : 'keyboard_arrow_down'" 
                                :label="props.expand ? 'Hide' : 'Show summary'" 
                                @click="props.expand = !props.expand" />
                        </template>

                        <template v-else-if="col.name === 'actions'">
                            <q-btn dense flat round icon="more_vert">
                                <q-menu>
                                    <q-list style="min-width: 150px">
                                        <q-item clickable v-close-popup @click="$parent.$emit('menu_action', {action: 'details', row_id: props.row.candidate_id})">
                                            <q-item-section>Visa detaljer</q-item-section>
                                        </q-item>
                                        <q-item clickable v-close-popup @click="$parent.$emit('menu_action', {action: 'asas', row_id: props.row.candidate_id})">
                                            <q-item-section>VRedigera</q-item-section>
                                        </q-item>
                                        <q-item clickable v-close-popup @click="$parent.$emit('menu_action', {action: 'details', row_id: props.row.candidate_id})">
                                            <q-item-section>Visa Delete</q-item-section>
                                        </q-item>
                                        </q-list>
                                </q-menu>
                            </q-btn>
                        </template>
                        <template v-else-if="col.name === 'status'">
                            <q-select
                                dense
                                outlined
                                emit-value
                                map-options
                                :options="''' + str(status_options) + r'''"
                                v-model="props.row.status"
                                @update:model-value="$parent.$emit('status_change', {candidate_id: props.row.candidate_id, new_status: props.row.status})"
                                style="min-width: 130px"
                            />
                        </template>  
                        <template v-else>
                            {{ col.value }}
                        </template>
                        
                    </q-td>
                </q-tr>

                <q-tr v-show="props.expand" :props="props" class="bg-blue-grey-1">
                    <q-td colspan="100%">
                        <div class="q-pa-md" style="white-space: pre-wrap; max-width: 1200px;">
                            <div class="text-h6"></div>
                            {{ props.row.summary || 'No Summary available' }}
                        </div>
                    </q-td>
                </q-tr>
            ''')
            self.table.on('menu_action', self._on_action)
            self.table.on('status_change', self._on_status_change)
            self.table.on('rowClick', lambda e: print(f"Row clicked: {e.args}"))
            ui.add_head_html('''
                <script>
                function sortByAbsJobAvailability(props) {
                    const table = props.table;
                    table.sortBy = 'job_availability';
                    table.descending = props.sortBy === 'job_availability' ? !props.descending : false;
                    table.rows.sort((a, b) => {
                        const aVal = a.job_availability === 'N/A' ? Infinity : Math.abs(parseInt(a.job_availability));
                        const bVal = b.job_availability === 'N/A' ? Infinity : Math.abs(parseInt(b.job_availability));
                        return table.descending ? bVal - aVal : aVal - bVal;
                    });
                    table.$emit('update:pagination', { sortBy: 'job_availability', descending: table.descending });
                    table.$forceUpdate();
                }
                </script>
            ''')

    def _filter_by_availability(self, event):
        value = getattr(event, "value", event)
        print("Val:", value)

        if value == "Before":
            print("Ska filtrera på '-'")
            new_rows = [
                c.copy()
                for c in self.original_candidates_list
                if isinstance(c.get("available_in", ""), str) and "-" in c["available_in"]
            ]
            print(f"Antal filtrerade kandidater: {len(new_rows)}")
        else:
            print("Visar alla kandidater")
            new_rows = [c.copy() for c in self.original_candidates_list]

        self.table.rows = new_rows

        if hasattr(self.table, "refresh"):
            print("Använder refresh()")
            self.table.refresh()
        else:
            print("Använder update()")
            self.table.update()



    def _on_status_change(self, event):
        candidate_id = event.args['candidate_id']
        new_status = event.args['new_status']
        print(f"Kandidat {candidate_id} uppdaterad till ny status: {new_status}")
        # Här kan du lägga till API-anrop eller uppdatera datamodellen
        ui.notify(f"Status uppdaterad till {new_status}", type='info')


    def _on_action(self, event):
        """Handle events from the action menu."""
        print("--- _on_action triggered ---")
        print(f"Event args: {event.args}")
        payload = event.args
        action = payload.get('action')
        row_id = payload.get('row_id')

        row = self.candidates_map.get(row_id)
        if not row:
            print(f"Kunde inte hitta kandidat med ID: {row_id}")
            return

        candidate_name = row.get('name', 'Okänd')
        print(f"Action: {action} på kandidat: {candidate_name} (ID: {row_id})")

        if action == 'details':
            ui.notify(f"Visar detaljer för {candidate_name}, status options: {self.status_options}", type='info')
        elif action == 'edit':
            ui.notify(f"Redigerar {candidate_name}", type='warning')
        elif action == 'delete':
            ui.notify(f"Tar bort {candidate_name}", type='negative')

    def _update_columns(self, hidden_columns: List[str]):
        """Hide selected columns and refresh the table."""
        self.visible_columns = [col["name"] for col in self.columns if col["name"] not in hidden_columns and col["name"] != "actions"]
        self.table.columns = [col for col in self.columns if col["name"] in self.visible_columns + ["actions"]]
        self.table.update()
        print(f"Visible columns updated: {self.visible_columns}")

    def update(self, new_candidates: List[CandidateResultLong]):
        self.candidates_map = {c.candidate_id: c.dict(exclude_none=True) for c in new_candidates}
        self.candidates_list = []
        for cand in self.candidates_map.values():
            cand_copy = cand.copy()
            # ✅ säker hantering av krav
            cand_copy['musthave'] = [req for req in (cand.get('requirements') or []) if req.get('ismusthave')]
            cand_copy['desirable'] = [req for req in (cand.get('requirements') or []) if not req.get('ismusthave')]
            cand_copy['combined_score'] = round((cand_copy.get('combined_score', 0) * 100),0)
            self.candidates_list.append(cand_copy)

        self.musthave_req_names = sorted({  
            req["reqname"] for cand in self.candidates_list for req in cand["musthave"]
        })
        self.desirable_req_names = sorted({
            req["reqname"] for cand in self.candidates_list for req in cand["desirable"]
        })
        
        self.filters = []
        self.search_term = ""
        self.table.rows = self.candidates_list
        self.table.columns = [col for col in self.columns if col["name"] in self.visible_columns + ["actions"]]
        if self.filter_section_expansion:
            self._rebuild_filters()
        self.apply_filters()


    def _rebuild_filters(self):
    
        if self.filter_section_expansion:
            with self.filter_section_expansion:
                self.filter_section_expansion.clear()
                
                with ui.row().classes('w-full items-start justify-between gap-8'):
                    
                    # Vänster kolumn: Chips för Must-have och Desirable
                    with ui.column().classes('w-1/3 gap-6'):
                        ui.label("Must-have").classes("text-md font-semibold")
                        
                        with ui.row().classes('flex-wrap gap-2'):
                            for req_name in self.musthave_req_names:
                                ui.chip(req_name, removable=True, on_click=lambda e, rn=req_name: self._toggle_filter(rn)) \
                                    .props(f"color={'green' if req_name in self.filters else 'black'} outline") \
                                    .classes('cursor-pointer') \
                                    .on('remove', lambda rn=req_name: self._remove_filter(rn))
                                ui.switch(on_change=lambda rn=req_name: self._toggle_req(rn))

                        ui.label("Desirable").classes("text-md font-semibold mt-6")
                        
                        with ui.row().classes('flex-wrap gap-1'):
                            for req_name in self.desirable_req_names:
                                ui.chip(req_name, removable=True, on_click=lambda e, rn=req_name: self._toggle_filter(rn)) \
                                    .props(f"color={'green' if req_name in self.filters else 'black'} outline") \
                                    .classes('cursor-pointer') \
                                    .on('remove', lambda rn=req_name: self._remove_filter(rn))
                                ui.switch(on_change=lambda rn=req_name: self._toggle_req(rn))

                    # Höger kolumn: Tre kontroller under varandra
                    with ui.column().classes('w-1/3'):
                        # Rad 1: Add requirement (full bredd)
                        add_input = ui.input(
                            label='Add requirement'
                        ).classes('w-full') \
                        .on('keydown.enter', lambda e: self._add_requirement_chip(add_input.value))
                        with ui.row():
                            Reeval_button = (
                                ui.button('Re-evaluate', icon='send')
                                .classes('bg-blue-500 text-white')
                                .on('click', lambda e: self.re_evaluate())
                            )
                            Reeval_button.bind_enabled_from(self, 'req_changed')
                            eval_label = ui.label("Requirement changed, press to execute").classes('text-red-500')
                            eval_label.bind_visibility_from(self, 'req_changed')

                        # Rad 2: Search + Select på samma rad
                        with ui.row().classes('w-full gap-2 flex-nowrap'):
                            ui.input(
                                label="Search",
                                on_change=lambda e: self._update_search(e.value)
                            ).classes('w-1/2')

                            ui.select(
                                options=[col["name"] for col in self.columns if col["name"] != "actions"],
                                label="Hide/select Columns",
                                multiple=True,
                                on_change=lambda e: self._update_columns(e.value)
                            ).classes('w-1/2')
                        
        # print("filters:\n", self.filters)     
        self.apply_filters()
    
    async def re_evaluate(self, shortlist_size: int = 3):
        candidates = await self.on_reeval(self.requirements)
        print("nr of candidates: ", len(candidates))
        self.update(candidates)
        self.req_changed = False
        self.orig_requirements = copy.deepcopy(self.requirements)

    def _add_requirement_chip(self, req_name: str):
        print("in rebuild with new requiremet", req_name)
        self.musthave_req_names.append(req_name)
        new_req = {
                "reqname": req_name,
                "ismusthave": True,
                "source": "USER",
            }
        self.requirements.append(new_req)        
        self._rebuild_filters()
        print("reuirements:\n", self.requirements)
        self.req_changed = self.requirements != self.orig_requirements
        print("self requirements = ", self.requirements)
        print("self orig req = ", self.orig_requirements)

        if self.req_changed:
            print("ja de skiljer sig åt")
        self.apply_filters()

    def _toggle_req(self, req_name: str):
        print("in rebuild")
        print(req_name, "ska bytas")
        if req_name in self.musthave_req_names:
            self.musthave_req_names.remove(req_name)
            self.desirable_req_names.append(req_name)
        else:
            self.musthave_req_names.append(req_name)
            self.desirable_req_names.remove(req_name)
        for req in self.requirements:
            if req["reqname"] == req_name:
                req["ismusthave"] = not req["ismusthave"]
                
        print("reuirements:\n", self.requirements)
        self.req_changed = self.requirements != self.orig_requirements
        print("self requirements = ", self.requirements)
        print("self orig req = ", self.orig_requirements)
        
        if self.req_changed:
            print("ja de skiljer sig åt")

        self._rebuild_filters()
        self.apply_filters()

    def _toggle_filter(self, req_name: str):
        """Toggle a requirement filter and update chip color."""
        if req_name in self.filters:
            self.filters.remove(req_name)
        else:
            self.filters.append(req_name)
        # 
        self._rebuild_filters()
        self.apply_filters()

    def _remove_filter(self, req_name: str):
        print("in remove filter")
        if req_name in self.musthave_req_names:
            self.musthave_req_names.remove(req_name)
        if req_name in self.desirable_req_names:
            self.desirable_req_names.remove(req_name)
        self.requirements = [
            r for r in self.requirements
            if r["reqname"] != req_name
        ]
        self.req_changed = self.requirements != self.orig_requirements
        if self.req_changed:
            print("ja de skiljer sig åt")

        self._rebuild_filters()
        self.apply_filters()

    def _update_search(self, value: str):
        self.search_term = value.lower()
        self.apply_filters()

    def apply_filters(self):
        filtered_rows = []
        for cand in self.candidates_list:
            include = True
            reqs = cand.get("requirements") or []  # <-- fallback till tom lista
            for req_name in self.filters:
                req_status = next(
                    (req.get("status") for req in reqs if req.get("reqname") == req_name),
                    None
                )
                if req_status != "YES":
                    include = False
                    break

            if include and self.search_term:
                search_match = False
                for field in ['candidate_id', 'name', 'combined_score', 'assignment', 'location', 'years_exp', 'status', 'job_availability']:
                    if field in cand and self.search_term in str(cand[field]).lower():
                        search_match = True
                        break
                if not search_match:
                    include = False

            if include:
                filtered_rows.append(cand)

        self.table.rows = filtered_rows
        self.table.update()

