from nicegui import ui
import pandas as pd

# -------------------------------
# Data (byt ut mot din egen)
data = {
    'Konsult': ['Anna', 'Erik', 'Sara', 'Johan', 'Maria', 'Lucas'],
    'Jan':    [85,  110,  60,   95,   45,   120],
    'Feb':    [90,   75,  105,  100,   30,    95],
    'Mar':    [100,  90,   70,  115,   80,    50],
    'Apr':    [95,  100,  85,   60,  110,    90],
}
df = pd.DataFrame(data)
# -------------------------------

def get_color(pct):
    pct = float(pct)
    if pct <= 50:    return 'bg-red-200 text-red-900'
    if pct <= 75:    return 'bg-yellow-200 text-yellow-900'
    if pct <= 105:   return 'bg-green-200 text-green-900'
    return 'bg-red-400 text-red-950 font-semibold'

# JavaScript-hjälpfunktion som körs i webbläsaren
ui.add_head_html(f'''
    <script>
        window.getAllocationColor = function(pct) {{
            pct = Number(pct);
            if (pct <= 50) return 'bg-red-200 text-red-900';
            if (pct <= 75) return 'bg-yellow-200 text-yellow-900';
            if (pct <= 105) return 'bg-green-200 text-green-900';
            return 'bg-red-400 text-red-950 font-semibold';
        }}
    </script>
''')

ui.markdown('### Konsultallokering per månad (%)')

table = ui.table.from_pandas(df).classes('w-full text-sm')

# Skapa snygga celler för alla månads-kolumner
for month in ['Jan', 'Feb', 'Mar', 'Apr']:
    table.add_slot(f'body-cell-{month}', r'''
        <q-td :props="props">
            <div class="text-center rounded px-3 py-1.5 min-w-[76px]"
                 :class="getAllocationColor(props.value)">
                {{ props.value }}%
            </div>
        </q-td>
    ''')

# Lite bättre utseende
table.classes('border shadow-sm rounded-lg')
ui.add_head_html('''
    <style>
        .q-table__cell { padding: 8px 6px !important; vertical-align: middle; }
    </style>
''')


ui.run(port = 8003)