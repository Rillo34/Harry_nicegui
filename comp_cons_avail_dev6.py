# data_table.py
import pandas as pd
import matplotlib.pyplot as plt
from nicegui import ui
from typing import Dict, List, Set
from datetime import date, datetime, timedelta
import asyncio
from .api_fe import APIController, UploadController
import sys
import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))




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
        self.table.add_slot('bottom-row', self.add_summary_row(self.table.rows))

        
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
        self.add_summary_row(filtered)
        print("antal filtrearde rader:", len(filtered))
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
    def add_summary_row(self, rows):
        exclude_from_summary = {
            'candidate_id',
            'project',
            'contract_id',
            'actions',
            'start_date',
            'end_date'
        }   
        cells = []

        def to_float(v):
            if v in (None, "", " ", "NaN"):
                return 0
            try:
                return float(v)
            except (ValueError, TypeError):
                return 0

        for col in self.table.columns:
            name = col['name']

            # kolumnens label
            if name == 'contract_id':
                cells.append("<q-td class='text-bold'>Totals (filtered):</q-td>")
                continue

            # ska vi hoppa över kolumnen?
            if name in exclude_from_summary:
                cells.append("<q-td></q-td>")
                continue

            # om alla värden i kolumnen är numeriska → summera dem
            try:
                total = sum(to_float(row.get(name)) for row in rows)
                cells.append(
                    f"<q-td class='text-bold text-right'>{total}</q-td>"
                )
            except (ValueError, TypeError):
                # kolumnen går inte att summera
                cells.append("<q-td></q-td>")

        return "<q-tr class='bg-grey-2'>" + "".join(cells) + "</q-tr>"



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
        # self.table.add_slot('bottom-row', self.add_summary_row(self.table.rows))

    


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

        for rad in self.table.rows:
            if rad['contract_id'] == row['contract_id']:
                rad['remains'] = new_remains
                rad['allocated_total'] = new_total_alloc
        
        self.table.update()

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

controller = UploadController()
api_client = APIController(controller)

async def get_contracts():
    contracts = await api_client.get_contracts()
    print(contracts)
    return contracts

async def get_allocations():
    allocations = await api_client.get_allocations()
    print(allocations)
    return allocations


contracts = asyncio.run(get_contracts())
contract_df = pd.DataFrame(contracts)

allocations = asyncio.run(get_allocations())
allocation_df = pd.DataFrame(allocations)
print(allocation_df)

month_cols = [col for col in allocation_df.columns if col[:4].isdigit() and col[4] == '-']
monthly_alloc = allocation_df.groupby('candidate_id')[month_cols].sum()
monthly_alloc['Total'] = monthly_alloc.sum(axis=1)
print(monthly_alloc)

df_percent = allocation_df.copy()
df_percent[month_cols] = df_percent[month_cols] / 150 
# df_percent[month_cols] = df_percent[month_cols].round(0)
for col in month_cols:
    df_percent[col] = df_percent[col].apply(lambda x: f'{x:.0%}')
print("----DF PERCENT ----", df_percent)

def handle_select(e):
    # e.value innehåller det valda alternativet
    selected_plot = e.value
    ui.notify(f'Du valde: {selected_plot}')
    # här kan du lägga logik för att visa rätt plot
    if selected_plot == 'plot1':
        ui.label("ettan")
    elif selected_plot == 'plot2':
        ui.label("tvåan")
    elif selected_plot == 'plot3':
        ui.label("trean")

with ui.column().classes('w-full'):
    with ui.tabs().classes('w-full') as tabs:
        contract_tab = ui.tab('Contracts')
        allocation_tab = ui.tab('Allocations abs')
        percent_tab = ui.tab('Allocations %')
        plot_tab = ui.tab('Plots')
    with ui.tab_panels(tabs, value = contract_tab).classes('w-full'):
        with ui.tab_panel(contract_tab):
            contract_table = DataTable(contract_df)
        with ui.tab_panel(allocation_tab):
            allocation_table = ContractAllocationTable(allocation_df)
        with ui.tab_panel(plot_tab):
            plots = ['plot1', 'plot2', 'plot3']
            plot_area = ui.column()

            def handle_select(e, area):
                area.clear()
                if e.value == 'plot1':
                    fig, ax = plt.subplots(figsize=(12,6))
                    monthly_alloc[month_cols].T.plot(kind='bar', stacked=True, ax=ax)
                    ax.set_title('Allokering per månad (stacked per kandidat)')
                    ax.set_ylabel('Allokerade timmar')
                    ax.set_xlabel('Månad')
                    ax.legend(title='Kandidat', bbox_to_anchor=(1.05, 1), loc='upper left')
                    area.add(ui.matplotlib(fig))   # <-- rendera i NiceGUI
                elif e.value == 'plot2':
                    fig, ax = plt.subplots()
                    monthly_alloc.T.plot(kind='bar', ax=ax)
                    area.add(ui.matplotlib(fig))
            ui.select(options=plots, value=plots[1], on_change=lambda e: handle_select(e, plot_area))
        with ui.tab_panel(percent_tab):
            percent_table = ContractAllocationTable(df_percent)
            

ui.run(port = 8007)

