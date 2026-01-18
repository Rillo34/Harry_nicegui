from nicegui import ui

columns = [
    {'name': 'name', 'label': 'Namn', 'field': 'name'},
    {'name': 'status', 'label': 'Status', 'field': 'status'},
    {'name': 'value', 'label': 'Värde', 'field': 'value'},
]

rows = [
    {'name': 'Server A', 'status': 'online',  'value': 98},
    {'name': 'Server B', 'status': 'warning', 'value': 65},
    {'name': 'Server C', 'status': 'error',   'value': 12},
    {'name': 'Server D', 'status': 'online',  'value': 87},
]

ui.table(columns=columns, rows=rows, row_key='name') \
    .props('dense') \
    .add_slot('body', r'''
        <q-tr :props="props"
              :class="props.row.status === 'error'   ? 'bg-red-100 text-red-900' :
                      props.row.status === 'warning' ? 'bg-orange-100 text-orange-900' :
                      'hover:bg-gray-50'">
            <q-td v-for="col in props.cols" :key="col.name" :props="props">
                {{ props.row[col.field] }}
            </q-td>
        </q-tr>
    ''')

ui.run()