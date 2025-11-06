import pandas as pd
import random
from nicegui import ui, events
import asyncio

# from nicegui.async_run import run_task

class DataModelTable:
    def __init__(self, df: pd.DataFrame, API_client) -> None:
        self.API_client = API_client
        self.controller = API_client.controller
        self.df = df.copy()
        self.columns = [{'name': col, 'label': col, 'field': col, 'sortable': True} 
        for col in self.df.columns
        if col != "is_default"]

        rows= self.df.to_dict('records')
        #   --- Build UI
        ui.label('Data Model Editor').classes('text-h5 q-mb-md')
        ui.label('Click on a cell to edit its value. Use the buttons to add, delete, or move rows.\n'
        'Top row is 1st state (default)').classes('text-subtitle2 q-mb-md').style('white-space: pre-line;')
        # ui.splitter()
        self.table = ui.table(
            columns=[{'name': 'delete', 'label': '', 'field': 'delete'}] + self.columns,
            rows=rows,
            row_key='id'
        )
        ui.button('SAVE model', icon='save', color='primary', on_click=self.save_table).classes('q-mt-md')


        # Header slot
        self.table.add_slot('header', r'''
        <q-tr :props="props">
            <q-th auto-width />
            <q-th v-for="col in props.cols" :key="col.name" :props="props">
                {{ col.label }}
            </q-th>
        </q-tr>
        ''')
        self.table.add_slot('body-cell-moveup', r'''
            <q-td :props="props" style="text-align: center;">
                <q-btn flat round dense icon="arrow_upward" color="primary"
                    @click="() => $parent.$emit('notify', props.row)" />
            </q-td>
            ''')

        # Body slot: dynamiskt generera popup-edit för varje kolumn
        self.table.add_slot('body', r'''
        <q-tr :props="props">
            <q-td auto-width>
                <q-btn size="sm" color="warning" round dense icon="delete"
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
            <q-td auto-width>
                <q-btn flat round dense icon="arrow_upward" color="primary"
                    @click="() => $parent.$emit('arrow_up', props.row)" />
            </q-td>
            <q-td auto-width>
                <q-btn flat round dense icon="arrow_downward" color="primary"
                    @click="() => $parent.$emit('arrow_down', props.row)" />
            </q-td>
        </q-tr>
        ''')

        # Bottom row
        with self.table.add_slot('bottom-row'):
            with self.table.cell().props(f'colspan={len(self.columns)+1}'):
                ui.button('Add row', icon='add', color='accent', on_click=self.add_row).classes('w-30')

        self.table.on('rename', self.rename)
        self.table.on('delete', self.delete)
        self.table.on('arrow_up', lambda e: self.move_row(e, direction='up'))
        self.table.on('arrow_down', lambda e: self.move_row(e, direction='down'))



    def add_row(self) -> None:
        if not self.table.rows:
            ui.notify("Ingen rad att duplicera")
            return
        last_row = self.table.rows[-1].copy()
        new_id = max(row['id'] for row in self.table.rows) + 1
        last_row['id'] = new_id
        # Lägg till i tabellen
        self.table.rows.append(last_row)
        self.table.update()
        ui.notify(f"Duplicerade sista raden som ID {new_id}")

    def move_row(self, e: events.GenericEventArguments, direction: str) -> None:
        # Hitta index i df
        print(e.args)
        row_id = e.args['id']
        print("Row ID: ", row_id)
        print("Direction: ", direction)
        df_temp=pd.DataFrame(self.table.rows)

        idx = df_temp.index[df_temp['id'] == row_id]
        if direction == 'up':
            if idx == 0:
                ui.notify("Redan överst!")
                return
            swap_idx = idx - 1
        elif direction == 'down':
            if idx == len(df_temp) - 1:
                ui.notify("Redan längst ner!")
                return
            swap_idx = idx + 1
        else:
            ui.notify("Okänt riktning!")
            return
        # Byt plats på rader i df
        df_temp.iloc[idx], df_temp.iloc[swap_idx] = df_temp.iloc[swap_idx].copy(), df_temp.iloc[idx].copy()

        # Uppdatera table
        df_temp['id'] = range(1, len(df_temp) + 1)
        self.table.rows = df_temp.to_dict('records')
        self.table.update()


    def rename(self, e: events.GenericEventArguments) -> None:
        print(e.args)
        for row in self.table.rows:
            if row['id'] == e.args['id']:
                row.update(e.args)
        ui.notify(f'Updated row {e.args["id"]}')
        self.table.update()

    def delete(self,e: events.GenericEventArguments) -> None:
        self.table.rows[:] = [row for row in self.table.rows if row['id'] != e.args['id']]
        ui.notify(f'Deleted row {e.args["id"]}')
        self.table.update()

    async def send_model_to_backend(self):
        #send to backend
        print("Sending data model to backend...")
        print("list of states:", self.controller.job_states_list)
        print("name_list:", self.controller.job_states_name_list)
        print("mapping dict :", self.controller.job_states_mapping_dict)
        await self.API_client.api_put_new_datamodel()
        self.controller.job_states_mapping_dict = {}
        ui.notify("Data model sent to backend")


    async def save_table(self) -> None:
        print("Saving table...")
        def show_mapping_dialog(changed, new_names, df_new):
            print("Showing mapping dialog...")
            with ui.dialog() as dialog, ui.card():
                ui.label("Some earlier states are changed/removed, pls map to new states:").classes('text-h6')
                mappings = {}
                for old_state in changed:
                    with ui.row().classes('items-center q-gutter-sm'):
                        ui.label(old_state)
                        mappings[old_state] = ui.select(
                            options=new_names, 
                            label="Map to new state")

                async def confirm():
                    mapping_result = {old: sel.value for old, sel in mappings.items()}
                    print("Mapping:", mapping_result)
                    print("controller mapping before:", self.controller.job_states_mapping_dict)
                    self.controller.job_states_mapping_dict = mapping_result
                    records = df_new.to_dict('records')
                    if records:
                        records[0]['is_default'] = True
                        for r in records[1:]:
                            r['is_default'] = False
                    self.controller.job_states_list = records
                    self.controller.job_states_name_list = new_names
                    ui.notify("Mapping saved!")
                    dialog.close()
                    await self.send_model_to_backend()
                    ui.notify("Data model saved!")
                ui.button("Confirm mapping", color="primary", on_click=confirm)
            dialog.open()

        df_new = pd.DataFrame(self.table.rows)
        old_names = self.df['name'].tolist()
        new_names = df_new['name'].tolist()
        print("Old names: ", old_names)
        print("New names: ", new_names)
        changed = [n for n in old_names if n not in new_names]
        added = [n for n in new_names if n not in old_names]
        print("Changed or deleted states: ", changed)
        print("Added states: ", added)
        anychanged = bool(changed or added)

        if anychanged:
            if changed:
                ui.notify(f"Removed or changed states: {', '.join(changed)}")
                show_mapping_dialog(changed, new_names, df_new)
            elif added:
                ui.notify(f"Added new states only: {', '.join(added)}")
                self.controller.job_states_mapping_dict = {}
                ui.notify("Data model saved!")
                records = df_new.to_dict('records')
                if records:
                    records[0]['is_default'] = True
                    for r in records[1:]:
                        r['is_default'] = False
                self.controller.job_states_list = records
                self.controller.job_states_name_list = new_names
                await self.send_model_to_backend()

            self.df = df_new.copy()
        else:
            if old_names == new_names:  # "No changes made."
                ui.notify("No changes made to states.")
                return
            else:
                print("Order of states changed.")
                self.df = df_new.copy()
                records = df_new.to_dict('records')
                if records:
                    records[0]['is_default'] = True
                    for r in records[1:]:
                        r['is_default'] = False
                self.controller.job_states_list = records
                self.controller.job_states_name_list = new_names
                await self.send_model_to_backend()
                ui.notify("Data model saved!")
            


            


        

    
        



# def get_df():   
#         rows = [
#         {"id": 1, "name": "1-Open", "description": "desc1", "is_default": True},
#         {"id": 2, "name": "2-In Progress", "description": "desc2", "is_default": False},
#         {"id": 3, "name": "3-Contracted", "description": "desc3", "is_default": False},
#         {"id": 4, "name": "On Hold", "description": "desc4", "is_default": False},
#         {"id": 5, "name": "Cancelled", "description": "desc5", "is_default": False},
#         ]
#         df = pd.DataFrame(rows)
#         return df

# ui.run(port=8004)
