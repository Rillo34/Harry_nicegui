# data_table.py
import pandas as pd
from nicegui import ui
from typing import Dict, List, Set
from datetime import date, datetime, timedelta




class DataTable:
    def __init__(self, df: pd.DataFrame, title="Table", hidden_columns: List[str] = None):
        self.df = df
        self.title = title
        self.table = None
        self.all_columns = list(self.df.columns)
        self.hidden_columns = hidden_columns or []
        self.visible_columns = [c for c in self.all_columns if c not in self.hidden_columns]
        self.render()

    def render(self):
        # ui.label(self.title).classes('text-sm font-bold mt-4 mb-2')

        rows = self.df.to_dict(orient='records')
        columns = [
            {'name': c, 'label': c, 'field': c, 'sortable': True}
            for c in self.visible_columns
        ]
        
        with ui.card().classes('w-full') as container:
            container.style('height: 700px;')  # eller 1000px, vad du vill

            self.table = ui.table(
                columns=columns,
                rows=rows,
                row_key="id",
                pagination={"rowsPerPage": 15}
            ).props('dense').classes('w-full no-wrap sticky-header')

        self.table.style('height: 100%; overflow-y: auto; overflow-x: auto;')
        self.add_remains_badge()
        
    def add_filter(self, fields_to_search):
        with ui.row().classes('items-center gap-2 mt-2'):
            ui.label("Filter:")
            ui.input(
                placeholder="Search...",
                on_change=lambda e: self._apply_filter(e.value)
            ).props('dense').classes("w-64 text-sm")
            ui.select(
                    options=list(self.all_columns),
                    label="Hide/select Columns",
                    multiple=True,
                    on_change=lambda e: self._update_columns(e.value)
                ).props('dense').classes("w-64 text-sm")

    def _apply_filter(self, term):
        term = term.lower()
        filtered = []

        for row in self.df.to_dict(orient='records'):
            if any(term in str(value).lower() for value in row.values()):                
                filtered.append(row)
        self.table.rows = filtered
        self.table.update()
    
    def _update_columns(self, hidden_columns: List[str]):
        """Hide selected columns and refresh the table."""
        all_columns = list(self.df.columns)
        self.visible_columns = [col for col in all_columns if col not in hidden_columns]
        new_columns = [
        {'name': c, 'label': c, 'field': c, 'sortable': True}
        for c in self.visible_columns
        ]

        self.table.columns = new_columns
        self.table.update()
        print(f"Visible columns updated: {self.visible_columns}")

    def add_remains_badge(self):
        self.table.add_slot('body-cell-remains', r'''
            <q-td :props="props">
                <q-badge
                    :color="props.row.remains > 30 ? 'red' : (props.row.remains < 0 ? 'orange' : 'green')"
                    align="middle"
                >
                    {{ props.row.remains }} h
                </q-badge>
                <span class="text-caption q-ml-sm">
                    {{ props.row.remains > 30 ? 'Need alloc' : (props.row.remains < 0 ? 'Over alloc' : 'ok') }}
                </span>
            </q-td>
        ''')



class ContractAllocationTable(DataTable):
    def __init__(self, contract_alloc_df: pd.DataFrame):
        # här anger du vilka kolumner som ska vara gömda från start
        hidden = ['start_date', 'end_date', 'id', 'allocation_percent']
    
        # cols.insert(cols.index("contract_hours")+1, cols.pop(cols.index("remains")))
        # df = df[cols]
        super().__init__(contract_alloc_df, title="Contract Allocation", hidden_columns=hidden)

    def render(self):
        # dropdownen för filter byggs i DataTable.add_filter
        self.add_filter(['candidate_id', 'project', 'contract_id'])
        super().render()
        self.add_allocation_buttons()
        self.add_summary_row()  # summera på filtrerade rader

    def add_summary_row(self):
        current_rows = self.table.rows
        total_alloc = sum(r['allocated_hours'] for r in current_rows)
        total_remains = sum(r['remains'] for r in current_rows)

        self.table.slots.pop('bottom-row', None)
        self.table.add_slot('bottom-row', f'''
            <q-tr>
                <q-td colspan="3" class="text-right text-bold">Totals (filtered):</q-td>
                <q-td>{total_alloc} h</q-td>
                <q-td>{total_remains} h</q-td>
            </q-tr>
        ''')
    # helper som subklasser kan använda


    def add_allocation_buttons(self):
        # se till att actions alltid finns kvar
        self.table.columns.insert(3, {
            'name': 'actions',
            'label': 'Actions',
            'field': 'actions'
        })
        self.table.update()

        self.table.add_slot('body-cell-actions', r'''
            <q-td :props="props">
                <q-btn size="sm" dense
                    @click="$parent.$emit('changeValue', {action: 'add', row: props.row})">
                    Add 10%
                </q-btn>
                <q-btn size="sm" dense
                    @click="$parent.$emit('changeValue', {action: 'remove', row: props.row})">
                    Sub 10%
                </q-btn>
            </q-td>
        ''')    
        self.table.on('changeValue', self._changeValue)

    def distribute_hours_over_months(self, start: date, end: date, total_hours: int):
        rng = pd.date_range(start, end, freq="D")
        df = pd.DataFrame({"date": rng})
        df["month"] = df["date"].dt.to_period("M")
        days_per_month = df["month"].value_counts().sort_index()
        hours_per_month = (days_per_month / days_per_month.sum()) * total_hours
        # Returnera en dict: {"2025-01": 40, "2025-02": 60, ...}
        return {str(k): round(v) for k, v in hours_per_month.to_dict().items()}

    def _changeValue(self, e):
        payload = e.args
        row = payload['row']
        print("payload: \n", payload)
        action = payload['action']
        factor = 1.1 if action == 'add' else (1/1.1)

        # month_cols = [c for c in row.keys() if c.startswith('202')]
        old_allocation = row['allocated_hours'] 
        new_allocation = int(row['allocated_hours'] * factor)
        diff = new_allocation - old_allocation
        row['allocated_hours'] = new_allocation
        new_total_alloc = row['allocated_total'] +diff
        new_remains = row['remains'] -diff
        month_hours = self.distribute_hours_over_months(
            row["start_date"],
            row["end_date"],
            row["allocated_hours"]
        )
        print(month_hours)
        row.update(month_hours)
        row['remains'] = new_remains
        row['allocated_total'] = new_total_alloc

        for rad in self.table.rows:
            if rad['id'] == row['id']:
                rad.update(row)
            elif rad['contract_id'] == row['contract_id']:
                rad['remains'] = new_remains
                rad['allocated_total'] = new_total_alloc

        for rad in self.contract_table.table.rows:
            if rad['contract_id'] == row['contract_id']:
                rad['remains'] = new_remains
                rad['allocated_total'] = new_total_alloc
        
        self.table.update()
        self.contract_table.table.update()

    def add_remains_badge(self):
        self.table.add_slot('body-cell-remains', r'''
            <q-td :props="props">
                <q-badge
                    :color="props.row.remains > 30 ? 'red' : (props.row.remains < 0 ? 'orange' : 'green')"
                    align="middle"
                >
                    {{ props.row.remains }} h
                </q-badge>
                <span class="text-caption q-ml-sm">
                    {{ props.row.remains > 30 ? 'Need alloc' : (props.row.remains < 0 ? 'Over alloc' : 'ok') }}
                </span>
            </q-td>
        ''')



class ContractHoursTable(DataTable):
    def __init__(self, df: pd.DataFrame):
        hidden = ['created_at', 'allocations', 'job_id']
        super().__init__(df, title="Contracts", hidden_columns=hidden)


    def render(self):
        self.add_filter(['contract_id', 'description', 'customer'])
        super().render()

class AbsenceTable(DataTable):
    def render(self):
        super().render()
        self.add_filter(['candidate_id'])