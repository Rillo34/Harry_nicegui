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
        self.original_df = df.copy()
        self.df = df
        self.df_latest = df.copy()
        self.filtered_df = df
        self.title = title
        self.perc_table = perc_table
        self.alloc_table = alloc_table
        self.table = None
        self.add_allocation = callbacks["add_allocation"]
        self.delete_allocation = callbacks["delete_allocation"]
        self.change_alloc = callbacks["change_alloc"] 
        self.change_cell_alloc = callbacks["change_cell_alloc"]
        self.group_mode = "None"
        self.enable_buttons = True
        self.selected_rows = []
        self.is_summary = is_summary
        self.summary_container = ui.row().classes( 'q-table__top q-tr bg-grey-2 text-bold' )
        self.all_columns = list(self.df.columns)
        self.hidden_columns = hidden_columns or []
        self.month_cols = [c for c in self.all_columns if c.startswith('202')]
        self.visible_columns = [c for c in self.all_columns if c not in self.hidden_columns]
        self.summary_row = {}
        if self.is_summary:
            self.add_summary_row()
        
        self.render()   
     

    # --- Update of dataframe ---

    def update(self, new_df: pd.DataFrame, group_by = False):
        self.table.update_from_pandas(new_df)
        if not group_by:
            self.df_latest = new_df
        if self.is_summary: 
            self.add_summary_row() 
            self.table.rows.insert(0, self.summary_row) # 4. Uppdatera UI igen 
            self._format_rows(self.table.rows)
            self.table.update() 

    
    def _format_rows(self, rows):           # --- If it is a perc_table
        """Format only UI rows, never the DataFrame."""
        for row in rows:                    # --- For the table
            for col in self.month_cols:
                val = row[col]
                if isinstance(val, (int, float)):
                    if val == 0:
                        row[col] = ""
                    # elif self.perc_table:
                    #     row[col] = f"{int(val)}%"
                           
        for col in self.month_cols:         # --- for the summary row
            if self.perc_table:
                val = self.summary_row.get(col) 
                # if isinstance(val, (int, float)): 
                #     self.summary_row[col] = f"{int(val)}%" 
        return rows
    
    def change_visibility_of_buttons(self, visible: bool):
        self.delete_button.visible = visible
        self.inc_button.visible = visible
        self.dec_button.visible = visible
        self.add_button.visible = visible

    def change_radio(self, e): 
        self.group_mode = e.value 
        print ("group mode = ", self.group_mode)
        if self.group_mode == "None": 
            df = self.df_latest.copy()
            self.enable_buttons
        elif self.group_mode == "Candidate":
            self.enable_buttons = False
            print("it is candidate")
            df = (
                self.df_latest.groupby("candidate_id")
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
            self.enable_buttons = False
            df = (
                self.df_latest.groupby("contract_id")
                .agg(
                    {
                        "candidate_id": lambda x: ", ".join(sorted(set(x))),
                        **{m: "sum" for m in self.month_cols},
                    }
                )
                .reset_index()
            )
        df = df.round(1)
        self.update(df, group_by=True)

    def _on_cell_edit(self, e): 
        print("Cell edit event args:", e.args)
        data = e.args[0] 
        ui.notify(f"Saving value {data['value']} for contract {data['contract_id']}, candidate {data['candidate_id']}, month {data['month']}")

    # ui.run_async(self._save_cell(contract_id, candidate_id, month, value))


    def render(self):
        df = self.df.copy()
        self.filter_container = ui.row().classes("w-full items-center")
        with self.filter_container:
            if self.alloc_table:
                self.radio = ui.radio(
                    ['Group by contract', 'Candidate', 'None'],
                    value='None',
                    on_change=self.change_radio,
                ).props('dense').classes("mr-4")
            if self.perc_table:
                delete_button = ui.button(icon = 'delete', text = "Delete", color ='red', on_click = self.delete_row).bind_enabled_from(self.radio, 'value', lambda v: v == 'None' )
                inc_button = ui.button(text = "add 10%", icon="arrow_upward", color ='grey', on_click = self.inc_alloc).bind_enabled_from(self.radio, 'value', lambda v: v == 'None' )
                dec_button = ui.button(text = "sub 10%", icon="arrow_downward",  color = 'grey', on_click = self.dec_alloc).bind_enabled_from(self.radio, 'value', lambda v: v == 'None' )
                add_button = ui.button(text = "Add allocation", icon="add", color = 'blue', on_click = self.add_alloc).bind_enabled_from(self.radio, 'value', lambda v: v == 'None' )

                ui.space()
            
                self.add_filter()
            else:
                ui.space()
                self.add_filter()

        df = df.round(1)
        rows = df.to_dict(orient='records')
        rows = self._format_rows(rows)
        rows.insert(0, self.summary_row)
        if self.perc_table:
            selection_mode = 'multiple'
            print("perc table - multiple selection")
        elif self.is_summary ==  True and not self.alloc_table:
            selection_mode = 'multiple'
        else:
            selection_mode = 'none'

        if selection_mode == 'multiple':
            columns = [{'name': 'selection', 'label': '', 'field': 'selection', 'sortable': False}] + [
                {'name': c, 'label': c, 'field': c, 'sortable': True}
                for c in self.visible_columns
            ]
        else:
            columns = [
                {'name': c, 'label': c, 'field': c, 'sortable': True}
                for c in self.visible_columns
            ]

        with ui.card().classes('w-full') as container:
            container.style('height: 700px;')  # eller 1000px, vad du vill

            self.table = ui.table(
                columns=columns,
                rows=rows,
                row_key= "id", 
                selection=selection_mode,
                pagination={"rowsPerPage": 20}
            ).props('dense').classes('w-full no-wrap sticky-header')
            self.table.on('cell-edit', self._on_cell_edit)

        self.table.style('height: 100%; overflow-y: auto; overflow-x: auto;')
        self.table.on('selection', self.update_selected_row)

        if selection_mode == 'multiple':
            self.table.add_slot('header-selection', r'''
                <q-th auto-width>
                    <q-checkbox v-model="props.selected" />
                </q-th>
            ''')
        for col in self.month_cols:
            self.table.add_slot(f"body-cell-{col}", f"""
                <q-td :props="props" class="cursor-pointer"
                    @click="() => $parent.$emit('cell-click', {{row: props.row, col: '{col}'}})">
                    {{{{ props.row['{col}'] }}}}
                </q-td>
            """)
        self.table.on("cell-click", lambda e: self.open_edit_dialog(e.args["row"], e.args["col"]))
        

    def open_edit_dialog(self, row, col): 
        print(f"Opening edit dialog for row: {row}, column: {col}")
        async def save_edit(e):
            new_value = self.edit_value.value
            self.current_row[self.current_col] = new_value
            print(f"row: {self.current_row}")
            edit_dialog.close()
            await self.change_cell_alloc(self.current_row, self.current_col, new_value)
        with ui.dialog() as edit_dialog, ui.card():
            ui.label(f"Edit {col} allocation")
            ui.label(f"Current value: {row[col]}")
            self.edit_value = ui.number(
                "Värde",
                format="%.1f",
                step=0.1,
                min=0,
                max=1
            )
            ui.button("Spara", on_click=save_edit)
        self.current_row = row
        self.current_col = col
        self.edit_value.value = row[col]
        edit_dialog.open()


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
        if self.df_latest.empty:
            for col in self.df_latest.columns:
                summary[col] = ''
        else:
            for col in self.df_latest.columns:
                if col in self.month_cols:
                    summary[col] = round(self.df_latest[col].sum(), 1)
                else:
                    summary[col] = ''
        self.summary_row = summary

    def update_selected_row(self, e):
        selected_rows = self.table.selected
        print("Selected rows:", selected_rows)
        if self.perc_table:
            self.selected_rows = [ 
                { "contract_id": row["contract_id"], "candidate_id": row["candidate_id"] } 
                for row in selected_rows ]
        else:
            self.selected_rows = [ row["contract_id"] for row in selected_rows ]
        print("Rader valda:", self.selected_rows)


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
        if self.df_latest.empty: 
            for col in self.df_latest.columns: 
                summary[col] = '' 
            self.summary_row = summary 
            return

        for col in self.df_latest.columns:
            if is_numeric_dtype(self.df_latest[col].dtype):
                summary[col] = self.df_latest[col].sum().round(1)   # eller mean(), median(), etc.
            else:
                summary[col] = ''
        # summary["contract_id"] = "SUMMARY"
        self.summary_row = summary

    def update_selected_row(self, e):
        selected_rows = self.table.selected
        print("Selected rows:", selected_rows)
        if self.perc_table:
            self.selected_rows = [ 
                { "contract_id": row["contract_id"], "candidate_id": row["candidate_id"] } 
                for row in selected_rows ]
        else:
            self.selected_rows = [ row["contract_id"] for row in selected_rows ]
        print("Rader valda:", self.selected_rows)
        

    async def delete_row (self):
        print("ska deleta rows:", self.selected_rows)
        await self.delete_allocation (self.selected_rows)
    
    async def inc_alloc(self):
        print("ska öka rows")
        await self.change_alloc(self.selected_rows, up_alloc = True)

    async def change_cell_alloc(self, row, col, new_value):
        print("ska ändra en cell")
        await self.change_cell_alloc(row, col, new_value)

    async def dec_alloc (self):
        print("ska minska row")
        await self.change_alloc(self.selected_rows, up_alloc = False)

    
    def add_alloc(self):
        print("ska lägga till alloc:")

        with ui.dialog() as dialog:
            with ui.card().classes("p-4"):   # <-- VIKTIG
                ui.label("Add new allocation")

                contract_list = sorted(self.df['contract_id'].unique().tolist())
                all_contracts = contract_list
                all_candidates = sorted(self.df['candidate_id'].dropna().unique().tolist())

                def get_candidates_for_contract(contract_id):
                    used = set(self.df[self.df['contract_id'] == contract_id]['candidate_id'].dropna())
                    print("used candidates for contract", contract_id, ":", used)
                    return [c for c in all_candidates if c not in used]

                def update_candidate_select(contract_id):
                    candidates = get_candidates_for_contract(contract_id)
                    candidate_select.options = candidates
                    candidate_select.value = None
                    candidate_select.update()

                contract_select = ui.select(
                    options=all_contracts,
                    label="Contract id",
                    value=contract_list[0] if contract_list else None,
                    on_change=lambda e: update_candidate_select(e.value)
                ).classes("w-48")

                candidate_select = ui.select(
                    options=get_candidates_for_contract(contract_select.value) if contract_select.value else [],
                    multiple=True,
                    value=None,
                    clearable=True,
                    on_change=lambda e: ui.notify(f"Selected candidates: {e.value}. Contract = {contract_select.value}"),
                    label="Candidates to add:"
                ).classes("w-72") 

                alloc_percent = ui.number(
                    "Alloc_percent",
                    format="%.1f",
                    step=0.1,
                    value=0.5,
                    min=0,
                    max=1
                ).classes("w-72")

                with ui.row():
                    ui.button("Cancel", on_click=dialog.close)
                    async def _on_save(e):
                        # Kör bara koroutinen – NiceGUI hanterar await automatiskt i bakgrunden
                        await self.add_allocation(
                            {
                                "contract_id": contract_select.value,
                                "candidate_ids": candidate_select.value,
                                "allocation_percent": alloc_percent.value
                            }
                        )
                        dialog.close()

                    ui.button("Save", on_click=_on_save).classes("bg-blue-500 text-white")
        dialog.open()
           


#--- WORKING HOURS DF FUNCTION ---



