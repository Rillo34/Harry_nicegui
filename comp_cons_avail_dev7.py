# data_table.py
from tracemalloc import start
import pandas as pd
import matplotlib.pyplot as plt
from nicegui import ui
from typing import Dict, List, Set
from datetime import date, datetime, timedelta
import asyncio
from backend import data_fetch_startup 
from .api_fe import APIController, UploadController
from pandas.api.types import is_bool_dtype, is_numeric_dtype
import sys
import re
import os
from datetime import date, datetime
import backend.services as services
from backend.models import ContractRequest, ContractAllocation
import holidays
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))


ui.add_head_html('''
    <style>
        .summary-row {
            background-color: #f5f5f5 !important;
            font-weight: bold;
            border-top: 2px solid #ccc; /* Detta skapar en "separator"-effekt */
        }
    </style>
''')

class DataTable:
    def __init__(self, df: pd.DataFrame, title="Table", hidden_columns: List[str] = None, is_summary=False):
        self.df = df
        self.filtered_df = df
        self.title = title
        self.table = None
        self.selected_contract_id = None
        self.selected_candidate_id = None
        self.is_summary = is_summary
        self.all_columns = list(self.df.columns)
        self.hidden_columns = hidden_columns or []
        self.visible_columns = [c for c in self.all_columns if c not in self.hidden_columns]
        self.summary_row = {}
        if self.is_summary:
            self.add_summary_row()
        # print("the row", self.summary_row)
        self.render()        
            

    def render(self):
        rows = self.df.to_dict(orient='records')
        self.summary_row['id'] = 'SUMMARY'
        rows.insert(0, self.summary_row)
        columns = [
            {'name': c, 'label': c, 'field': c, 'sortable': True}
            for c in self.visible_columns
        ]
        self.add_filter()

        with ui.card().classes('w-full') as container:
            container.style('height: 700px;')  # eller 1000px, vad du vill

            self.table = ui.table(
                columns=columns,
                rows=rows,
                row_key="id",
                selection = 'single',
                on_select=lambda e: self.update_selected_row(e),
                pagination={"rowsPerPage": 20}
            ).props('dense').classes('w-full no-wrap sticky-header')
        self.table.props(':row-props="props => String(props.row.contract_id) === \'SUMMARY\' ? { style: \'background-color: #f5f5f5; font-weight: bold;\' } : {}"')
        self.table.style('height: 100%; overflow-y: auto; overflow-x: auto;')
        self.table.add_slot(
            'body-row',
            '''
            <q-tr :props="props">
                <q-tooltip class="big-tooltip max-w-96 p-4 whitespace-normal">
                    Beskrivning: {{ props.row.description }}<br>
                    Kund: {{ props.row.customer }}
                </q-tooltip>

                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                    {{ col.value }}
                </q-td>
            </q-tr>
            '''
        )
            
    def add_filter(self, fields_to_search=None):
        with ui.row().classes('items-center gap-2 mt-2'):
            ui.label("Filter:")
            ui.input(
                placeholder="Search...",
                on_change=lambda e: self._apply_filter(e.value)
            ).props('dense').classes("w-64 text-sm")
            print("hidden columns:", self.hidden_columns)
            ui.select(
                    options=list(self.all_columns),
                    value =  self.hidden_columns,
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
        self.filtered_df = pd.DataFrame(filtered)
        if self.is_summary:
            self.add_summary_row()
        filtered.insert(0, self.summary_row)
        self.table.rows = filtered
        self.table.update()
    
    def _update_columns(self, hidden_columns: List[str]):
        """Hide selected columns and refresh the table."""
        print("Hiding columns:", hidden_columns)
        self.hidden_columns = hidden_columns
        self.visible_columns = [col for col in self.all_columns if col not in hidden_columns]
        new_columns = [
        {'name': c, 'label': c, 'field': c, 'sortable': True}
        for c in self.visible_columns 
        ]

        self.table.columns = new_columns
        self.table.update()
        print(f"Visible columns updated: {self.visible_columns}")
        print(f"Hidden columns: {self.hidden_columns}")


    def add_summary_row(self):
        summary = {}
        if self.filtered_df.empty: 
            for col in self.df.columns: 
                summary[col] = '' 
            summary['contract_id'] = 'SUMMARY' 
            self.summary_row = summary 
            return

        for col in self.filtered_df.columns:
            if is_numeric_dtype(self.filtered_df[col].dtype):
                summary[col] = self.filtered_df[col].sum()   # eller mean(), median(), etc.
            else:
                summary[col] = ''
        summary["contract_id"] = "SUMMARY"
        self.summary_row = summary

#--- WORKING HOURS DF FUNCTION ---

def get_working_hours_df():
    def arbetsdagar(year, month):
        sv_holidays = holidays.CountryHoliday('SE', years=[year])
        dagar = []
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        delta = timedelta(days=1)
        current_date = start_date
        while current_date < end_date:
            if current_date.weekday() < 5 and current_date not in sv_holidays:
                dagar.append(current_date)
            current_date += delta
        return dagar
    
    rows = []
    for year in range(2025, 2028):
        for month in range(1, 13):
            dagar = arbetsdagar(year, month)
            rows.append({
                "year": year,
                "month": f"{month:02d}",
                "arbetsdagar": len(dagar)
            })

    arbetsdagar_df = pd.DataFrame(rows)
    df_pivot = arbetsdagar_df.pivot(index="year", columns="month", values="arbetsdagar")
    df_pivot = df_pivot * 8
    return df_pivot.reset_index()
    
def clear_selection(table):
    if isinstance(table.selection, set):
        table.selection.clear()
    else:
        table.selection = None

def add_groupby_radio(e): 
    if e.value == 'Group by contract':
        clear_selection(allocation_table.table)
        allocation_table.table.selection = None

        df = (
            allocation_df
            .groupby('contract_id')
            .agg({
                'candidate_id': list,
                **{col: 'sum' for col in month_cols},
            })
            .reset_index()
        )

        # Gör listan till en sträng
        df['candidate_id'] = df['candidate_id'].apply(lambda x: ', '.join(x))

        # Kolumnordning: kontrakt → kandidater → månader
        df = df[['contract_id', 'candidate_id'] + month_cols]

        allocation_table.df = df


    elif e.value == 'Candidate':
        clear_selection(allocation_table.table)
        allocation_table.table.selection = None  # OBS! Inte 'None' som sträng

        df = (
            allocation_df
            .groupby('candidate_id')
            .agg({
                'contract_id': list,
                **{col: 'sum' for col in month_cols},
            })
            .reset_index()
        )

        df['contract_id'] = df['contract_id'].apply(lambda x: ', '.join(map(str, x)))

        df = df[['candidate_id', 'contract_id'] + month_cols]

        allocation_table.df = df


    else:
        allocation_table.df = allocation_df
        clear_selection(allocation_table.table)
        allocation_table.table.selection = 'single'

    # Uppdatera tabellrader
    allocation_table.table.rows = allocation_table.df.to_dict(orient='records')
    allocation_table.table.rows.insert(0, allocation_table.summary_row)
    allocation_table.table.update()


def get_candidates_for_contract(contract_id):
    allocated_candidates = allocation_df[
        allocation_df['contract_id'] == contract_id
    ]['candidate_id'].tolist()
    return allocated_candidates


def update_allocations_for_contract(df, contract_id, new_candidates):
    # Ta bort gamla rader för kontraktet
    df = df[df["contract_id"] != contract_id].copy()
    new_rows = []
    next_id = df["id"].max() + 1 if not df.empty else 1

    for cand in new_candidates:
        new_rows.append({
            "id": next_id,
            "contract_id": contract_id,
            "candidate_id": cand
        })
        next_id += 1
    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    return df
        
controller = UploadController()
api_client = APIController(controller)

async def get_contracts():
    contracts = await api_client.get_contracts()
    print(contracts)
    return contracts

async def get_allocations():
    allocations = await api_client.get_allocations_perc()
    print(allocations)
    return allocations





def get_candidates_for_contract(contract_id): 
    return (allocation_df[allocation_df['contract_id'] == contract_id]['candidate_id'] .unique() .tolist())

def calculate_allocation_metrics(allocation_df):
    # hitta månadskolumner
    month_cols = [col for col in allocation_df.columns if col.startswith('202')]

    # antal kandidater per kontrakt
    candidates_per_contract = (
        allocation_df
        .groupby('contract_id')['candidate_id']
        .nunique()
    )

    # dela varje månadskolumn med antal kandidater
    for col in month_cols:
        allocation_df[col] = allocation_df[col] // allocation_df['contract_id'].map(candidates_per_contract)

    return allocation_df

def get_contract_df(contracts):

    for v in contracts:
        v["month_hours"] = services.distribute_hours_over_months(
                    v["start_date"],
                    v["end_date"],
                    v["contract_hours"]
                )
    for v in contracts: 
        for key in ["start_date", "end_date", "created_at"]: 
            if hasattr(v[key], "isoformat"): v[key] = v[key].isoformat()

    contract_df = pd.DataFrame(contracts)
    month_cols = contract_df["month_hours"].apply(pd.Series)
    month_cols = month_cols.fillna(0)
    contract_df = pd.concat([contract_df.drop(columns=["month_hours"]), month_cols], axis=1)
    return contract_df

def get_allocation_df(allocations):
    allocation_df = pd.DataFrame(allocations)

    # 1. Lägg till månadskolumner från contract_df
    allocation_df = allocation_df.merge(
        contract_df,  # global
        on="contract_id",
        how="left"
    )

    # 2. Hitta månadskolumner
    month_cols = [col for col in allocation_df.columns if col.startswith("202")]

    # 3. Räkna kandidater per kontrakt
    candidates_per_contract = (
        allocation_df.groupby("contract_id")["candidate_id"].nunique()
    )

    # 4. Dela timmar per kandidat
    for col in month_cols:
        allocation_df[col] = allocation_df[col] // allocation_df["contract_id"].map(candidates_per_contract)

    return allocation_df


# --- CONTRACTS---
# contracts = asyncio.run(get_contracts())
contracts = [c.model_dump() for c in data_fetch_startup.get_contracts()]
contract_df = get_contract_df(contracts)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
hidden_columns = ['contract_id', 'job_id', 'start_date', 'end_date', 'estimated_value', 'contract_hours', 'remains', 'contract_type', 'status', 'notes', 'created_at', 'allocations']
all_contracts = contract_df['contract_id'].tolist()


# --- ALLOCATIONS ---

allocations = [c.model_dump() for c in data_fetch_startup.get_allocations()]
allocation_df_orig = pd.DataFrame(allocations)
allocation_df = get_allocation_df(allocations)
month_cols = [col for col in allocation_df.columns if col.startswith("202")]
allocation_df = allocation_df[['id', 'contract_id', 'candidate_id'] + month_cols]
all_candidates = allocation_df['candidate_id'].unique().tolist()

# --- WORKING HOURS---

working_hours_df = get_working_hours_df()


with ui.column().classes('w-full'):
    with ui.tabs().classes('w-full') as tabs:
        contract_tab = ui.tab('Contracts')
        allocation_tab = ui.tab('Allocations (edit)')
        arbetsdagar_tab = ui.tab('Arbetsdagar')
    with ui.tab_panels(tabs, value = allocation_tab).classes('w-full'):
        with ui.tab_panel(contract_tab):
            contract_table = DataTable(contract_df, hidden_columns=hidden_columns, is_summary=True)
            contract_table.table.selection = 'none'
        with ui.tab_panel(allocation_tab):
            with ui.row():
                ui.radio(['Group by contract', 'Candidate', 'None'], value = 'None', on_change= add_groupby_radio).props('dense').classes("m-2")
                selected_label = ui.label("No selection yet").props('dense').classes("m-2")
                def get_candidates_for_contract(contract_id):
                    allocated_candidates = allocation_df[
                        allocation_df['contract_id'] == contract_id
                    ]['candidate_id'].tolist()
                    return allocated_candidates

                def update_candidate_select(contract_id):
                    candidates = get_candidates_for_contract(contract_id)
                    candidate_select.options = all_candidates
                    candidate_select.value = candidates  # rensa val
                    candidate_select.update()
                    print("allocation df:\n", allocation_df_orig)
                
                def update_alloc_df_orig(e):
                    global allocation_df_orig
                    new_candidates = e.value               # list of candidate_ids
                    contract_id = contract_select.value    # current contract_id
                    # Uppdatera df
                    df = update_allocations_for_contract(
                        allocation_df_orig,
                        contract_id,
                        new_candidates
                    )
                    allocation_df_orig = df
                    print("Updated allocation_df_orig:")
                    print(allocation_df_orig)

                    

                with ui.row().classes("ml-10 gap-4"): # flyttar åt höger + luft mellan
                    contract_select = ui.select(
                        options=all_contracts,
                        label="Contract id",
                        value=all_contracts[0] if all_contracts else None,
                        on_change=lambda e: update_candidate_select(e.value)
                    ).classes("w-48")  # bredd
                    candidate_select = ui.select(
                        options=all_candidates,
                        multiple=True,
                        value=get_candidates_for_contract(contract_select.value) if contract_select.value else [],
                        # on_change=lambda e: ui.notify(f"Selected candidates: {e.value}. Contract = {contract_select.value}"),
                        on_change=lambda e: update_alloc_df_orig(e),
                        label="Candidates on contract"
                    ).classes("w-72")  # bredare
            allocation_table = DataTable(allocation_df, is_summary=True)
            # allocation_table.add_select()
        with ui.tab_panel(arbetsdagar_tab): 
            arbetsdagar_table = DataTable(working_hours_df)


     
ui.run(port = 8004)