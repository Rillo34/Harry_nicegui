import pandas as pd
from nicegui import ui

# 1. Skapa en exempel-DataFrame
data = {
    'Namn': ['Anna', 'Erik', 'Sara', 'Karl', 'Linn', 'Olof'],
    'Ålder': [28, 34, 22, 45, 31, 29],
    'Stad': ['Stockholm', 'Göteborg', 'Malmö', 'Uppsala', 'Lund', 'Kiruna']
}
df = pd.DataFrame(data)

# 2. Konvertera DF till format som NiceGUI-tabellen förstår
columns = [{'name': col, 'label': col, 'field': col} for col in df.columns]
rows = df.to_dict('records')

# 3. Skapa tabellen
table = ui.table(columns=columns, rows=rows, row_key='Namn').classes('w-full')

# 4. Applicera bakgrundsfärg på de tre översta raderna (index 0, 1, 2)
# Vi använder en enkel loop för att slippa skriva samma sak tre gånger
for row_index in range(3):
    table.set_row_style(row_index, 'background-color: #ffe082') # En snygg gul/orange nyans

ui.run(port=8002)