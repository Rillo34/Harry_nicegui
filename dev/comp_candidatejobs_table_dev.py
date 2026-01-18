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
import asyncio
from datetime import date
from niceGUI.api_fe import APIController, UploadController

class CandidateJobsTable():
    def __init__(self, API_client, candidates: List[CandidateResultLong]):
        self.fictive_start_date = date(2025, 10, 1)
        self.api_client = API_client
        self.controller = API_client.controller
        self.table = ui.table(columns=[], rows=[])
        self._process_candidates(candidates)
        self._build_ui()

    async def get_api_candidates(self):
        candidates = await self.api_client.api_get_candidates_job()
        return candidates
        
    def _process_candidates(self, candidates):
        self.filter_section_expansion = None
        # starta async init   
        print("candidates: ", candidates)
        self.candidates_map = {c.candidate_id: c.dict(exclude_none=True) for c in candidates}
        self.candidates_list = []
        for cand in self.candidates_map.values():
            cand_copy = cand.copy()
            cand_copy['musthave'] = [req for req in cand['requirements'] if req['ismusthave']]
            cand_copy['desirable'] = [req for req in cand['requirements'] if not req['ismusthave']]
            cand_copy['combined_score'] = f"{cand_copy['combined_score'] * 100:.0f}"
            if cand_copy.get('available_from'):
                days = (cand_copy['available_from'] - self.fictive_start_date).days
                cand_copy['job_availability'] = f"{days}d"
            else:
                cand_copy['job_availability'] = "N/A"
            self.candidates_list.append(cand_copy)
        
        self.original_candidates_list = self.candidates_list.copy()
        
        print(f"Job_availability values: {[cand['job_availability'] for cand in self.candidates_list]}")

        priority_fields = ["candidate_id", "name", "combined_score"]
        other_fields = [f for f in CandidateResultLong.__fields__ if f not in priority_fields and f != "requirements"]
        excluded_fields = ["education", "summary"]
        ordered_fields = [f for f in priority_fields + other_fields if f not in excluded_fields]
        ordered_fields.append("job_availability")

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
            ui.label(f'Job: {self.controller.job_id}, {self.controller.job_description} for {self.controller.customer}').classes('mr-2')
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

        with self.table:
            self.table.add_slot('body-cell-combined_score', r'''
                <q-td :props="props" class="text-center">
                    <q-badge
                        :color="
                            props.row.combined_score >= 90 ? 'blue-2' :
                            (props.row.combined_score >= 75 ? 'green-2' :
                            (props.row.combined_score >= 60 ? 'yellow-2' : 'red-2'))
                        "
                        class="q-pa-sm text-subtitle2 text-black"
                        rounded
                    >
                        {{ props.row.combined_score }} %
                    </q-badge>
                </q-td>
                ''')
            self.table.add_slot('body-cell-availability', r'''
                <q-td :props="props" class="text-center">
                    <q-badge
                        :color="
                            props.row.availability === 'EXCELLENT' ? 'blue' :
                            props.row.availability === 'GOOD' ? 'green' :
                            props.row.availability === 'OK' ? 'orange' :
                            'red'
                        "
                        class="shadow-2"
                        style="
                            font-size: 14px;
                            padding: 4px 8px;
                            line-height: 1;
                            min-width: 60px;
                            justify-content: center;
                        "
                        rounded
                    >
                        {{ props.row.availability }}
                    </q-badge>
                </q-td>
                ''')
            self.table.add_slot(
                "body-cell-musthave",
                r'''
                <q-td :props="props">
                    <div class="flex flex-wrap gap-1">
                        <q-icon
                            v-for="req in props.row.musthave"
                            :name="req.status === 'YES' ? 'check_circle' : req.status === 'NO' ? 'cancel' : 'help'"
                            :color="req.status === 'YES' ? 'green' : req.status === 'NO' ? 'red' : 'yellow-8'"
                            size="sm"
                        >
                            <q-tooltip>{{ req.reqname }}: {{ req.status }}</q-tooltip>
                        </q-icon>
                    </div>
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-desirable",
                r'''
                <q-td :props="props">
                    <div class="flex flex-wrap gap-1">
                        <q-icon
                            v-for="req in props.row.desirable"
                            :name="req.status === 'YES' ? 'check_circle' : req.status === 'NO' ? 'cancel' : 'help'"
                            :color="req.status === 'YES' ? 'green' : req.status === 'NO' ? 'red' : 'yellow-8'"
                            size="sm"
                        >
                            <q-tooltip>{{ req.reqname }}: {{ req.status }}</q-tooltip>
                        </q-icon>
                    </div>
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-actions",
                r'''
                <q-td :props="props">
                    <q-btn dense flat round icon="more_vert">
                        <q-menu>
                            <q-list style="min-width: 150px">
                                <q-item clickable v-close-popup
                                        @click="console.log('Emitting details for ' + props.row.candidate_id); $parent.$emit('menu_action', {action: 'details', row_id: props.row.candidate_id})">
                                    <q-item-section>Visa detaljer</q-item-section>
                                </q-item>
                                <q-item clickable v-close-popup
                                        @click="console.log('Emitting edit for ' + props.row.candidate_id); $parent.$emit('menu_action', {action: 'edit', row_id: props.row.candidate_id})">
                                    <q-item-section>Redigera</q-item-section>
                                </q-item>
                                <q-item clickable v-close-popup
                                        @click="console.log('Emitting delete for ' + props.row.candidate_id); $parent.$emit('menu_action', {action: 'delete', row_id: props.row.candidate_id})">
                                    <q-item-section>Ta bort</q-item-section>
                                </q-list>
                        </q-menu>
                    </q-btn>
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-status",
                r'''
                <q-td :props="props">
                    <q-select
                        dense
                        outlined
                        emit-value
                        map-options
                        :options="['Applied', 'Screened', 'Interviewed', 'Offered', 'Hired']"
                        v-model="props.row.status"
                        @update:model-value="$parent.$emit('status_change', {candidate_id: props.row.candidate_id, new_status: props.row.status})"
                        style="min-width: 130px"
                    />
                </q-td>
                '''
            )
            self.table.add_slot(
                "header-cell-job_availability",
                r'''
                <q-th :props="props">
                    <q-btn flat dense @click="sortByAbsJobAvailability(props)">
                        {{ props.col.label }}
                        <q-icon v-if="props.sortBy === 'job_availability' && props.descending" name="arrow_drop_down" />
                        <q-icon v-if="props.sortBy === 'job_availability' && !props.descending" name="arrow_drop_up" />
                    </q-btn>
                </q-th>
                '''
            )
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
            ui.notify(f"Visar detaljer för {candidate_name}", type='info')
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
        """Update the table with new candidates, refreshing data and UI."""
        self.candidates_map = {c.candidate_id: c.dict(exclude_none=True) for c in new_candidates}
        self.candidates_list = []
        for cand in self.candidates_map.values():
            cand_copy = cand.copy()
            cand_copy['musthave'] = [req for req in cand['requirements'] if req['ismusthave']]
            cand_copy['desirable'] = [req for req in cand['requirements'] if not req['ismusthave']]
            cand_copy['combined_score'] = f"{cand_copy['combined_score'] * 100:.0f}%"
            if cand_copy.get('available_from'):
                days = (cand_copy['available_from'] - self.fictive_start_date).days
                cand_copy['job_availability'] = f"{days}d"
            else:
                cand_copy['job_availability'] = "N/A"
            self.candidates_list.append(cand_copy)

        print(f"Updated job_availability values: {[cand['job_availability'] for cand in self.candidates_list]}")
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
                                    .props(f"color={'green' if req_name in self.filters else 'grey'} outline") \
                                    .classes('cursor-pointer') \
                                    .on('remove', lambda rn=req_name: self._remove_filter(rn))
                                ui.switch(on_change=lambda rn=req_name: self._toggle_req(rn))

                        ui.label("Desirable").classes("text-md font-semibold mt-6")
                        
                        with ui.row().classes('flex-wrap gap-2'):
                            for req_name in self.desirable_req_names:
                                ui.chip(req_name, removable=True, on_click=lambda e, rn=req_name: self._toggle_filter(rn)) \
                                    .props(f"color={'green' if req_name in self.filters else 'grey'} outline") \
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
                        Reeval_button = (
                            ui.button('Re-evaluate', icon='send')
                            .classes('bg-blue-500 text-white')
                            .on('click', lambda e: self.re_evaluate())
                            .props('enabled')
                        )

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
                        
             
        self.apply_filters()
    
    async def re_evaluate(self, shortlist_size: int = 3):
        print("in re_evaluate")
        self.controller.shortlist_size = shortlist_size
        self.controller.requirements = self.musthave_req_names + self.desirable_req_names
        candidates = await self.api_client.api_reevaluate()
        print("nr of candidates: ", len(candidates))
        self.table.update(candidates)
        ui.notify(f"Updated with {len(candidates)} candidates")

    def _add_requirement_chip(self, req_name: str):
        print("in rebuild", req_name)
        self.musthave_req_names.append(req_name)
        self._rebuild_filters()
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

        self._rebuild_filters()
        self.apply_filters()

    def _toggle_filter(self, req_name: str):
        """Toggle a requirement filter and update chip color."""
        if req_name in self.filters:
            self.filters.remove(req_name)
        else:
            self.filters.append(req_name)
        self._rebuild_filters()
        self.apply_filters()

    def _remove_filter(self, req_name: str):
        """Toggle a requirement filter and update chip color."""
        print("in remove")
        self.musthave_req_names.remove(req_name)
        self._rebuild_filters()
        self.apply_filters()


    def _update_search(self, value: str):
        self.search_term = value.lower()
        self.apply_filters()

    def apply_filters(self):
        filtered_rows = []
        for cand in self.candidates_list:
            include = True
            for req_name in self.filters:
                req_status = next(
                    (req["status"] for req in cand["requirements"] if req["reqname"] == req_name), None
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
        
        # print(f"Filtered rows: {[cand['name'] for cand in filtered_rows]}")
        self.table.rows = filtered_rows
        self.table.update()

def get_initial_data() -> List[CandidateResultLong]:
    fake_candidates = [
    {
        "candidate_id": "CAND_001",
        "name": "Alice Andersson",
        "assignment": "Backend Developer",
        "years_exp": "5",
        "location": "Stockholm",
        "education": "MSc Computer Science",
        "internal": False,
        "available_from": date.today() + timedelta(days=30),
        "combined_score": 0.82,
        "summary": "Strong backend profile with solid Python and API experience.",
        "availability": "EXCELLENT",
        "requirements": [
            {"reqname": "Python", "status": "YES", "ismusthave": True, "source": "JD"},
            {"reqname": "Django", "status": "MAYBE", "ismusthave": False, "source": "USER"},
            {"reqname": "REST APIs", "status": "MAYBE", "ismusthave": True, "source": "JD"},
        ],
        "status": "Shortlisted",
    },
    {
        "candidate_id": "CAND_002",
        "name": "Björn Berg",
        "assignment": "Frontend Developer",
        "years_exp": "3",
        "location": "Göteborg",
        "education": "BSc Information Technology",
        "internal": True,
        "available_from": date.today() + timedelta(days=14),
        "combined_score": 0.74,
        "summary": "Good React skills, some gaps in TypeScript.",
        "availability": "GOOD",
        "requirements": [
            {"reqname": "Python", "status": "NO", "ismusthave": True, "source": "JD"},
            {"reqname": "Django", "status": "MAYBE", "ismusthave": False, "source": "USER"},
            {"reqname": "REST APIs", "status": "YES", "ismusthave": True, "source": "JD"},
        ],
        "status": "Consider",
    },
    {
        "candidate_id": "CAND_003",
        "name": "Carla Carlsson",
        "assignment": "Data Scientist",
        "years_exp": "6",
        "location": "Malmö",
        "education": "PhD Statistics",
        "internal": False,
        "available_from": date.today() + timedelta(days=60),
        "combined_score": 0.88,
        "summary": "Excellent ML background, strong in Python and statistics.",
        "availability": "OK",
        "requirements": [
            {"reqname": "Python", "status": "YES", "ismusthave": True, "source": "JD"},
            {"reqname": "Django", "status": "NO", "ismusthave": False, "source": "USER"},
            {"reqname": "REST APIs", "status": "YES", "ismusthave": True, "source": "JD"},
        ],
        "status": "Shortlisted",
    },
    {
        "candidate_id": "CAND_004",
        "name": "David Dahl",
        "assignment": "DevOps Engineer",
        "years_exp": "4",
        "location": "Uppsala",
        "education": "BSc Systems Engineering",
        "internal": True,
        "available_from": date.today() + timedelta(days=7),
        "combined_score": 0.69,
        "summary": "Solid CI/CD knowledge, limited cloud exposure.",
        "availability": "POOR",
        "requirements": [
            {"reqname": "Python", "status": "YES", "ismusthave": True, "source": "JD"},
            {"reqname": "Django", "status": "MAYBE", "ismusthave": False, "source": "USER"},
            {"reqname": "REST APIs", "status": "NO", "ismusthave": True, "source": "JD"},
        ],
        "status": "Consider",
    },
    {
        "candidate_id": "CAND_005",
        "name": "Eva Ek",
        "assignment": "Project Manager",
        "years_exp": "10",
        "location": "Stockholm",
        "education": "MBA",
        "internal": False,
        "available_from": date.today() + timedelta(days=90),
        "combined_score": 0.77,
        "summary": "Experienced PM with agile background.",
        "availability": "OK",
        "requirements": [
            {"reqname": "Python", "status": "YES", "ismusthave": True, "source": "JD"},
            {"reqname": "Django", "status": "MAYBE", "ismusthave": False, "source": "USER"},
            {"reqname": "REST APIs", "status": "YES", "ismusthave": True, "source": "JD"},
        ],
        "status": "Shortlisted",
    }
]
    return [CandidateResultLong(**cand) for cand in fake_candidates] 


@ui.page('/')
def main_page():
    initial_candidates = get_initial_data()
#     the_candidates = [CandidateResultLong(**cand) for cand in initial_candidates]
#     table = CandidateJobsTable(candidates=the_candidates)
#     # input("get new candidates")
#     # new_candidates =get_new_dummy_data()
#     # table.update(new_candidates)

# ui.run(port=8004, reload=True)