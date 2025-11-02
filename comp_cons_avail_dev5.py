import pandas as pd
import random
from nicegui import ui, events

def add_row() -> None:
    if not table.rows:
        ui.notify("Ingen rad att duplicera")
        return
    last_row = table.rows[-1].copy()
    new_id = max(row['row_id'] for row in table.rows) + 1
    last_row['row_id'] = new_id
    # Lägg till i tabellen
    table.rows.append(last_row)
    table.update()
    ui.notify(f"Duplicerade sista raden som ID {new_id}")

def get_df():   
    namn = [f'Namn_{i}' for i in range(1, 11)]
    projekt = [f'Projekt_{chr(65+i)}' for i in range(10)]
    månader = ['jan', 'feb', 'mar', 'apr', 'maj', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec']

    data = []
    for n, p in zip(namn, projekt):
        rad = {'namn': n, 'projekt': p}
        rad.update({m: random.randint(10, 100) for m in månader})
        data.append(rad)

    df = pd.DataFrame(data)
    df['row_id'] = df.index
    return df


df = get_df()
columns = [{'name': col, 'label': col, 'field': col, 'sortable': True} for col in df.columns]

def rename(e: events.GenericEventArguments) -> None:
    print(e.args)
    for row in table.rows:
        if row['row_id'] == e.args['row_id']:
            row.update(e.args)
    ui.notify(f'Updated row {e.args["row_id"]}')
    table.update()

def delete(e: events.GenericEventArguments) -> None:
    table.rows[:] = [row for row in table.rows if row['row_id'] != e.args['row_id']]
    ui.notify(f'Deleted row {e.args["row_id"]}')
    table.update()

table = ui.table(
    columns=[{'name': 'delete', 'label': '', 'field': 'delete'}] + columns,
    rows=df.to_dict('records'),
    row_key='id'
).classes('w-full')

# Header slot
table.add_slot('header', r'''
<q-tr :props="props">
    <q-th auto-width />
    <q-th v-for="col in props.cols" :key="col.name" :props="props">
        {{ col.label }}
    </q-th>
</q-tr>
''')

# Body slot: dynamiskt generera popup-edit för varje kolumn
table.add_slot('body', r'''
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
</q-tr>
''')

# Bottom row
with table.add_slot('bottom-row'):
    with table.cell().props(f'colspan={len(columns)+1}'):
        ui.button('Add row', icon='add', color='accent', on_click=add_row).classes('w-60')

table.on('rename', rename)
table.on('delete', delete)

ui.run(port=8004)
