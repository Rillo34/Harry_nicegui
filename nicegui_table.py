import sys
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel
from nicegui import ui

# --- Del 1: Nödvändiga modeller ---
class RequirementResult(BaseModel):
    reqname: str
    status: str
    ismusthave: bool
    source: str

class CandidateResultLong(BaseModel):
    candidate_id: str
    name: str
    combined_score: float
    summary: str
    assignment: str
    location: str
    internal: bool
    years_exp: str
    education: str
    requirements: List[RequirementResult]

# --- Del 2: CandidateTable-klass (med update-metod och musthave/desirable) ---
class CandidateTable:
    def __init__(self, candidates: List[CandidateResultLong]):
        self.candidates_map = {c.candidate_id: c.dict(exclude_none=True) for c in candidates}
        self.candidates_list = []
        for cand in self.candidates_map.values():
            cand_copy = cand.copy()
            cand_copy['musthave'] = [req for req in cand['requirements'] if req['ismusthave']]
            cand_copy['desirable'] = [req for req in cand['requirements'] if not req['ismusthave']]
            self.candidates_list.append(cand_copy)
        
        self.columns = [
            {
                "name": field,
                "label": field.replace("_", " ").capitalize(),
                "field": field,
                "sortable": True,
                "style": "max-width: 200px; white-space: normal; word-wrap: break-word;"
            }
            for field in CandidateResultLong.__fields__.keys() if field != 'requirements'
        ]
        self.columns.extend([
            {
                "name": "musthave",
                "label": "Must-have",
                "field": "musthave",
                "sortable": False
            },
            {
                "name": "desirable",
                "label": "Desirable",
                "field": "desirable",
                "sortable": False
            },
            {
                "name": "actions",
                "label": "",
                "field": "actions",
                "sortable": False
            }
        ])

        self.req_names: List[str] = sorted({
            req["reqname"]
            for cand in self.candidates_list
            for req in cand["requirements"]
        })
        self.filters: Dict[str, List[str]] = {req_name: [] for req_name in self.req_names}
        self._build_ui()

    def _build_ui(self):
        with ui.card().classes("w-full mb-4"):
            ui.label("Filter by Requirements").classes("text-lg font-bold")
            self.filter_container = ui.row().classes("flex flex-wrap gap-4")
            with self.filter_container:
                self._render_filters()

            # Add input field and button for updating candidates
            ui.label("Update Candidates").classes("text-lg font-bold mt-4")
            with ui.row():
                self.update_input = ui.input("Enter 'update' to load new candidates").classes("w-64")
                ui.button("Update", on_click=self._handle_update_button).classes("mt-2")

        self.table = ui.table(
            columns=self.columns,
            rows=self.candidates_list,
            row_key="candidate_id",
            pagination={'sortBy': 'combined_score', 'descending': True}
        ).classes("w-full max-w-[1400px]")

        with self.table:
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
                                </q-item>
                            </q-list>
                        </q-menu>
                    </q-btn>
                </q-td>
                '''
            )
            self.table.on('menu_action', self._on_action)
            self.table.on('rowClick', lambda e: print(f"Row clicked: {e.args}"))  # Debug row click

    def update(self, new_candidates: List[CandidateResultLong]):
        """Update the table with new candidates, refreshing data and UI."""
        # Update candidates_map and candidates_list
        self.candidates_map = {c.candidate_id: c.dict(exclude_none=True) for c in new_candidates}
        self.candidates_list = []
        for cand in self.candidates_map.values():
            cand_copy = cand.copy()
            cand_copy['musthave'] = [req for req in cand['requirements'] if req['ismusthave']]
            cand_copy['desirable'] = [req for req in cand['requirements'] if not req['ismusthave']]
            self.candidates_list.append(cand_copy)

        # Update requirement names and filters
        self.req_names = sorted({
            req["reqname"]
            for cand in self.candidates_list
            for req in cand["requirements"]
        })
        self.filters = {req_name: [] for req_name in self.req_names}

        # Refresh the table rows
        self.table.rows = self.candidates_list

        # Clear and rebuild the filter UI
        self.filter_container.clear()
        with self.filter_container:
            self._render_filters()

    def _handle_update_button(self):
        """Handle the update button click, loading new dummy data if input is 'update'."""
        if self.update_input.value.lower() == 'update':
            new_candidates = get_new_dummy_data()
            self.update(new_candidates)
            ui.notify("Table updated with new candidates!", type='positive')
            self.update_input.value = ''  # Clear the input field
        else:
            ui.notify("Please enter 'update' to load new candidates.", type='warning')

    def _on_action(self, event):
        """Hanterar händelser från åtgärdsmenyn."""
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

    def _render_filters(self):
        for req_name in self.req_names:
            with ui.column():
                ui.label(req_name).classes("text-sm")
                ui.select(
                    ["YES", "NO", "MAYBE"], multiple=True, value=self.filters[req_name],
                    on_change=lambda e, rn=req_name: self._update_filter(rn, e.value)
                ).classes("w-40").props('dense options-dense')

    def _update_filter(self, req_name: str, values: List[str]):
        self.filters[req_name] = values
        self.apply_filters()

    def apply_filters(self):
        filtered_rows = []
        for cand in self.candidates_list:
            include = True
            for req_name, selected_statuses in self.filters.items():
                if selected_statuses:
                    req_status = next(
                        (req["status"] for req in cand["requirements"] if req["reqname"] == req_name), None
                    )
                    if req_status not in selected_statuses:
                        include = False
                        break
            if include:
                filtered_rows.append(cand)
        self.table.rows = filtered_rows

# --- Del 3: Exempeldata och applikationsstart ---
def get_initial_data() -> List[CandidateResultLong]:
    return [
        CandidateResultLong(
            candidate_id='Nr1', name='Harry Potter', combined_score=0.95, summary='The boy who lived.',
            assignment='Defense Against the Dark Arts', location='Hogwarts', internal=True,
            years_exp='7', education="Hogwarts School of Witchcraft and Wizardry",
            requirements=[
                RequirementResult(reqname='Bravery', status='YES', ismusthave=True, source='CV'),
                RequirementResult(reqname='Can fly a broom', status='YES', ismusthave=True, source='CV'),
                RequirementResult(reqname='Voldemort knowledge', status='MAYBE', ismusthave=False, source='Interview')
            ]),
        CandidateResultLong(
            candidate_id='Nr2', name='Hermione Granger', combined_score=0.98, summary='Brightest witch of her age.',
            assignment='Head of Magical Law Enforcement', location='Ministry of Magic', internal=True,
            years_exp='10+', education="Hogwarts School of Witchcraft and Wizardry",
            requirements=[
                RequirementResult(reqname='Bravery', status='YES', ismusthave=True, source='CV'),
                RequirementResult(reqname='Can fly a broom', status='NO', ismusthave=True, source='CV'),
                RequirementResult(reqname='Voldemort knowledge', status='YES', ismusthave=False, source='Interview')
            ])
    ]

def get_new_dummy_data() -> List[CandidateResultLong]:
    return [
        CandidateResultLong(
            candidate_id='Nr3', name='Ron Weasley', combined_score=0.85, summary='Loyal friend and strategist.',
            assignment='Auror Training', location='Ministry of Magic', internal=True,
            years_exp='6', education="Hogwarts School of Witchcraft and Wizardry",
            requirements=[
                RequirementResult(reqname='Teamwork', status='YES', ismusthave=True, source='CV'),
                RequirementResult(reqname='Combat skills', status='MAYBE', ismusthave=True, source='Interview'),
                RequirementResult(reqname='Chess mastery', status='YES', ismusthave=False, source='Reference')
            ]),
        CandidateResultLong(
            candidate_id='Nr4', name='Luna Lovegood', combined_score=0.90, summary='Creative and open-minded witch.',
            assignment='Magizoologist', location='Hogsmeade', internal=False,
            years_exp='5', education="Hogwarts School of Witchcraft and Wizardry",
            requirements=[
                RequirementResult(reqname='Teamwork', status='MAYBE', ismusthave=True, source='CV'),
                RequirementResult(reqname='Combat skills', status='NO', ismusthave=True, source='Interview'),
                RequirementResult(reqname='Creature knowledge', status='YES', ismusthave=False, source='Reference')
            ])
    ]

@ui.page('/')
def main_page():
    ui.label('Candidate Table').classes('text-2xl font-bold p-4')
    initial_candidates = get_initial_data()
    CandidateTable(candidates=initial_candidates)
   

ui.run(port=8004, reload=False)  # Använder reload=False för stabilare felsökning