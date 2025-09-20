from nicegui import ui

# Dummydata för kandidater
rows = [
    {'id': 1, 'name': 'Anna'},
    {'id': 2, 'name': 'Björn'},
    {'id': 3, 'name': 'Cecilia'},
]

# Dynamisk lista med statusar (t.ex. från databasen)
status_list = [
    {'key': 'contacted', 'label': 'Kontaktad'},
    {'key': 'interviewed', 'label': 'Intervjuad'},
    {'key': 'offered', 'label': 'Erbjuden'},
    {'key': 'rejected', 'label': 'Avslagen'},
]

# Tabell med meny längst till höger
table = ui.table(
    columns=[
        {'name': 'id', 'label': 'ID', 'field': 'id'},
        {'name': 'name', 'label': 'Namn', 'field': 'name'},
        {'name': 'actions', 'label': '', 'field': 'actions'},
    ],
    rows=rows,
    row_key='id'
).classes('w-full')

# Generera menyval från status_list
status_items_html = "\n".join([
    f'''
    <q-item clickable v-close-popup
        @click="$parent.$emit('menu_action', {{action: 'set_status', row_id: props.row.id, status: '{status['key']}'}})">
        <q-item-section>{status['label']}</q-item-section>
    </q-item>
    ''' for status in status_list
])

# Lägg till meny i tabellens actions-kolumn
table.add_slot(
    "body-cell-actions",
    f'''
    <q-td :props="props">
        <q-btn dense flat round icon="more_vert">
            <q-menu>
                <q-list style="min-width: 150px">
                    <q-item-label header>Status</q-item-label>
                    {status_items_html}
                </q-list>
            </q-menu>
        </q-btn>
    </q-td>
    '''
)

# Hantera menyval
ui.on('menu_action', lambda e: ui.notify(f"Status för kandidat {e.args['row_id']} satt till: {e.args['status']}"))

ui.run(port = 8003)
