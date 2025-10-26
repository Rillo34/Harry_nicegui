from nicegui import ui
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict
from datetime import datetime, date
import uuid
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))
from models import RequirementResult, CandidateResultLong
from faker import Faker

fake = Faker()

# Models imported from models.py


class CandidateTable:
    def __init__(self, candidates: List[CandidateResultLong], fictive_start_date: date = date(2025, 10, 1)):
        self.fictive_start_date = fictive_start_date
        self.candidates_map = {c.candidate_id: c.dict(exclude_none=True) for c in candidates}
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

        self.req_names: List[str] = sorted({
            req["reqname"]
            for cand in self.candidates_list
            for req in cand["requirements"]
        })
        self.filters: Dict[str, List[str]] = {req_name: [] for req_name in self.req_names}
        self.search_term = ""

        self._build_ui()

    def _build_ui(self):
        with ui.row().classes('items-center w-full'):
            ui.label('Candidate Table').classes('text-2xl font-bold p-4')
            ui.input(
                placeholder='Search candidates...',
                on_change=lambda e: self._update_search(e.value)
            ).classes('w-64')

        filter_section_expansion = ui.expansion('Requirements', icon='extension').classes('w-full')
        with filter_section_expansion:
            ui.label("Filter by Requirements").classes("text-lg font-bold")
            self.filter_container = ui.row().classes("flex flex-wrap gap-4")
            with self.filter_container:
                self._render_filters()

        self.table = ui.table(
            columns=self.columns,
            rows=self.candidates_list,
            row_key="candidate_id",
            pagination={'sortBy': 'combined_score', 'descending': True}
        ).classes("w-full max-w-[1800px]")

        with self.table:
            self.table.add_slot(
                "body-cell-combined_score",
                r'''
                <q-td :props="props" style="background-color: #fff9c4; font-weight: bold; text-align: left;">
                    {{ props.row.combined_score }}
                </q-td>
                '''
            )
            self.table.add_slot(
                "body-cell-job_availability",
                r'''
                <q-td :props="props">
                    {{ props.row.job_availability }}
                </q-td>
                '''
            )
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
            # Custom sort for job_availability by absolute value
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
            self.table.on('rowClick', lambda e: print(f"Row clicked: {e.args}"))
            # Add custom sort function in JavaScript
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
        self.req_names = sorted({
            req["reqname"]
            for cand in self.candidates_list
            for req in cand["requirements"]
        })
        self.filters = {req_name: [] for req_name in self.req_names}
        self.search_term = ""

        self.table.rows = self.candidates_list
        self.filter_container.clear()
        with self.filter_container:
            self._render_filters()
        self.apply_filters()

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

    def _update_search(self, value: str):
        self.search_term = value.lower()
        self.apply_filters()

    def apply_filters(self):
        filtered_rows = []
        for cand in self.candidates_list:
            include = True
            # Apply requirement filters
            for req_name, selected_statuses in self.filters.items():
                if selected_statuses:
                    req_status = next(
                        (req["status"] for req in cand["requirements"] if req["reqname"] == req_name), None
                    )
                    if req_status not in selected_statuses:
                        include = False
                        break
            # Apply search filter
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
        
        print(f"Filtered rows: {[cand['name'] for cand in filtered_rows]}")
        self.table.rows = filtered_rows
        self.table.update()

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
            available_from=date(2025, 9, 26),  # -5d from 2025-10-01
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
            available_from=date(2025, 10, 11),  # +10d from 2025-10-01
            summary="Brightest witch of her age.",
            requirements=[
                RequirementResult(reqname="Bravery", status="YES", ismusthave=True, source="JD"),
                RequirementResult(reqname="Can fly a broom", status="NO", ismusthave=True, source="JD"),
                RequirementResult(reqname="Voldemort knowledge", status="YES", ismusthave=False, source="USER"),
            ],
            status_id=2,
            status="Interviewing",
        ),
        CandidateResultLong(
            candidate_id="Nr3",
            name="Ron Weasley",
            combined_score=0.85,
            assignment="Auror Training",
            years_exp="6",
            location="Ministry of Magic",
            education="Hogwarts School of Witchcraft and Wizardry",
            internal=True,
            available_from=None,  # N/A
            summary="Loyal friend and strategist.",
            requirements=[
                RequirementResult(reqname="Bravery", status="YES", ismusthave=True, source="USER"),
                RequirementResult(reqname="Can fly a broom", status="MAYBE", ismusthave=True, source="JD"),
                RequirementResult(reqname="Voldemort knowledge", status="NO", ismusthave=False, source="JD"),
            ],
            status_id=3,
            status="Available",
        ),
        CandidateResultLong(
            candidate_id="Nr4",
            name="Luna Lovegood",
            combined_score=0.90,
            assignment="Magizoologist",
            years_exp="5",
            location="Hogsmeade",
            education="Hogwarts School of Witchcraft and Wizardry",
            internal=False,
            available_from=date(2025, 10, 1),  # 0d from 2025-10-01
            summary="Creative and open-minded witch.",
            requirements=[
                RequirementResult(reqname="Bravery", status="MAYBE", ismusthave=True, source="JD"),
                RequirementResult(reqname="Can fly a broom", status="NO", ismusthave=True, source="JD"),
                RequirementResult(reqname="Voldemort knowledge", status="YES", ismusthave=False, source="JD"),
            ],
            status_id=4,
            status="Interviewing",
        ),
    ]

def get_new_dummy_data() -> List[CandidateResultLong]:
    return [
        CandidateResultLong(
            candidate_id='Nr5',
            name='Draco Malfoy',
            combined_score=0.88,
            summary='Ambitious and cunning.',
            assignment='Slytherin Consultant',
            location='Malfoy Manor',
            internal=False,
            years_exp='6',
            education="Hogwarts School of Witchcraft and Wizardry",
            available_from=date(2025, 9, 21),  # -10d from 2025-10-01
            requirements=[
                RequirementResult(reqname='Teamwork', status='NO', ismusthave=True, source='CV'),
                RequirementResult(reqname='Combat skills', status='YES', ismusthave=True, source='Interview'),
                RequirementResult(reqname='Chess mastery', status='MAYBE', ismusthave=False, source='Reference')
            ],
            status_id=5,
            status="Available",
        ),
        CandidateResultLong(
            candidate_id='Nr6',
            name='Neville Longbottom',
            combined_score=0.87,
            summary='Brave and loyal.',
            assignment='Herbology Specialist',
            location='Hogwarts',
            internal=True,
            years_exp='5',
            education="Hogwarts School of Witchcraft and Wizardry",
            available_from=date(2025, 10, 6),  # +5d from 2025-10-01
            requirements=[
                RequirementResult(reqname='Teamwork', status='YES', ismusthave=True, source='CV'),
                RequirementResult(reqname='Combat skills', status='MAYBE', ismusthave=True, source='Interview'),
                RequirementResult(reqname='Chess mastery', status='NO', ismusthave=False, source='Reference')
            ],
            status_id=6,
            status="Available",
        )
    ]

@ui.page('/')
def main_page():
    initial_candidates = get_initial_data()
    table = CandidateTable(candidates=initial_candidates)
    input("get new candidates")
    new_candidates =get_new_dummy_data()
    table.update(new_candidates)

ui.run(port=8004, reload=True)