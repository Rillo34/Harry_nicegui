from nicegui import ui

ui.add_head_html('''
<script>
window.getStatusColor = function(v) {
    return v==='EXCELLENT' ? 'green' :
           v==='BAD'       ? 'red' :
           v==='OK'        ? 'orange' :
           'grey-6';
};
</script>
''')

rows = [
    {'id': 1, 'status': 'EXCELLENT'},
    {'id': 2, 'status': 'BAD'},
    {'id': 3, 'status': 'OK'},
]

columns = [
    {'name': 'id', 'label': 'ID', 'field': 'id'},
    {'name': 'status', 'label': 'Status', 'field': 'status'},
]

table = ui.table(columns=columns, rows=rows).classes('w-full')

with table.add_slot('body-cell-status'):
    with table.cell():
        ui.badge().props('''
            :color="getStatusColor(props.value)"
            :label="props.value"
            text-color="white"
        ''')

ui.run(port=8002)