from nicegui import ui

table = ui.table(
    columns=[{'name': 'name', 'label': 'Name', 'field': 'name'}],
    rows=[{'name': 'Alice'}, {'name': 'Bob'}, {'name': 'Charlie'}],
    row_key='name',
    on_select=lambda e: ui.notify(f'selected: {e.selection}'),
)

ui.run(port=8013)