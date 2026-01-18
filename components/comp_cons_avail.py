# data_table.py
from tracemalloc import start
import pandas as pd
import matplotlib.pyplot as plt
from nicegui import ui
from typing import Dict, List, Set
from datetime import date, datetime, timedelta
import asyncio
from backend import data_fetch_startup 
from pandas.api.types import is_bool_dtype, is_numeric_dtype
import sys
import re
import os
from datetime import date, datetime
import backend.services as services
from backend.models import ContractRequest, ContractAllocation
import holidays
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))


ui.add_css("""
.summary-row {
    background-color: #e0f2fe;
    font-weight: bold;
    border-top: 2px solid #2563eb;
}
""")

class DataTable:
    def __init__(self, df: pd.DataFrame, title="Table", hidden_columns: List[str] = None, is_summary=False, alloc_table = False, perc_table = False, callbacks = None):
        self.original_df = df
        self.df = df
        self.filtered_df = df
        self.title = title
        self.perc_table = perc_table
        self.alloc_table = alloc_table
        self.table = None
        self.add_allocation = callbacks["add_allocation"]
        self.delete_allocation = callbacks["delete_allocation"]
        self.change_alloc = callbacks["change_alloc"] 
        self.group_mode = "None"
        self.selected_contract_id = None
        self.selected_candidate_id = None
        self.selected_row = None
        self.is_summary = is_summary
        self.all_columns = list(self.df.columns)
        self.hidden_columns = hidden_columns or []
        self.month_cols = [c for c in self.all_columns if c.startswith('202')]
        self.visible_columns = [c for c in self.all_columns if c not in self.hidden_columns]
        self.summary_row = {}
        if self.is_summary:
            self.add_summary_row()
        
        self.render()   
     

    # --- Update of dataframe ---
    def update(self, new_df: pd.DataFrame):
        self.filtered_df = new_df
        self.all_columns = list(self.df.columns)
        self.visible_columns = [c for c in self.all_columns if c not in self.hidden_columns]
        rows = new_df.to_dict(orient='records')
        rows = self._format_rows(rows)

        if self.is_summary:
            self.add_summary_row()
            self.summary_row['id'] = 'SUMMARY'
            rows.insert(0, self.summary_row)

        self.table.columns = [
            {'name': c, 'label': c, 'field': c, 'sortable': True}
            for c in self.visible_columns
        ]
        self.table.rows = rows
        self.table.update()
    
    def _format_rows(self, rows):           # --- If it is a perc_table
        """Format only UI rows, never the DataFrame."""

        for row in rows:                    # --- For the table
            for col in self.month_cols:
                val = row[col]
                if isinstance(val, (int, float)):
                    if val == 0:
                        row[col] = ""
                    elif self.perc_table:
                        row[col] = f"{int(val)}%"

                           
        for col in self.month_cols:         # --- for the summary row
            if self.perc_table:
                val = self.summary_row.get(col) 
                if isinstance(val, (int, float)): 
                    self.summary_row[col] = f"{int(val)}%" 
        return rows
    
    def change_radio(self, e): 
        self.group_mode = e.value 
        df = self.df
        print ("group mode = ", self.group_mode)
        if self.group_mode == "Candidate":
            print("it is candidate")
            df = (
                df.groupby("candidate_id")
                .agg(
                    {
                        "contract_id": lambda x: ", ".join(sorted(set(x))),
                        **{m: "sum" for m in self.month_cols},
                    }
                )
                .reset_index()
            )

        elif self.group_mode == "Group by contract":
            print("it is contract")
            df = (
                df.groupby("contract_id")
                .agg(
                    {
                        "candidate_id": lambda x: ", ".join(sorted(set(x))),
                        **{m: "sum" for m in self.month_cols},
                    }
                )
                .reset_index()
            )
        self.update(df)

    def render(self):
        df = self.df.copy()
        self.filter_container = ui.row()
        with self.filter_container:
            if self.alloc_table:
                self.radio = ui.radio(
                    ['Group by contract', 'Candidate', 'None'],
                    value='None',
                    on_change=self.change_radio,
                ).props('dense').classes("mr-4")
                delete_button = ui.button(icon = 'delete', color ='red', on_click = self.delete_row)
                inc_button = ui.button(text = "add 10%", color ='grey', on_click = self.inc_alloc)
                dec_button = ui.button(text = "sub 10%", color = 'grey', on_click = self.dec_alloc)
            ui.space()
            self.add_filter()

        rows = df.to_dict(orient='records')
        rows = self._format_rows(rows)

        self.summary_row['id'] = 'SUMMARY'
        rows.insert(0, self.summary_row)
        columns = [{'name': 'selection', 'label': '', 'field': 'selection', 'sortable': False}] + [
            {'name': c, 'label': c, 'field': c, 'sortable': True}
            for c in self.visible_columns
        ]
        print("innan table")
        with ui.card().classes('w-full') as container:
            container.style('height: 700px;')  # eller 1000px, vad du vill

            self.table = ui.table(
                columns=columns,
                rows=rows,
                row_key="id",
                on_select=lambda e: self.update_selected_row(e),
                selection = "multiple",
                pagination={"rowsPerPage": 20}
            ).props('dense').classes('w-full no-wrap sticky-header')
        self.table.style('height: 100%; overflow-y: auto; overflow-x: auto;')

        self.table.add_slot('header-selection', r'''
            <q-th auto-width>
                <q-checkbox v-model="props.selected" />
            </q-th>
        ''')

        self.table.add_slot('body', r'''
            <q-tr :props="props"
                :class="props.row.contract_id === 'SUMMARY'   ? 'bg-red-100 text-red-900' :
                        props.row.contract_id === '1' ? 'bg-orange-100 text-orange-900' :
                        'hover:bg-gray-50'">
                <q-td auto-width>
                    <q-checkbox v-model="props.selected" dense />
                </q-td>
                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                    {{ props.row[col.field] }}
                </q-td>
            </q-tr>
                 
        ''')
        if self.alloc_table:
            self.add_allocation_buttons()
            
    def add_allocation_buttons(self):
        pass

    def _changeValue(self):
        print("kajshdkajshd")
        

    def add_filter(self, fields_to_search=None):
        with self.filter_container:
            ui.label("Filter:")
            ui.input(
                placeholder="Search...",
                on_change=lambda e: self._apply_filter(e.value)
            ).props('dense').classes("w-64 text-sm")
            # print("hidden columns:", self.hidden_columns)
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
        filtered = self._format_rows(filtered)
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

    def update_selected_row(self, e):
        print("i update select")
        self.selected_row = e.selection[0]
        print("selected: ", e)       

    async def delete_row (self):
        
        print("ska deleta row:")
        contract_id = self.selected_row['contract_id'] 
        candidate_id = self.selected_row['candidate_id'] 
        await self.delete_allocation (contract_id, candidate_id)
    
    async def inc_alloc(self):
        print("ska öka row:")

        contract_id = self.selected_row['contract_id'] 
        candidate_id = self.selected_row['candidate_id']
        await self.change_alloc(contract_id, candidate_id, up_alloc = True)

    async def dec_alloc (self):
        print("ska minska row:")

        contract_id = self.selected_row['contract_id'] 
        candidate_id = self.selected_row['candidate_id']
        await self.change_alloc(contract_id, candidate_id, up_alloc = False)

#--- WORKING HOURS DF FUNCTION ---



