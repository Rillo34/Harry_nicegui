# file: simple_table_with_select_all.py
from typing import List, Dict
from nicegui import ui

# ----------------------------------------------------------------------
# Sample data
# ----------------------------------------------------------------------
data: List[Dict] = [
    {"id": 1, "name": "Alice", "age": 34, "city": "Stockholm"},
    {"id": 2, "name": "Bob",   "age": 27, "city": "Gothenburg"},
    {"id": 3, "name": "Cara",  "age": 41, "city": "Malmö"},
    {"id": 4, "name": "Dave",  "age": 19, "city": "Uppsala"},
]

# ----------------------------------------------------------------------
# State
# ----------------------------------------------------------------------
selected_rows: List[Dict] = []
row_checkboxes: Dict[int, ui.checkbox] = {}
select_all_checkbox: ui.checkbox = None

# ----------------------------------------------------------------------
# Update selected rows
# ----------------------------------------------------------------------
def update_selection():
    selected_rows.clear()
    for row in data:
        if row_checkboxes[row["id"]].value:
            selected_rows.append(row)
    label.set_text(f"Valda: {len(selected_rows)} rad(er)")
    # Uppdatera "Välj alla"-status (valfritt: halvmarkerad om vissa valda)
    all_checked = all(cb.value for cb in row_checkboxes.values())
    some_checked = any(cb.value for cb in row_checkboxes.values()) and not all_checked
    if all_checked:
        select_all_checkbox.value = True
        select_all_checkbox.props(remove='indeterminate')
    elif some_checked:
        select_all_checkbox.value = False
        select_all_checkbox.props('indeterminate')
    else:
        select_all_checkbox.value = False
        select_all_checkbox.props(remove='indeterminate')

# ----------------------------------------------------------------------
# Toggle all checkboxes
# ----------------------------------------------------------------------
def toggle_select_all():
    value = select_all_checkbox.value
    for cb in row_checkboxes.values():
        cb.value = value
        cb.run_method('update')  # Tvinga uppdatering
    update_selection()

# ----------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------
with ui.column().classes('w-full max-w-4xl mx-auto p-4'):
    ui.label('Enkel tabell med kryssrutor och "Välj alla"').classes('text-2xl font-bold mb-4')

    # Header med "Välj alla"
    with ui.row().classes('grid grid-cols-[40px_1fr_1fr_1fr] gap-2 font-semibold bg-gray-100 p-2 rounded-t'):
        select_all_checkbox = ui.checkbox(value=False).props('dense')
        select_all_checkbox.on_value_change(toggle_select_all)
        ui.label('Namn').classes('ml-2')
        ui.label('Ålder').classes('ml-2')
        ui.label('Stad').classes('ml-2')

    # Rader
    for item in data:
        with ui.row().classes('grid grid-cols-[40px_1fr_1fr_1fr] gap-2 items-center py-2 border-b hover:bg-gray-50'):
            cb = ui.checkbox(value=False).props('dense')
            row_checkboxes[item["id"]] = cb
            cb.on_value_change(update_selection)
            ui.label(item["name"]).classes('ml-2')
            ui.label(str(item["age"])).classes('ml-2')
            ui.label(item["city"]).classes('ml-2')

    # Info om val
    label = ui.label('Valda: 0 rad(er)').classes('mt-4 font-medium')

    # Knapp för att visa valda rader
    ui.button('Skriv ut valda rader', on_click=lambda: print(selected_rows)).classes('mt-2')

ui.run(title='NiceGUI – Enkel tabell med Välj alla')