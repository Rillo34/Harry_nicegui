import pandas as pd
import random
from nicegui import ui

# Konsulter och projekt
konsulter = ['Anna', 'Björn', 'Cecilia', 'David', 'Erik']
projekt = [f'Projekt {i+1}' for i in range(10)]
månader = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']

# Skapa allokeringar
data = []
for konsult in konsulter:
    aktiva_projekt = random.sample(projekt, k=random.randint(3, 6))  # varje konsult har 3–6 projekt
    for proj in aktiva_projekt:
        rad = {'Konsult': konsult, 'Projekt': proj}
        # Projektets aktiva månader
        start = random.randint(0, 8)
        slut = random.randint(start + 1, 12)
        for i, månad in enumerate(månader):
            rad[månad] = f"{random.choice(range(10, 101, 10))}" if start <= i < slut else ''
        data.append(rad)

df = pd.DataFrame(data)
projectlist = sorted(df['Projekt'].unique())
months = [col for col in df.columns if col not in ["Konsult", "Projekt"]]
df[months] = df[months].apply(pd.to_numeric, errors='coerce').fillna(0)
total_row = pd.DataFrame([["Total"] + df[months].sum().tolist()], columns=["Konsult"] + months)
df = pd.concat([df, total_row], ignore_index = True)
print("df igen: ", df)
df_sum = df.groupby('Konsult')[månader].sum().reset_index()
print(df_sum)

def filter(text):
    filtrerad_df = df[df.apply(lambda row: text.lower() in str(row).lower(), axis=1)]
    grid.options['rowData'] = filtrerad_df.to_dict('records')
    grid.update()

def filter_projects(valda_projekt):
    if valda_projekt:
        filtrerad_df = df[df['Projekt'].isin(valda_projekt)]
    else:
        filtrerad_df = df
    grid.options['rowData'] = filtrerad_df.to_dict('records')
    grid.update()

with ui.tabs().classes('w-full') as tabs:
    tab_detailed = ui.tab('Detailed')
    tab_summary = ui.tab('Summary')
with ui.tab_panels(tabs, value=2).classes('w-full'):
    with ui.tab_panel(tab_detailed):

        with ui.row().classes('items-center gap-4 w-full'):
            ui.input('Search', on_change=lambda e: filter(e.value)).classes('w-1/4')
            ui.select(
                options=projectlist,
                label='Filtrera på projekt',
                multiple=True,
                on_change=lambda e: filter_projects(e.value)
            ).classes('w-1/4')


        grid = ui.aggrid({
            'rowData': df.to_dict('records'),
            'columnDefs': [
                {'field': 'Konsult', 'pinned': 'left'},
                {'field': 'Projekt', 'pinned': 'left'},
            ] + [
                {'field': col, 'editable': True} for col in df.columns if col not in ['Konsult', 'Projekt']
            ],
            'defaultColDef': {
                'sortable': True,
                'filter': True,
                'resizable': True,
            },
            'enableRangeSelection': True,
            'suppressRowClickSelection': False,
        }).classes('w-full h-[800px]')

    with ui.tab_panel(tab_summary):
        grid_summary = ui.aggrid({
            'rowData': df_sum.to_dict('records'),
            'columnDefs': [
                {'field': 'Konsult', 'pinned': 'left'},
            ] + [
                {'field': col} for col in df_sum.columns if col != 'Konsult'
            ],
            'defaultColDef': {
                'sortable': True,
                'filter': True,
                'resizable': True,
            },
        }).classes('w-full h-[800px]')

ui.run()