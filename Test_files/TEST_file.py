from nicegui import ui
import random

# Exempeldatabas (kan bytas ut mot din egen data)
data = [
    {'id': 1, 'project': 'Website redesign', 'owner': 'Anna', 'allocation_percent': 45, 'status': 'active'},
    {'id': 2, 'project': 'Mobile app v2', 'owner': 'Erik', 'allocation_percent': 80, 'status': 'review'},
    {'id': 3, 'project': 'API migration', 'owner': 'Sara', 'allocation_percent': 20, 'status': 'planning'},
    {'id': 4, 'project': 'Database optimization', 'owner': 'Johan', 'allocation_percent': 100, 'status': 'done'},
    {'id': 5, 'project': 'Security audit', 'owner': 'Maria', 'allocation_percent': 65, 'status': 'active'},
]

def format_percent(value):
    return f"{value}%"

with ui.card().classes('w-full max-w-5xl mx-auto mt-6'):
    ui.label('Resource Allocation').classes('text-2xl font-bold mb-4')

    table = ui.table(
        columns=[
            {'name': 'project',     'label': 'Project',         'field': 'project',     'align': 'left'},
            {'name': 'owner',       'label': 'Owner',           'field': 'owner',       'align': 'left'},
            {'name': 'allocation',  'label': 'Allocation',      'field': 'allocation_percent', 'align': 'center'},
            {'name': 'status',      'label': 'Status',          'field': 'status',      'align': 'center'},
        ],
        rows=data,
        row_key='id',
        pagination={'rowsPerPage': 10}
    ).classes('w-full')

    # Gör kolumnen "allocation" till en custom cell med progressbar
    def render_progress_cell(row):
        percent = row['allocation_percent']
        color = 'text-positive' if percent >= 90 else \
                'text-warning' if percent >= 70 else \
                'text-negative' if percent <= 30 else \
                ''

        with ui.row().classes('items-center gap-3 w-full justify-center'):
            ui.label(format_percent(percent)).classes(f'font-mono w-14 text-right {color}')
            with ui.element('div').classes('w-32 h-5 bg-grey-3 rounded-full overflow-hidden'):
                ui.element('div').classes(f'h-full rounded-full transition-all duration-500') \
                    .style(f'width: {percent}%; background: linear-gradient(to right, #4ade80, #22c55e);') \
                    .tooltip(f'{percent}% allokerat')

    # Använd custom render-funktion för just allocation-kolumnen
    table.add_slot('body-cell-allocation', '''
        <q-td key="allocation" :props="props">
            <div class="flex items-center gap-3 justify-center">
                <q-linear-progress
                    :value="props.row.allocation_percent / 100"
                    size="20px"
                    :color="props.row.allocation_percent >= 90 ? 'positive' : props.row.allocation_percent >= 70 ? 'warning' : props.row.allocation_percent <= 30 ? 'negative' : 'primary'"
                    track-color="grey-3"
                    class="w-32"
                />
                <span class="font-mono text-sm w-10 text-right">
                    {{ props.row.allocation_percent }}%
                </span>
            </div>
        </q-td>
    ''')

    # Alternativ 2: ren python-renderad variant (utan Quasar-komponent)
    # table.columns[2]['render'] = render_progress_cell



ui.run(port = 8003)