from nicegui import ui
import uuid
import sys, os
from typing import Dict, List, Set
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))
from models import RequirementResult, CandidateResultLong

from typing import List, Dict, Set
from nicegui import ui
from models import CandidateResultLong, RequirementResult
from faker import Faker
import sys
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel
from nicegui import ui
fake = Faker()

status_list = [
    {'key': 'contacted', 'label': 'Kontaktad'},
    {'key': 'interviewed', 'label': 'Intervjuad'},
    {'key': 'offered', 'label': 'Erbjuden'},
    {'key': 'rejected', 'label': 'Avslagen'},
]

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
        
        priority_fields = ["candidate_id", "name", "combined_score"]  # fält du vill ha först
        other_fields = [f for f in CandidateResultLong.__fields__ if f not in priority_fields and f != "requirements"]
        excluded_fields = ["education", "summary"]

        ordered_fields = [f for f in priority_fields + other_fields if f not in excluded_fields]
        self.columns = [
            {
                "name": field,
                "label": field.replace("_", " ").capitalize(),
                "field": field,
                "sortable": True,
                "style": "max-width: 200px; white-space: normal; word-wrap: break-word;"
            }
            # for field in CandidateResultLong.__fields__.keys() if field != 'requirements'
            for field in ordered_fields
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
        filter_section_expansion = ui.expansion('Reguirements', icon='extension').classes('w-full')
        with filter_section_expansion:
        # with ui.card().classes("w-full mb-4"):
            ui.label("Filter by Requirements").classes("text-lg font-bold")
            self.filter_container = ui.row().classes("flex flex-wrap gap-4")
            with self.filter_container:
                self._render_filters()

            # Add input field and button for updating candidates
            # ui.label("Update Candidates").classes("text-lg font-bold mt-4")
            # with ui.row():
            #     self.update_input = ui.input("Enter 'update' to load new candidates").classes("w-64")
            #     ui.button("Update", on_click=self._handle_update_button).classes("mt-2")

        self.table = ui.table(
            columns=self.columns,
            rows=self.candidates_list,
            row_key="candidate_id",
            pagination={'sortBy': 'combined_score', 'descending': True}
        ).classes("w-full max-w-[1800px]")

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
            status_items_html = "\n".join([
                f'''
                <q-item clickable v-close-popup
                    @click="$parent.$emit('menu_action', {{action: 'set_status', row_id: props.row.id, status: '{status['key']}'}})">
                    <q-item-section>{status['label']}</q-item-section>
                </q-item>
                ''' for status in status_list
            ])

            # Lägg till meny i tabellens actions-kolumn
            self.table.add_slot(
                "body-cell-actions",
                f'''
                <q-td :props="props">
                    <q-btn dense flat round icon="more_vert">
                        <q-menu>
                            <q-list style="min-width: 150px">
                                <q-item-label header>Status</q-item-label>
                                {status_items_html}
                            </q-list>
                        </q-menu>
                    </q-btn>
                </q-td>
                '''
            )
            self.table.on('menu_action', self._on_action)
            # self.table.on('rowClick', lambda e: print(f"Row clicked: {e.args}"))  # Debug row click

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
            candidate_id="Nr1",
            combined_score=0.95,
            name="Harry Potter",
            assignment="Defense Against the Dark Arts",
            years_exp="7",
            location="Hogwarts",
            education="Hogwarts School of Witchcraft and Wizardry",
            internal=True,
            available_from = fake.date_between(start_date='-1y', end_date='+1y'),
        
            summary="The boy who lived.",
            requirements=[
                RequirementResult(reqname="Bravery", status="YES", ismusthave=True, source="USER"),
                RequirementResult(reqname="Can fly a broom", status="YES", ismusthave=True, source="JD"),
                RequirementResult(reqname="Voldemort knowledge", status="MAYBE", ismusthave=False, source="JD"),
            ],
            status_id=1,
            status="Available",
        ),
        CandidateResultLong(
            candidate_id="Nr2",
            name="Hermione Granger",
            combined_score=0.98,
            assignment="Head of Magical Law Enforcement",
            years_exp="10+",
            location="Ministry of Magic",
            education="Hogwarts School of Witchcraft and Wizardry",
            internal=True,
            # ingen available_from → blir None
            summary="Brightest witch of her age.",
            requirements=[
                RequirementResult(reqname="Bravery", status="YES", ismusthave=True, source="JD"),
                RequirementResult(reqname="Can fly a broom", status="NO", ismusthave=True, source="JD"),
                RequirementResult(reqname="Voldemort knowledge", status="YES", ismusthave=False, source="USER"),
            ],
            status_id=2,
            status="Interviewing",
        ),
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
                RequirementResult(reqname='Chess mastery', status='YES', ismusthave=False, source='Reference')
            ])
    ]

@ui.page('/')
def main_page():
    ui.label('Candidate Table').classes('text-2xl font-bold p-4')
    initial_candidates = get_initial_data()
    CandidateTable(candidates=initial_candidates)
   

ui.run(port=8004, reload=False)  # Använder reload=False för stabilare felsökning
    


# Sample data
def get_initial_data():
    return [CandidateResultLong
            (candidate_id='Nr1', name='Harry', combined_score=0.65, summary='Harry is the best', assignment='Best recruiter in the world', 
             location='RobeStockholm', internal=False, years_exp='3-5', education="Master's, Computer Science", 
             requirements=[RequirementResult(reqname='Can recruit fast', status='YES', ismusthave=True, source='JD'), 
            RequirementResult(reqname='and really good', status='YES', ismusthave=True, source='JD')])
            ]   
    


