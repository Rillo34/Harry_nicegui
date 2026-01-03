# THIS FILE IS FOR DEVELOPMENT AND TESTING OF COMPONENTS ONLY but it is the best one for AVAILABILITY DEVELOPMENT

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
        self.add_summary_row()
        

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
                pagination={"rowsPerPage": 20}
            ).props('dense').classes('w-full no-wrap sticky-header :row-props="props => props.row.name === \'Bob\' ? { style: \'background-color: #ffebee\' } : {}"')

        self.table.style('height: 100%; overflow-y: auto; overflow-x: auto;')
        self.add_remains_badge()
        # self.add_summary_row(self.table.rows)
         
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
                    :color="props.row.remains > 50 ? 'red' : (props.row.remains < 0 ? 'orange' : 'green')"
                    align="middle"
                >
                    {{ props.row.remains }} h
                </q-badge>
                <span class="text-caption q-ml-sm">
                    {{ props.row.remains > 50 ? 'Need alloc' : (props.row.remains < 0 ? 'Over alloc' : 'ok') }}
                </span>
            </q-td>
        ''')

    def add_delete_and_copy_buttons(self):
        # se till att actions alltid finns kvar
        self.table.columns.insert(0 , {
            'name': 'editrow',
            'label': 'Editrow',
            'field': 'editrow'
        })
        self.table.update()

        self.table.add_slot('body-cell-editrow', r'''
            <q-td :props="props">
                <!-- Add 10% -->
                <q-btn 
                    size="sm" dense color="purple" glossy
                    icon="" 
                    @click="$parent.$emit('editrow', {action: 'add', row: props.row})"
                    round
                ></q-btn>

                <!-- Sub 10% -->
                <q-btn 
                    size="sm" dense color="purple" glossy
                    icon="remove" 
                    @click="$parent.$emit('editrow', {action: 'remove', row: props.row})"
                    round
                ></q-btn>
            </q-td>
        ''')    
        self.table.add_slot('body-cell')
        def _(props):
            ui.tooltip(f"Radinfo: {props['row']}")


        self.table.on('editrow', self._edit_row)

    def _edit_row(self, e):
        print("yes")
        print(e.args)


    def add_summary_row(self):
        summary = {}
        for col in self.df.columns:
            if is_numeric_dtype(self.df[col].dtype):
                print("yes")
                summary[col] = self.df[col].sum()   # eller mean(), median(), etc.
            else:
                print("no")
                summary[col] = ''
        summary['id'] = 'summary'   # marker
        print("summary row:", summary)

        self.table.add_row(summary)
        self.table.update()
        
        
    def add_allocation_buttons(self):
        # se till att actions alltid finns kvar
        self.table.columns.insert(2 , {
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


    def _changeValue(self, e):
        global allocation_df
        payload = e.args
        row = payload['row']
        print("payload: \n", payload)
        action = payload['action']
        if action == "add":
            action = 10
        else:
            action = -10
        candidate = row["candidate_id"]
        contract = row["contract_id"]
        print(candidate, contract)
        month_cols = [k for k in row.keys() if k not in ['candidate_id','contract_id']]
        # Filtrera kolumner som faktiskt har ett värde
        cols_with_value = [c for c in month_cols if row[c] not in ['', None]]
        for month in cols_with_value:
            value_str = row[month]
            if isinstance(value_str, str) and value_str.endswith('%'):
                value = float(value_str.rstrip('%'))
            else:
                value = float(value_str)
            # Uppdatera allocation_df
            allocation_df.loc[
                (allocation_df['candidate_id'] == candidate) &
                (allocation_df['contract_id'] == contract) &
                (allocation_df['month'] == month),
                'allocation_percent'
            ] = value + action
        df_new = get_allocations_perc_df(allocation_df)
        self.df = df_new
        allocation_table.table.rows = df_new.to_dict(orient='records')
        allocation_table.table.update()
        update_contract_table()
        update_candidate_table()
        update_contract_summary_table ()
    

        


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


def update_contract_table():
    df = get_contract_total_hours_df(allocation_df, contract_df)
    contract_df["remains"] = df["remains"]
    contract_table.df = contract_df
    contract_table.table.rows = contract_df.to_dict(orient='records')
    contract_table.table.update()


def update_candidate_table():
    """Uppdatera kandidatsummering-tabellen"""
    df_candidate = get_candidate_perc_df(allocation_df)
    candidate_summary_table.df = df_candidate
    candidate_summary_table.table.rows = df_candidate.to_dict(orient='records')
    candidate_summary_table.table.update()


def update_contract_summary_table():
    """Uppdatera kontraktsummering-tabellen (remains/total_allocation)"""
    df_summary = get_contract_total_hours_df(allocation_df, contract_df)
    # Om du vill visa bara vissa kolumner, t.ex. contract_id + remains:
    # df_summary = df_summary[['contract_id', 'remains']]
    contract_summary_table.df = df_summary
    contract_summary_table.table.rows = df_summary.to_dict(orient='records')
    contract_summary_table.table.update()

# contracts = asyncio.run(get_contracts())
contracts = data_fetch_startup.get_contracts()
contract_df = pd.DataFrame(contracts)
print ("--contract ---\n", contract_df.head())
contract_df.info()

# allocations = asyncio.run(get_allocations())
allocations = data_fetch_startup.get_allocations()

allocation_df = pd.DataFrame(allocations)
print("--allocations ---\n", allocation_df)
allocation_df.info()


# index=["candidate_id", "contract_id", "contract_hours", "start_date", "end_date"],
def get_allocations_perc_df(alloc_df: pd.DataFrame) -> pd.DataFrame:
    alloc_df_pivot = alloc_df.pivot_table(
        index=["candidate_id", "contract_id"],
        columns="month",
        values="allocation_percent",
        fill_value=0
    ).reset_index()
    alloc_df_pivot = alloc_df_pivot.apply(pd.to_numeric, errors='ignore')

    alloc_df_percent = alloc_df_pivot.copy()
    month_cols = [c for c in alloc_df_pivot.columns if c[:2].isdigit()]
    alloc_df_percent[month_cols] = alloc_df_percent[month_cols] / 100
    for col in month_cols:
        alloc_df_percent[col] = alloc_df_percent[col].apply(lambda x: f'{x:.0%}')
        alloc_df_percent[col] = alloc_df_percent[col].replace('0%', '')

    return alloc_df_percent


def get_candidate_perc_df(alloc_df: pd.DataFrame) -> pd.DataFrame:
    alloc_df_pivot = alloc_df.pivot_table(
        index=["candidate_id", "contract_id"],
        columns="month",
        values="allocation_percent",
        fill_value=0
    ).reset_index()
    alloc_df_pivot = alloc_df_pivot.apply(pd.to_numeric, errors='ignore')

    alloc_df_percent = alloc_df_pivot.copy()
    month_cols = [c for c in alloc_df_pivot.columns if c[:2].isdigit()]
    alloc_df_percent[month_cols] = alloc_df_percent[month_cols] / 100
    alloc_df_groupby_candidate_perc = alloc_df_percent.groupby('candidate_id').sum().reset_index()
    # alloc_df_groupby_candidate_perc = alloc_df_groupby_candidate_perc.style.applymap(self.color_cells)

    for col in month_cols:
        alloc_df_groupby_candidate_perc[col] = alloc_df_groupby_candidate_perc[col].apply(lambda x: f'{x:.0%}')
        alloc_df_groupby_candidate_perc[col] = alloc_df_groupby_candidate_perc[col].replace('0%', '')
    return alloc_df_groupby_candidate_perc


def get_contract_total_hours_df(alloc_df: pd.DataFrame, contract_df: pd.DataFrame) -> pd.DataFrame:
    alloc_pivot = (
        alloc_df
        .pivot_table(
            index="contract_id",
            columns="month",
            values="allocation_percent",
            aggfunc="sum",      # om flera kandidater på samma kontrakt/månad
            fill_value=0
        )
        .reset_index()
    )
    contract_cols = ["contract_id", "contract_hours"]
    contract_df_small = contract_df[contract_cols]
    result_df = (
        contract_df_small
        .merge(
            alloc_pivot,
            on="contract_id",
            how="left"
        )
    )
    month_cols = [c for c in result_df.columns if isinstance(c, str) and re.fullmatch(r"\d{2}-\d{2}", c)]
    print("month cols", month_cols)
    result_df[month_cols] = result_df[month_cols].fillna(0)
    result_df["total_allocation"] = result_df[month_cols].sum(axis=1)
    result_df["remains"] = result_df["contract_hours"] - result_df["total_allocation"]
    result_df = result_df[contract_cols + ["remains", "total_allocation"] + month_cols]
    return result_df



# allocation_df_groupby_candidate_perc = allocation_df_percent.groupby('candidate_id').sum().reset_index()
# print ("--pivot group by candidate ---\n", allocation_df_groupby_candidate_perc)

# allocation_df_groupby_contract = allocation_df_pivot.groupby('contract_id').sum().reset_index()
# print ("--pivot group by contract ---\n", allocation_df_groupby_contract)



with ui.column().classes('w-full'):
    with ui.tabs().classes('w-full') as tabs:
        contract_base_tab = ui.tab('Contracts')
        allocation_tab = ui.tab('Allocations % (edit)')
        candidate_tab = ui.tab('Alloc summary %')
        contract_tab = ui.tab('Contracts summary hours')
    with ui.tab_panels(tabs, value = contract_tab).classes('w-full'):
        is_allocation_table = False
        with ui.tab_panel(contract_base_tab):
            df = get_contract_total_hours_df(allocation_df, contract_df)
            contract_df["remains"] = df["remains"]
            contract_table = DataTable(contract_df)
        with ui.tab_panel(allocation_tab):
            df = get_allocations_perc_df(allocation_df)
            allocation_table = DataTable(df)
            allocation_table.add_allocation_buttons()
            allocation_table.add_delete_and_copy_buttons()

        with ui.tab_panel(candidate_tab):
            df = get_candidate_perc_df(allocation_df)
            candidate_summary_table = DataTable(df)
        with ui.tab_panel(contract_tab):
            df = get_contract_total_hours_df(allocation_df, contract_df)
            # df = df[['contract_id', 'remains']]
            new_contract_df = (
                contract_df
                .drop(columns=["remains"], errors="ignore")
                .merge(
                    df[['contract_id', 'remains']],
                    on='contract_id',
                    how='right'
                )
            )
            contract_summary_table = DataTable(df)

ui.run(port = 8007)

