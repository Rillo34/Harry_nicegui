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

class CandidateTable:
    def __init__(self, candidates: List[CandidateResultLong]):
        # Spara originaldata som dicts
        self.candidates = [
            {**c.dict(exclude_none=True), "requirements": [r.dict() for r in c.requirements]}
            for c in candidates
        ]

        # Skapa kolumner från modellen
        self.columns = [
            {
                "name": field,
                "label": field.replace("_", " ").capitalize(),
                "field": field,
                "sortable": True,
                "style": "max-width: 200px; white-space: normal; word-wrap: break-word;"
            }
            for field in CandidateResultLong.__fields__.keys()
        ]

        # Hämta unika kravnamn för filtren
        self.req_names: List[str] = sorted({
            req["reqname"]
            for cand in self.candidates
            for req in cand["requirements"]
        })

        # Filterstatus
        self.filters: Dict[str, List[str]] = {req_name: [] for req_name in self.req_names}

        # Bygg UI
        self._build_ui()

    def _build_ui(self):

        # Filter UI
        with ui.card().classes("w-full mb-4"):
            ui.label("Filter by Requirements").classes("text-lg font-bold")
            # Spara container för filtren så vi kan rensa/bygga om vid update_data()
            self.filter_container = ui.row().classes("flex flex-wrap gap-4")
            with self.filter_container:
                self._render_filters()

        # Tabell UI
        self.table = ui.table(
            columns=self.columns,
            rows=self.candidates,
            row_key="candidate_id",
            pagination={'sortBy': 'combined_score', 'descending': True}
        ).classes("w-full max-w-[1400px]")  # begränsad bredd

        # Anpassad cell för requirements
        with self.table:
            self.table.add_slot(
                "body-cell-requirements",
                r'''
                <q-td :props="props">
                    <div class="flex flex-wrap gap-1">
                        <q-icon
                            v-for="req in props.row.requirements"
                            :name="req.status === 'YES' ? 'check_circle' : req.status === 'NO' ? 'cancel' : 'help'"
                            :color="req.status === 'YES' ? 'green' : req.status === 'NO' ? 'red' : 'yellow'"
                            size="sm"
                            class="q-mr-xs"
                        >
                            <q-tooltip class="custom-tooltip">{{ req.status }} {{ req.reqname }}</q-tooltip>
                        </q-icon>
                    </div>
                </q-td>
                '''
            )


        # Bind context menu event

    def _render_filters(self):
        """Bygger filter-UI:t utifrån self.req_names."""
        for req_name in self.req_names:
            with ui.column():
                ui.label(req_name).classes("text-sm")
                ui.select(
                    ["YES", "NO", "MAYBE"],
                    multiple=True,
                    value=self.filters[req_name],
                    on_change=lambda e, rn=req_name: self._update_filter(rn, e.value)
                ).classes("w-40")

    def _update_filter(self, req_name: str, values: List[str]):
        self.filters[req_name] = values
        self.apply_filters()

    def apply_filters(self):
        filtered_rows = []
        for cand in self.candidates:
            include = True
            for req_name, selected_statuses in self.filters.items():
                if selected_statuses:
                    req_status = next(
                        (req["status"] for req in cand["requirements"] if req["reqname"] == req_name),
                        None
                    )
                    if req_status not in selected_statuses:
                        include = False
                        break
            if include:
                filtered_rows.append(cand)
        self.table.rows = filtered_rows
        self.table.update()

    def update_data(self, new_candidates: List[CandidateResultLong]):
        # Uppdatera originaldata
        self.candidates = [
            {**c.dict(exclude_none=True), "requirements": [r.dict() for r in c.requirements]}
            for c in new_candidates
        ]
        print("fick kandidater: \n", len(self.candidates))

        # Uppdatera kravnamn och filter
        self.req_names = sorted({
            req["reqname"]
            for cand in self.candidates
            for req in cand["requirements"]
        })
        self.filters = {req_name: [] for req_name in self.req_names}
        print("reqnames : \n", self.req_names)

        # Bygg om filtren i UI
        self.filter_container.clear()
        with self.filter_container:
            self._render_filters()

        # Uppdatera tabellrader
        self.table.rows = self.candidates
        self.table.update()

    


# Sample data
def get_initial_data():
    return [CandidateResultLong
            (candidate_id='Nr1', name='Harry', combined_score=0.65, summary='Harry is the best', assignment='Best recruiter in the world', 
             location='RobeStockholm', internal=False, years_exp='3-5', education="Master's, Computer Science", 
             requirements=[RequirementResult(reqname='Can recruit fast', status='YES', ismusthave=True, source='JD'), 
            RequirementResult(reqname='and really good', status='YES', ismusthave=True, source='JD')])
            ]   
    


