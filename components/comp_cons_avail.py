# data_table.py
from tkinter import dialog
from tracemalloc import start
from nicegui import events
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
from backend.models import ContractRequest, ContractAllocation
import holidays
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))




class DataTable:
    def __init__(self, df: pd.DataFrame, title="Table", hidden_columns: List[str] = None, is_summary=False, alloc_table = False, 
                 perc_table = False, contract_table=False, callbacks = None, top_rows = None):
        self.original_df = df.copy()
        self.df = df
        self.name_list = []
        self.df_latest = df.copy()
        self.filtered_df = df
        self.title = title
        self.perc_table = perc_table
        self.alloc_table = alloc_table
        self.contract_table = contract_table
        self.table = None
        callbacks = callbacks or {}
        self.change_step = 0.1
        self.add_allocation= callbacks.get("add_alloc")
        self.change_cell_alloc = callbacks.get("change_cell_alloc")
        self.delete_allocation = callbacks.get("delete_row")
        self.change_step_alloc = callbacks.get("change_alloc")
        self.get_dialog_data = callbacks.get("get_dialog_data")
        self.update_notes = callbacks.get("update_notes")
        self.add_contract = callbacks.get("add_contract")
        self.delete_contract = callbacks.get("delete_contract")
        self.edit_contract = callbacks.get("edit_contract")
        self.nr_of_top_rows = 3 if perc_table else 1
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
        self.top_rows = []    
        if top_rows:
            self.capacity_dict = top_rows.get("capacity", {})
            self.average_dict = top_rows.get("utilisation", {})
            self.add_top_rows()
        self.render()   
        print("self top ", self.top_rows)
     

# -----------------------------
# API CALLS
# -----------------------------

    async def delete_row(self):
        if not self.selected_rows:
            ui.notify("No rows selected for deletion", color="red")
            return
        for row in self.selected_rows:
            payload=[{"contract_id":row["contract_id"],"candidate_id":row["candidate_id"]}]
            await self.delete_allocation(payload)
        ids={(r["contract_id"],r["candidate_id"]) for r in self.selected_rows}
        self.table.rows=[r for r in self.table.rows if (r["contract_id"],r["candidate_id"]) not in ids]
        self.selected_rows.clear()
        self.df_latest = self.df_latest[
            ~self.df_latest[["contract_id","candidate_id"]].apply(tuple, axis=1).isin(ids)
        ]
        self.update(self.df_latest)

    
    async def change_alloc(self, step):
        if not self.selected_rows:
            ui.notify("No rows selected", color="red")
            return
        # print(f"Changing allocation by {step*100:.0f}% for rows: {self.table.selected}")

        # delta = step / 100  # 10 -> 0.1, -10 -> -0.1
        

        # for r in self.selected_rows:
        #     mask = (self.df.contract_id == r["contract_id"]) & (self.df.candidate_id == r["candidate_id"])
        #     row = self.df.loc[mask]
        #     print(row)
        #     for m in self.month_cols:
        #         self.df.loc[mask, m] = (
        #             pd.to_numeric(self.df.loc[mask, m], errors="coerce")
        #             .fillna(0)
        #             + delta
        #         ).round(1)
        # print("AFTER UPDATE:")
        # print(self.df.loc[mask, self.month_cols])
        # self.update(self.df)
        await self.change_step_alloc(self.selected_rows, step=step)




    async def add_alloc(self):
        if not self.selected_rows:
            ui.notify("No rows selected for adding allocation", color="red")
            return
        if len(self.selected_rows) > 1:
            ui.notify("Please select only one row to copy/add allocation", color="red")
            return
        row = self.selected_rows
        name_list= await self.get_dialog_data(row)
        current_contract = row[0]['contract_id']
        with ui.dialog() as dialog:
            async def save_and_close():

                orig = self.df[
                    (self.df.contract_id == row[0]["contract_id"]) &
                    (self.df.candidate_id == row[0]["candidate_id"])
                ].iloc[0]

                new = orig.copy()
                # new["candidate_id"] = candidate_select.value
                new["candidate_name"] = candidate_select.value
                # new["candidate_name"] = self.df_latest.loc[self.df_latest['candidate_id'] == candidate_select.value, 'candidate_name'].values[0]
                new["id"] = f'{orig.contract_id}_{candidate_select.value}'

                for m in self.month_cols:
                    new[m] = round(orig[m] * (percent_input.value / 100), 1) if orig[m] > 0 else 0

                idx = orig.name
                self.df = pd.concat(
                    [self.df.iloc[:idx+1], new.to_frame().T, self.df.iloc[idx+1:]],
                    ignore_index=True
                )

                self.update(self.df)
                dialog.close()
                await self.add_allocation(row, candidate_select.value, percent_input.value)

            with ui.card().classes('p-4 w-96'):
                ui.label(f"Adding allocation to contract {current_contract}").classes("text-lg font-bold mb-4")
                candidate_select = ui.select(
                    options=name_list,
                    label="Candidate",
                    multiple=True
                ).classes("w-full")
                percent_input = ui.number(
                    label="Percent",
                    format="%.1f",
                    step=5,
                    value=50,
                    min=0,
                    max=100
                ).classes("w-full")
                with ui.row().classes("justify-end mt-4"):
                    ui.button("Cancel", on_click=dialog.close)
                    ui.button("Save", on_click=lambda: save_and_close()).classes("bg-blue-500 text-white")
        dialog.open()

    async def adding_contract(self, add_or_edit = "add"):
        row = self.selected_rows    
        print("row for contract dialog:", row)
        def year_month_list(year: int):
                return [f"{year}-{m:02d}" for m in range(1, 13)]

        def to_year_month(date_str):
            if not date_str:
                return None
            return datetime.fromisoformat(date_str).strftime("%Y-%m")
        
        with ui.dialog() as dialog:
            if add_or_edit == "add" or not row:
                # defaultvärden för nytt kontrakt
                contract_description_value = None
                contract_customer_value = None
                contract_total_hours_value = 100
                contract_start_date_value = None
                contract_end_date_value = None
                contract_notes_value = None
            else:
                # värden från vald rad
                r = row[0]
                contract_id = r.get("contract_id", "")
                contract_description_value = r.get("description", None)
                contract_customer_value = r.get("customer", None)
                contract_total_hours_value = r.get("contract_hours", 100)
                contract_start_date_value = to_year_month(r.get("start_date"))
                contract_end_date_value = to_year_month(r.get("end_date"))
                contract_notes_value = r.get("notes", None)
            
            year_month_list = year_month_list(2026)
            async def save_and_close():
                data = {
                    "description": contract_description.value,
                    "contract_hours": contract_total_hours.value,
                    "customer": contract_customer.value,
                    "start_month": contract_start_date.value,
                    "end_month": contract_end_date.value,
                    "notes": contract_notes.value,
                }
                if add_or_edit == "edit":
                    await self.edit_contract(contract_id, data)
                else:
                    await self.add_contract(data)
                dialog.close()
            
            with ui.card().classes('p-4 w-96'):
                ui.label("Adding contract").classes("text-lg font-bold mb-4")

                contract_description = ui.input(
                    label="Contract description",
                    value=contract_description_value
                ).classes("w-full")
                contract_customer = ui.input(
                    label="Customer",
                    value=contract_customer_value
                ).classes("w-full")
                contract_total_hours = ui.number(
                    label="Contract hours",
                    format="%.0f",
                    step=20,
                    value=contract_total_hours_value,
                    min=0
                ).classes("w-full")

                # Bättre layout för selects
                with ui.grid(columns=2).classes("w-full gap-2 mt-4"):
                    contract_start_date = ui.select(
                        options=year_month_list,
                        label="Start month",
                        value=contract_start_date_value
                    ).classes("w-full")
                    contract_end_date = ui.select(
                        options=year_month_list,
                        label="End month",
                        value=contract_end_date_value
                    ).classes("w-full")
                contract_notes = ui.input(
                    label="Notes",
                    value=contract_notes_value
                ).classes("w-full")
                # Knappar
                with ui.row().classes("justify-end gap-2 mt-4"):
                    ui.button("Cancel", on_click=dialog.close)
                    ui.button(
                        "Save",
                        on_click=lambda: save_and_close()
                    ).classes("bg-blue-500 text-white")
                dialog.open()
    
    async def editing_contract(self):
        if not self.selected_rows:
            ui.notify("No contract selected for editing", color="red")
            return
        if len(self.selected_rows) > 1:
            ui.notify("Please select only one contract to edit", color="red")
            return
        await self.adding_contract(add_or_edit="edit")
    
    async def deleting_contract(self):
        if not self.selected_rows:
            ui.notify("No contract selected for deletion", color="red")
            return
        if len(self.selected_rows) > 1:
            ui.notify("Please select only one contract to delete", color="red")
            return
        contract_id = self.selected_rows[0].get("contract_id")
        if not contract_id:
            ui.notify("Selected row does not have a valid contract_id", color="red")
            return
        await self.delete_contract(contract_id)


    def update(self, new_df: pd.DataFrame, top_rows = None ):
        # 1. Uppdatera FE-DF
        self.top_rows = top_rows if top_rows is not None else []
        self.df = new_df.copy()
        self.df[self.month_cols]=self.df[self.month_cols].apply(pd.to_numeric,errors="coerce").fillna(0)
        self.add_summary_row()
        self.add_top_rows()
        rows = (
            self.top_rows +
            [self.summary_row] +
            self._format_rows(self.df.to_dict(orient="records"))
        )
        self.table.rows = rows
        self.table.update()


    def render(self):
        df = self.df.copy()
            # summary_df = pd.DataFrame([
            #     {"label": "CAPACITY", "2026-04": 160, "2026-05": 152, "2026-06": 168},
            #     {"label": "TOTAL",    "2026-04": 124, "2026-05": 118, "2026-06": 132},
            #     {"label": "UTIL%",    "2026-04": "78%", "2026-05": "78%", "2026-06": "79%"},
            # ])
            # print(summary_df)
            # self.summary_table = ui.table.from_pandas(summary_df).props('dense')

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
                inc_button = ui.button(text = "add 10%", icon="arrow_upward", color ='grey', on_click = lambda e: self.change_alloc(self.change_step)).bind_enabled_from(self.radio, 'value', lambda v: v == 'None' )
                dec_button = ui.button(text = "sub 10%", icon="arrow_downward",  color = 'grey', on_click = lambda e: self.change_alloc(-self.change_step)).bind_enabled_from(self.radio, 'value', lambda v: v == 'None' )
                add_button = ui.button(text = "Copy/add allocation", icon="add", color = 'blue', on_click = self.add_alloc).bind_enabled_from(self.radio, 'value', lambda v: v == 'None' )

                ui.space()
                self.add_filter()
            elif self.contract_table:
                add_button = ui.button(text = "Copy/add contract", icon="add", color = 'blue', on_click = self.adding_contract)
                edit_button = ui.button(text = "Edit contract", icon="edit", color = 'grey', on_click = self.editing_contract)
                delete_button = ui.button(text = "Delete contract", icon="delete", color = 'red', on_click = self.deleting_contract)
                ui.space()
                self.add_filter()
            else:
                ui.space()
                self.add_filter()

        df = df.round(1)
        df = df.reset_index(drop=True)
        rows = df.to_dict(orient='records')
        rows = self._format_rows(rows)
        rows = [self.summary_row] + self.top_rows + rows
        # ... tidigare kod ...

        if self.perc_table:
            selection_mode = 'multiple'
        elif self.is_summary == True and not self.alloc_table:
            selection_mode = 'multiple'
        else:
            selection_mode = 'single'  # eller 'none'

        columns = [{'name': 'selection', 'label': '', 'field': 'selection', 'sortable': False}] + [
            {'name': c, 'label': c, 'field': c, 'sortable': True, 'align': 'left'}
            for c in self.visible_columns]
        
        self.table_container = ui.row().classes("w-full items-center").style('overflow-x: auto; height: 700px;')  # Lägg till horisontell scroll vid behov
        with self.table_container:
            self.table = ui.table(
            columns=columns,
            rows=rows,
            row_key="id",
            selection=selection_mode,
            pagination={"rowsPerPage": 20}
        ).props('dense').classes('w-full no-wrap sticky-header')

            top_cols = self.month_cols + ['candidate_name']

            for col in top_cols:
                col_str = str(col)
                self.table.add_slot(
                    f'body-cell-{col_str}',
                    f'''
                    <q-td :props="props"
                        class="cursor-pointer"
                        @click="$parent.$emit('cell-click', {{ row: props.row, col: '{col_str}', rowIndex: props.rowIndex }})"
                        :style="props.rowIndex < {self.nr_of_top_rows} ? 'background-color: #ffe082' : ''">
                        {{{{ props.value }}}}
                    </q-td>
                    '''
                )

            self.table.add_slot(f'body-cell-notes', f'''
                <q-td :props="props" class="cursor-pointer" 
                    @click="$parent.$emit('notes-click', {{ row: props.row, col: 'notes' }})">
                    {{{{ props.value }}}}
                </q-td>
            ''')
            self.table.add_slot(f'body-cell-fill_up', f'''
                <q-td :props="props" 
                    :style="parseFloat(props.value) < 100 
                        ? 'background-color: #d1fae5; color: #065f46' 
                        : 'background-color: #fee2e2; color: #991b1b'">
                    {{{{ props.value }}}}
                </q-td>
            ''')
                # self.table.add_slot('body-cell-candidate_name', r'''
                #     <q-td :props="props" 
                #         class="cursor-pointer"
                #         :class="hasTotalCapacity(props.row.candidate_name) ? 'bg-orange-4' : ''"
                #         @click="$parent.$emit('cell-click', { row: props.row, col: 'candidate_name' })">
                #         {{ props.value }}
                #     </q-td>
                # ''')
             
            # Valfrir "select all" checkbox i header (bra för multiple)
            if selection_mode == 'multiple':
                self.table.add_slot('header-selection', r'''
                    <q-th auto-width>
                        <q-checkbox dense v-model="props.selected" @click.stop="props.selectAll(false)" />
                    </q-th>
                ''')
        self.table.on_select(self.update_selected_row)  # eller ditt lambda-notify
        self.table.on('cell-click', lambda e: self.open_edit_dialog(e.args['row'], e.args['col'], e.args['rowIndex'])) # Lyssna på custom eventet och visa notis
        self.table.on('notes-click', lambda e: self.open_notes_dialog(e.args['row'], e.args['col'])) # Lyssna på custom eventet och visa notis
        # self.table.on('notes-click', lambda e: ui.notify(f"Notes clicked for row: {e.args['row']}, column: {e.args['col']}")) # Lyssna på custom eventet och visa notis
        
# -----------------------------
# FILTER AND GROUPING
# -----------------------------
    def _format_rows(self, rows):
        formatted_rows = []
        # Filtrera bort specialrader direkt
        target_rows = [r for r in rows if r.get("id") not in ["summary", "summary_capacity", "summary_average"]]
        for row in target_rows:
            new_row = dict(row)  # Skapa kopia för att undvika referensproblem
            for col in self.month_cols:
                val = new_row.get(col, 0)
                # Hantera None/NaN (viktigt för att emitEvent ska fungera)
                if val is None or (isinstance(val, float) and str(val) == 'nan'):
                    new_row[col] = ""
                elif isinstance(val, (int, float)):
                    if val == 0:
                        new_row[col] = ""
                    elif self.perc_table:
                        new_row[col] = f"{int(round(val * 100))}%"
                # Om värdet redan är en sträng behålls det som det är
            formatted_rows.append(new_row)
        return formatted_rows
    
    
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
                self.df_latest.groupby("candidate_name")
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
                        "candidate_name": lambda x: ", ".join(sorted(set(x))),
                        "description": "first",
                        **{m: "sum" for m in self.month_cols},
                    }
                )
                .reset_index()
            )
        df["Total"] = df[self.month_cols].sum(axis=1)
        df = df.round(1)
        self.update(df)


    def open_edit_dialog(self, row, col, rowIndex):
        print(f"Opening edit dialog for row: {row}, column: {col}, rowIndex: {rowIndex} ")
        if rowIndex < self.nr_of_top_rows:  # Första två raderna är summary och capacity, som inte ska redigeras
            ui.notify("This row cannot be edited", color="red")
            return
        try:
            real_value = self.df_latest.loc[self.df_latest['id'] == row['id'], col].values[0]
            print(f"Real value from DF for contract_id {row['contract_id']}, candidate_id {row['candidate_id']}, month {col}: {real_value}")
            if pd.isna(real_value):
                initial_value = 0.0
            else:
                initial_value = float(real_value)
        except Exception as e:
            print(f"Kunde inte hitta värde i DF: {e}")
            initial_value = 0.0

        async def save_edit():
            new_value = float(self.edit_value.value or 0)
            edit_dialog.close()
            self.df.loc[self.df['id'] == row['id'], col] = new_value
            self.update(self.df)
            await self.change_cell_alloc(row, col, new_value)

        with ui.dialog() as edit_dialog, ui.card():
            ui.label(f"Edit {col} allocation")
            # Här skickar vi in initial_value (som nu är en ren float från DF)
            self.edit_value = ui.number(
                "Värde (0.0 - 1.0)",
                format="%.2f",
                value=initial_value, 
                step=0.05,
                min=0,
                max=1
            ).classes('w-full')
            
            with ui.row():
                ui.button("Save", on_click=save_edit)
                ui.button("Cancel", on_click=edit_dialog.close).props('flat')

        edit_dialog.open()
    
    def open_notes_dialog(self, row, col):
        print(f"Opening notes dialog for row: {row}, column: {col}")        
        async def save_notes():
            new_value = self.edit_value.value
            print(f"Saving notes for contract {row['contract_id']} to: {new_value}")
            notes_dialog.close()
            new_row = row.copy()
            new_row[col] = new_value
            for r in self.table.rows:
                if r['id'] == row['id']:
                    r[col] = new_value
                    break
            self.table.update()
            await self.update_notes(row, col, new_value)            

        with ui.dialog() as notes_dialog, ui.card().classes('p-4 w-96'):
            ui.label("Update notes").classes("text-lg font-bold mb-4")
            # Här skickar vi in initial_value (som nu är en ren float från DF)
            self.edit_value = ui.input(
                value=row.get('notes', ''),
                placeholder="Enter notes here"
             ).classes('w-full')            
            with ui.row():
                ui.button("Save", on_click=save_notes)
                ui.button("Cancel", on_click=notes_dialog.close).props('flat')
        notes_dialog.open()

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
        if term == "":
            self.filtered_df = self.df_latest.copy()
            self.add_summary_row()
            self.table.rows = [self.summary_row] + self.top_rows + self._format_rows(self.filtered_df.to_dict(orient='records'))
            self.table.update()
            return
        for row in self.df.to_dict(orient='records'):
            if any(term in str(value).lower() for value in row.values()):                
                filtered.append(row)
        filtered = self._format_rows(filtered)
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

        
# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

    # def add_summary_row(self):
    #     summary = {}
    #     if self.df_latest.empty:
    #         for col in self.df_latest.columns:
    #             summary[col] = ''
    #     else:
    #         for col in self.filtered_df.columns:
    #             if col in self.month_cols:
    #                 summary[col] = round(self.filtered_df[col].sum(), 1)
    #             else:
    #                 summary[col] = ''
    #     summary["candidate_name"] = "TOTAL"  # eller "Summary"
    #     summary["id"] = "summary"  # Viktigt för att inte kollidera med riktiga rader
    #     self.summary_row = summary
    def add_summary_row(self):
        summary = {
            col: round(self.filtered_df[col].sum(), 1) if col in self.month_cols else ''
            for col in self.filtered_df.columns
        }
        summary["candidate_name"] = "TOTAL"
        summary["id"] = "summary"
        self.summary_row = summary

    def add_top_rows(self):
        self.top_rows = []

        # --- CAPACITY ---
        capacity = {
            col: self.capacity_dict.get(col, '') if col in self.month_cols else ''
            for col in self.filtered_df.columns
        }
        capacity["candidate_name"] = "CAPACITY"
        capacity["id"] = "summary_capacity"
        self.top_rows.append(capacity)

        # --- UTILISATION (TOTAL / CAPACITY) ---
        utilisation = {}
        for col in self.filtered_df.columns:
            if col in self.month_cols:
                cap = self.capacity_dict.get(col, 0)
                total = self.summary_row.get(col, 0)

                if cap and cap != 0:
                    utilisation[col] = f"{(total / cap) * 100:.0f}%"
                else:
                    utilisation[col] = ""
            else:
                utilisation[col] = ""

        utilisation["candidate_name"] = "UTILISATION"
        utilisation["id"] = "summary_average"
        self.top_rows.append(utilisation)


    # def add_top_rows(self):
    #     self.top_rows = []

    #     # --- CAPACITY ---
    #     capacity = {}
    #     print("Adding capacity row with dict:", self.capacity_dict)
    #     for col in self.filtered_df.columns:
    #         if col in self.month_cols:
    #             capacity[col] = self.capacity_dict.get(col, '')
    #         else:
    #             capacity[col] = ''
    #     capacity["candidate_name"] = "CAPACITY"
    #     capacity["id"] = "summary_capacity"
    #     self.top_rows.append(capacity)
    #     # --- AVERAGE ---
    #     avg = {}
    #     print("Adding average row with dict:", self.average_dict)
    #     for col in self.filtered_df.columns:
    #         if col in self.month_cols:
    #             # avg[col] = round(self.average_dict.get(col, 0), 2)
    #             # eller procent:
    #             avg[col] = f"{self.average_dict.get(col, 0) * 100:.0f}%"
    #         else:
    #             avg[col] = ''
    #     avg["candidate_name"] = "UTILISATION"
    #     avg["id"] = "summary_average"
    #     print("Average row to add:", avg)
    #     self.top_rows.append(avg)
    #     print("Top rows after adding average:", self.top_rows)

    def update_selected_row(self, e):
        self.selected_rows = self.table.selected
        print("Selected rows:", self.selected_rows)
        if self.perc_table:
            self.selected_rows = [ 
                { "contract_id": row["contract_id"], "candidate_id": row["candidate_id"] } 
                for row in self.selected_rows ]
        # else:
        #     self.selected_rows = [ row["contract_id"] for row in selected_rows ]
        print("Rader valda:", self.selected_rows)

        

    

    


