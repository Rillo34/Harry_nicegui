from nicegui import ui

rows = [
    {"id": 1, "name": "1-Open", "description": "desc1", "is_default": True},
    {"id": 2, "name": "2-In Progress", "description": "desc2", "is_default": False},
    {"id": 3, "name": "3-Contracted", "description": "desc3", "is_default": False},
    {"id": 4, "name": "On Hold", "description": "desc4", "is_default": False},
    {"id": 5, "name": "Cancelled", "description": "desc5", "is_default": False},
]

# --- Kolumndefinitioner ---
columns = [
    {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left', 'sortable': True},
    {'name': 'name', 'label': 'Name', 'field': 'name', 'align': 'left', 'sortable': True},
    {'name': 'description', 'label': 'Description', 'field': 'description', 'align': 'left', 'sortable': True},
    # {'name': 'is_default', 'label': 'Default', 'field': 'is_default', 'align': 'center', 'sortable': True},
    {'name': 'moveup', 'label': 'Move-up', 'align': 'center'}
]

# --- Skapa tabellen ---
# table = ui.table(
#     columns=columns,
#     rows=rows,
#     row_key='id',
# ).props('dense bordered hover flat').classes('w-3/4 mx-auto mt-10')
table = ui.table(columns=columns, rows=rows)
# table.add_slot('body-cell-moveup', '''
#     <q-td :props="props">
#         <q-btn label="Notify" @click="() => $parent.$emit('notify', props.row)" flat />
#     </q-td>
# ''')
table.add_slot('body-cell-moveup', r'''
    <q-td :props="props" style="text-align: center;">
        <q-btn flat round dense icon="arrow_upward" color="primary"
            @click="() => $parent.$emit('notify', props.row)" />
    </q-td>
    ''')

table.on('notify', lambda e: ui.notify(f'Hi {e.args["name"]}!'))

ui.run(port = 8004)