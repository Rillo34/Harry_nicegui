from nicegui import ui

rows = [
    {'id': 1, 'namn': 'Anna', 'projekt': 'Projekt A', 'status': 'Pågående'},
    {'id': 2, 'namn': 'Bertil', 'projekt': 'Projekt B', 'status': 'Avslutat'},
]
columns = [
    {'name': 'namn', 'label': 'Namn', 'field': 'namn'},
    {'name': 'projekt', 'label': 'Projekt', 'field': 'projekt'},
    {'name': 'status', 'label': 'Status', 'field': 'status'},
]

table = ui.table(columns=columns, rows=rows, row_key='id').classes('w-full')

# --- Dialog definieras en gång ---
with ui.dialog() as dialog, ui.card().classes('p-6 w-[400px] text-center'):
    dialog_title = ui.label('Detaljer').classes('text-xl font-bold mb-2')
    dialog_content = ui.label('Här kommer mer information...')
    ui.button('Stäng', on_click=dialog.close).classes('mt-4')

# --- Slot med select ---
table.add_slot('body-cell-status', r'''
<q-td :props="props">
    <q-select
        v-model="props.row.status"
        :options="['Planerad', 'Pågående', 'Avslutat']"
        dense outlined
        emit-value
        map-options
        @update:model-value="() => $parent.$emit('status_change', props.row)"
    />
</q-td>
''')

# --- Event: öppna popup ---
def on_status_change(e):
    row = e.args
    dialog_title.text = f"Ändrat status för {row['namn']}"
    dialog_content.text = f"Projekt: {row['projekt']}\nNy status: {row['status']}"
    dialog.open()

table.on('status_change', on_status_change)

ui.run(port = 8004)
