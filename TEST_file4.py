import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype

from nicegui import ui

df = pd.DataFrame(data={
    'col1': [x for x in range(4)],
    'col2': ['This', 'column', 'contains', 'strings.'],
    'col3': [x / 4 for x in range(4)],
    'col4': [True, False, True, False],
})

def update(*, df: pd.DataFrame, r: int, c: int, value):
    df.iat[r, c] = value
    ui.notify(f'Set ({r}, {c}) to {value}')

def delete_row(r):
    df.drop(index=r, inplace=True)
    ui.notify(f'Deleted row {r}')
    ui.refresh()  # kräver NiceGUI 1.4+

with ui.grid(rows=len(df.index)+1).classes('grid-flow-col'):
    for c, col in enumerate(df.columns):
        ui.label(col).classes('font-bold')

        for r, row in enumerate(df.loc[:, col]):

            # välj komponent baserat på dtype
            if is_bool_dtype(df[col].dtype):
                cls = ui.checkbox
                extra = {}
            elif is_numeric_dtype(df[col].dtype):
                cls = ui.number
                extra = {"step": 10}
            else:
                cls = ui.input
                extra = {}

            cls(
                value=row,
                on_change=lambda event, r=r, c=c: update(df=df, r=r, c=c, value=event.value),
                **extra
            )

    # Lägg till en extra kolumn med knappar
    ui.label("Actions").classes("font-bold")
    for r in range(len(df.index)):
        with ui.row():
            ui.button("Delete", color="red", on_click=lambda r=r: delete_row(r))
            ui.button("Info", on_click=lambda r=r: ui.notify(f"Row {r}: {df.iloc[r].to_dict()}"))

ui.run(port =8002)