import pandas as pd
from nicegui import ui

# Skapa en exempel-DF med decimaltal
df = pd.DataFrame({
    'kontrakt': ['Projekt A', 'Projekt B'],
    'jan': [0.5, 1.0],  # 50% och 100%
    'feb': [0.1, 0.8],
})

# Konvertera DF till list-format för ui.table
rows = df.to_dict('records')
manader = ['jan', 'feb']

columns = [
    {'name': 'kontrakt', 'label': 'Kontrakt', 'field': 'kontrakt', 'align': 'left'},
]
for m in manader:
    columns.append({
        'name': m, 
        'label': m.capitalize(), 
        'field': m,
        # Formatera talet som procent i visningsläget (valfritt, slotten skriver över detta)
    })

def bulk_update_pct(delta: float):
    if not table.selected:
        ui.notify('Välj rader först')
        return
    for row in table.selected:
        for m in manader:
            row[m] = round(row.get(m, 0) + delta, 2)
    table.update()

with ui.column().classes('w-full q-pa-md'):
    with ui.row():
        ui.button('+10%', on_click=lambda: bulk_update_pct(0.1)).props('color=green')
        ui.button('-10%', on_click=lambda: bulk_update_pct(-0.1)).props('color=red')

    table = ui.table(columns=columns, rows=rows, selection='multiple', row_key='kontrakt').classes('w-full')

    # Slot för att visa och editera som %
    for m in manader:
        table.add_slot(f'body-cell-{m}', f'''
            <q-td :props="props">
                {{{{ (props.row.{m} * 100).toFixed(0) }}}} %
                
                <q-popup-edit v-model.number="props.row.{m}" v-slot="scope" buttons>
                    <q-input 
                        v-model.number="scope.value" 
                        type="number" 
                        step="0.1" 
                        prefix="Prop:"
                        hint="0.1 = 10%"
                        dense 
                        autofocus 
                        @keyup.enter="scope.set" 
                    />
                </q-popup-edit>
            </q-td>
        ''')

ui.run()


self.table.add_slot('body', r'''
        <template v-slot:body="props">
            <q-tr :props="props"
                :class="props.row.contract_id === ''   ? 'bg-red-100 text-red-900' :
                        props.row.contract_id === '1' ? 'bg-orange-100 text-orange-900' :
                        'hover:bg-gray-50'">

                <q-td auto-width>
                    <q-checkbox v-model="props.selected" dense />
                </q-td>

                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                    {{ props.row[col.field] }}
                </q-td>

            </q-tr>
        </template>
        ''')