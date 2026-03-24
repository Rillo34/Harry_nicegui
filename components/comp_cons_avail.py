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

ui.add_head_html("""
<style>
.q-table__tr.summary-row {
    background-color: #e3f2fd !important;  /* ljusblå */
    font-weight: 700 !important;
}
.q-table__tr.summary-row td {
    background-color: inherit !important;
}
</style>
""")

ui.add_head_html('''
    <script>
        function getColorClass(val) {
            if (val === null || isNaN(val)) return '';
            if (val <= 0.2) return 'bg-green-100 text-green-800';
            if (val <= 0.5) return 'bg-yellow-100 text-yellow-800';
            if (val <= 0.8) return 'bg-orange-100 text-orange-800';
            return 'bg-red-100 text-red-800';  // > 0.8 → rött
        }
    </script>
''')



class DataTable:
    def __init__(self, df: pd.DataFrame, title="Table", hidden_columns: List[str] = None, is_summary=False, alloc_table = False, perc_table = False, callbacks = None, top_rows = None  ):
        self.original_df = df.copy()
        self.df = df
        self.df_latest = df.copy()
        self.filtered_df = df
        self.title = title
        self.perc_table = perc_table
        self.alloc_table = alloc_table
        self.table = None
        callbacks = callbacks or {}
        self.change_step = 0.1
        self.add_alloc= callbacks.get("add_alloc")
        self.change_cell_alloc = callbacks.get("change_cell_alloc")
        self.delete_allocation = callbacks.get("delete_row")
        self.change_step_alloc = callbacks.get("change_alloc")
        print("top rows in init", top_rows)
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

    async def delete_row (self):
        print("ska deleta rows:", self.selected_rows)
        if self.selected_rows:
            await self.delete_allocation (self.selected_rows)
        else:
            ui.notify("No rows selected for deletion", color="red")
    
    async def change_alloc(self, step):
        print("ska ändra row:s:", self.selected_rows, "med step:", step)
        if not self.selected_rows:
            ui.notify("No rows selected for changing allocation", color="red")
            return
        await self.change_step_alloc(self.selected_rows, step=step)

    async def change_cell_alloc(self, row, col, new_value):
        print("ska ändra en cell", row, col, new_value)
        await self.change_cell_alloc(row, col, new_value)

# -----------------------------
# RENDER AND UPDATE
# -----------------------------

    def update(self, new_df: pd.DataFrame, group_by = False):
        self.table.update_from_pandas(new_df)
        if not group_by:
            self.df_latest = new_df
        
        if self.is_summary:
            self.add_summary_row()

            self.table.rows = [self.summary_row] + self.top_rows + self.table.rows  # 4. Uppdatera UI igen
            self._format_rows(self.table.rows)
            self.table.update() 

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
                inc_button = ui.button(text = "add 10%", icon="arrow_upward", color ='grey', on_click = lambda e: self.change_alloc(self.change_step)).bind_enabled_from(self.radio, 'value', lambda v: v == 'None' )
                dec_button = ui.button(text = "sub 10%", icon="arrow_downward",  color = 'grey', on_click = lambda e: self.change_alloc(-self.change_step)).bind_enabled_from(self.radio, 'value', lambda v: v == 'None' )
                add_button = ui.button(text = "Add allocation", icon="add", color = 'blue', on_click = self.add_alloc).bind_enabled_from(self.radio, 'value', lambda v: v == 'None' )

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
            {'name': c, 'label': c, 'field': c, 'sortable': True}
            for c in self.visible_columns]

        with ui.card().classes('w-full') as container:
            container.style('height: 700px;')

            self.table = ui.table(
                columns=columns,
                rows=rows,
                row_key="id",
                selection=selection_mode,
                pagination={"rowsPerPage": 20}
            ).props('dense').classes('w-full no-wrap sticky-header')

            self.table.on('cell-edit', self._on_cell_edit)
            self.table.on_select(self.update_selected_row)  # eller ditt lambda-notify

            # Fixa cell-klick utan att störa selection
            for col in self.month_cols:
                # self.table.add_slot(f"body-cell-{col}", f"""
                #     <q-td :props="props" class="cursor-pointer"
                #         @click.stop="$parent.$emit('cell-click', {{row: props.row, col: '{col}'}})">
                #         {{{{ props.row['{col}'] }}}}
                #     </q-td>
                # """)
                # self.table.add_slot(f"body-cell-{col}", f"""
                #     <q-td :props="props" class="cursor-pointer bg-red-100"
                #         @click.stop="$emit('cell-click', {{row: props.row, col: '{col}'}}); $q.notify('Klick på {col}!!!')">
                #         {{{{ props.value }}}}   <!-- ← props.value är oftast snyggare än props.row[col] -->
                #     </q-td>
                # """)
                
                col_str = str(col)
                self.table.add_slot(f'body-cell-{col_str}', f'''
                    <q-td :props="props" class="cursor-pointer" 
                        @click="$parent.$emit('cell-click', {{ row: props.row, col: '{col_str}' }})">
                        {{{{ props.value }}}}
                    </q-td>
                ''')

            # Valfrir "select all" checkbox i header (bra för multiple)
            if selection_mode == 'multiple':
                self.table.add_slot('header-selection', r'''
                    <q-th auto-width>
                        <q-checkbox dense v-model="props.selected" @click.stop="props.selectAll(false)" />
                    </q-th>
                ''')

        # ... resten av din kod ...
        
        # self.table.on("cell-click", lambda e: self.open_edit_dialog(e.args["row"], e.args["col"]))
        # self.table.on("cell-click", lambda e: ui.notify(f"Klick på cell i kolumn {e.args['col']} för kontrakt {e.args['row']['contract_id']}"))  # Temporär notis för att testa cell-click
        # Nu körs notisen VARJE gång eventet triggas
        # Nu skickar vi vidare den data vi just såg i notisen till din dialog-funktion
        self.table.on('cell-click', lambda e: self.open_edit_dialog(e.args['row'], e.args['col'])) # Lyssna på custom eventet och visa notis
        
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
                        "description": "first",
                        **{m: "sum" for m in self.month_cols},
                    }
                )
                .reset_index()
            )
        df["Total"] = df[self.month_cols].sum(axis=1)
        df = df.round(1)
        self.update(df, group_by=True)

    def _on_cell_edit(self, e): 
        print("Cell edit event args:", e.args)
        data = e.args[0] 
        ui.notify(f"Saving value {data['value']} for contract {data['contract_id']}, candidate {data['candidate_id']}, month {data['month']}")



    def open_edit_dialog(self, row, col):
        print(f"Opening edit dialog for row: {row}, column: {col}")
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
            new_value = self.edit_value.value
            edit_dialog.close()
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

        
# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

    def add_summary_row(self):
        summary = {}
        if self.df_latest.empty:
            for col in self.df_latest.columns:
                summary[col] = ''
        else:
            for col in self.filtered_df.columns:
                if col in self.month_cols:
                    summary[col] = round(self.filtered_df[col].sum(), 1)
                else:
                    summary[col] = ''
            summary["contract id"] = "Total"  # eller "Summary"
        summary["id"] = "summary"  # Viktigt för att inte kollidera med riktiga rader
        self.summary_row = summary

    def add_top_rows(self):
        self.top_rows = []

        # --- CAPACITY ---
        capacity = {}
        print("Adding capacity row with dict:", self.capacity_dict)
        for col in self.filtered_df.columns:
            if col in self.month_cols:
                capacity[col] = self.capacity_dict.get(col, '')
            else:
                capacity[col] = ''
        capacity["contract_id"] = "Capacity"
        capacity["id"] = "summary_capacity"
        self.top_rows.append(capacity)
        # --- AVERAGE ---
        avg = {}
        print("Adding average row with dict:", self.average_dict)
        for col in self.filtered_df.columns:
            if col in self.month_cols:
                # avg[col] = round(self.average_dict.get(col, 0), 2)
                # eller procent:
                avg[col] = f"{self.average_dict.get(col, 0) * 100:.0f}%"
            else:
                avg[col] = ''
        avg["contract_id"] = "Average"
        avg["id"] = "summary_average"
        print("Average row to add:", avg)
        self.top_rows.append(avg)
        print("Top rows after adding average:", self.top_rows)

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

        

    

    


