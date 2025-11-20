import pandas as pd
import random
from datetime import datetime, timedelta
from nicegui import ui, events
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime, date
import uuid
import os
import sys
# from TEST_file import populate_dummy_contracts_df
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from models import ContractRequest, ContractAllocation, CandidateAway



# 👇 Lägg CSS här – direkt efter importerna
ui.add_head_html("""
<style>
.q-table td, .q-table th {
    padding: 2px 6px !important;
    font-size: 16px !important;
    line-height: 1.2 !important;
}
.q-tr {
    height: 22px !important;
}
.q-btn {
    min-height: 18px !important;
    height: 18px !important;
    padding: 0 2px !important;
    font-size: 11px !important;
}
.q-input {
    font-size: 12px !important;
    height: 20px !important;
    padding: 0 4px !important;
}
.q-table__bottom, .q-table__top {
    padding: 0 !important;
    margin: 0 !important;
}
</style>
""")



class AllocationTable:
    def __init__(self, df_assignments: pd.DataFrame):
        self.original_df = df_assignments.copy()
        self.df_assignments = df_assignments.copy()
        self.df = df_assignments.copy()
        # self.df["row_id"] = range(len(self.df))
        self.columns = [{'name': col, 'label': col, 'field': col, 'sortable': True} for col in self.df.columns]
        self.create_table()
        self.create_filter()
        

    def create_filter(self):
        with ui.row().classes('items-center gap-2'):
            ui.label('Filter på projekt/kandidat: ')
            
            ui.input(placeholder='Skriv namn...', on_change=self.apply_filter).classes('w-64')
            # ui.input(
            #         label="Search",
            #         on_change=lambda e: self._update_search(e.value)
            #     ).classes('w-64')

    def apply_filter(self, e):
        search_term = e.value.lower()
        # filtrera baserat på candidate_id
        # filtered_df = self.original_df[self.original_df['candidate_id'].str.lower().str.contains(search_term)]
        for row in self.table:
            for field in ['candidate_id', 'project']:
                print(f"Filtering on field: {field}, searccing for: {search_term} on row: {row}")
                if search_term in str(field).lower():
                    search_match = True
                    print("we have a match")
                else:
                    search_match = False
        # self.df["row_id"] = range(len(self.df))
        # self.table.rows = self.df.to_dict('records')
        # self.table.update()
        
    def rename(self, e: events.GenericEventArguments) -> None:
        print(e.args)
        for row in self.table.rows:
            if row['row_id'] == e.args['row_id']:
                row.update(e.args)
        ui.notify(f'Updated row {e.args["row_id"]}')
        self.table.update()

    def delete(self, e: events.GenericEventArguments) -> None:
        self.table.rows[:] = [row for row in self.table.rows if row['row_id'] != e.args['row_id']]
        ui.notify(f'Deleted row {e.args["row_id"]}')
        self.table.update()

   

    def menu_action(e):
        # e innehåller x, y, target osv.
        print(f"Mouse clicked at x={e.args['x']}, y={e.args['y']}")
        print(f"Row data if available: {e.args.get('row')}")


    def create_table(self):
        with ui.tabs() as tabs:
            ui.tab('alloc', label='Allocate', icon='grid_4x4')
            ui.tab('project', label='Project', icon='functions')
            ui.tab('candidate', label='Candidate', icon='functions')
            ui.tab('avail', label='Input', icon='person_search')
        with ui.tab_panels(tabs, value='h').classes('w-full'):
            with ui.tab_panel('project'):
                ui.label('Summary per project/month')        
                rows = self.df.to_dict(orient='records')
                # Skapa kolumner
                columns = [{'name': col, 'label': col, 'field': col} for col in self.df.columns]
                self.table = ui.table(columns=columns, rows=rows).classes('dense w-full')
            # with ui.tab_panel('candidate'):
            #     def get_columns(df):
            #         return [
            #             {
            #                 'name': col,
            #                 'label': col,
            #                 'field': col,
            #                 'sortable': True,
            #             }
            #             for col in df.columns
            #         ]
            #     ui.label('Summary per candidate/month')
            #     df_candidate_month = self.df_assignments.pivot_table(
            #         index='candidate_id',
            #         columns='month',
            #         values='allocation_percent',
            #         aggfunc='sum',
            #         fill_value=0
            #     ).reset_index()
            #     # rows = df_candidate_month.to_dict(orient='records')
            #     columns = [{'name': col, 'label': col, 'field': col} for col in df_candidate_month.columns]
            #     columns = get_columns(df_candidate_month)
            #     candtable = ui.table(columns=columns, rows=rows).classes('dense w-full')
                
            #     print (df_candidate_month.head(5))
            with ui.tab_panel('a'):
                ui.label('Infos')

        # totals=[]
        # self.search_input = ui.input('Search')  
        # with ui.scroll_area().style('height: 100vh; overflow-x: auto;'):           
        #     self.table = ui.table(
        #         columns=[{'name': 'delete', 'label': '', 'field': 'delete'}] + self.columns,
        #         rows=self.df.to_dict('records'),
        #         row_key='row_id',
        #         ).classes('dense w-full')
        #     self.table.style('font-size: 13px; line-height: 0.7;')
        
        # self.search_input.bind_value(self.table, 'filter')
        self.table.add_slot('header', r'''
        <q-tr :props="props">
            <q-th auto-width />
            <q-th v-for="col in props.cols" :key="col.name" :props="props">
                {{ col.label }}
            </q-th>
        </q-tr>
        ''')
        # self.table.add_slot('top-row', f'''
        # <q-tr>
        #     <q-td auto-width></q-td>
        #     {''.join([f'<q-td>{{{{"{totals[col]}"}}}}</q-td>' for col in df_pivot.columns if col not in ["row_id"]])}
        # </q-tr>
        # ''')
        # Body slot: dynamiskt generera popup-edit för varje kolumn
        self.table.add_slot('body', r'''
        <q-tr :props="props">
            <q-td auto-width>
                <q-btn size="sm" color="warning" round dense flat icon="delete"
                    @click="() => $parent.$emit('delete', props.row)" />
            </q-td>
            <q-td v-for="col in props.cols" :key="col.name" :props="props">
                <template v-if="col.name !== 'delete'">
                    {{ props.row[col.field] }}
                    <q-popup-edit v-model="props.row[col.field]" v-slot="scope"
                        @update:model-value="() => $parent.$emit('rename', props.row)">
                        <q-input
                            :type="typeof props.row[col.field] === 'number' ? 'number' : 'text'"
                            v-model="scope.value"
                            dense autofocus counter
                            :step="typeof props.row[col.field] === 'number' ? 10 : undefined"
                            @keyup.enter="scope.set"
                        />
                    </q-popup-edit>
                </template>
            </q-td>
        </q-tr>
        ''')

        # Bottom row
        with self.table.add_slot('bottom-row'):
            with self.table.cell().props(f'colspan={len(self.columns)+1}'):
                ui.button('Add row', icon='add', color='accent', on_click=self.add_row).classes('w-60')
        # self.add_totals()
        self.table.on('rename', self.rename)
        self.table.on('delete', self.delete)

    def add_row(self) -> None:
        if not self.table.rows:
            ui.notify("Ingen rad att duplicera")
            return
        last_row = self.table.rows[-1].copy()
        new_id = max(row['row_id'] for row in self.table.rows) + 1
        last_row['row_id'] = new_id
        # Lägg till i tabellen
        self.table.rows.append(last_row)
        self.table.update()
        ui.notify(f"Duplicerade sista raden som ID {new_id}")


    def _update_search(self, value: str):
        self.search_term = value.lower()
        self.apply_filters()

    def apply_filters(self):
        filtered_rows = []
        for field in ['candidate_id', 'contract_id']:
            if field in cand and self.search_term in str(cand[field]).lower():
                search_match = True
                break
