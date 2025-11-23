import pandas as pd
from nicegui import ui

# --- Data ---
df = pd.DataFrame({
    'Namn': ['Anna', 'Björn', 'Cecilia', 'David'],
    'Ålder': [25, 30, 28, 33],
    'Poäng': [12.5, 8.0, 15.0, 9.5],
    'Aktiv': [True, False, True, True]
})

# --- Event: uppdatera df när cell ändras ---
def on_cell_change(event):
    row = event.args['rowIndex']
    col = event.args['colDef']['field']
    value = event.args['newValue']

    # konvertera numeriska värden
    if pd.api.types.is_numeric_dtype(df[col]):
        value = pd.to_numeric(value, errors='ignore')

    df.at[row, col] = value
    ui.notify(f'{col} för {df.at[row,"Namn"]} → {value}')

# --- Kolumndefinitioner ---
column_defs = [
    {'field': 'Namn', 'pinned': 'left', 'editable': False},
    {'field': 'Ålder', 'editable': True, 'cellEditor': 'agNumberCellEditor'},
    {'field': 'Poäng', 'editable': True, 'cellEditor': 'agNumberCellEditor'},
    {'field': 'Aktiv', 'editable': True, 'cellEditor': 'agSelectCellEditor', 'cellEditorParams': {'values': [True, False]}},
]

# --- Grid ---
grid = ui.aggrid({
    'rowData': df.to_dict('records'),
    'columnDefs': column_defs,
    'defaultColDef': {
        'sortable': True,   # pilar i header
        'filter': True,
        'resizable': True,
        'editable': True
    },
    'enableRangeSelection': True,
    'singleClickEdit': True,  # klicka direkt för edit → spinner-pilar syns direkt
}).on('cellValueChanged', on_cell_change)

ui.run(port=8005)
