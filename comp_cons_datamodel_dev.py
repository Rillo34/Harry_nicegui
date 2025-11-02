from nicegui import ui

# --- Exempeldata ---
statuses = [
    {"id": 1, "name": "1-Open", "is_default": True, "sort_order": 0},
    {"id": 2, "name": "2-In Progress", "is_default": False, "sort_order": 1},
    {"id": 3, "name": "3-Contracted", "is_default": False, "sort_order": 2},
    {"id": 4, "name": "On Hold", "is_default": False, "sort_order": 3},
    {"id": 5, "name": "Cancelled", "is_default": False, "sort_order": 4},
]

def get_statuses():
    return sorted(statuses, key=lambda s: s["sort_order"])

# --- Table ---
table = ui.table(
    columns=[
        {"name": "name", "label": "Name", "field": "name"},
        {"name": "is_default", "label": "Default", "field": "is_default"},
        {"name": "actions", "label": "Actions", "field": "actions"}
    ],
    rows=get_statuses(),
    row_key="id"
).classes("w-full")

# --- Flytta upp/ner exakt ett steg ---
def move_up(e):
    row = e.args
    idx = next(i for i, s in enumerate(statuses) if s["id"] == row["id"])
    if idx > 0:
        statuses[idx], statuses[idx-1] = statuses[idx-1], statuses[idx]
        # uppdatera sort_order så vi behåller unika värden
        for i, s in enumerate(statuses):
            s["sort_order"] = i
        table.rows = get_statuses()
        table.update()

def move_down(e):
    row = e.args
    idx = next(i for i, s in enumerate(statuses) if s["id"] == row["id"])
    if idx < len(statuses) - 1:
        statuses[idx], statuses[idx+1] = statuses[idx+1], statuses[idx]
        for i, s in enumerate(statuses):
            s["sort_order"] = i
        table.rows = get_statuses()
        table.update()

# --- Edit ---
def rename(e):
    row = e.args
    idx = next(i for i, s in enumerate(statuses) if s["id"] == row["id"])
    statuses[idx]["name"] = row["name"]
    statuses[idx]["is_default"] = row["is_default"]
    table.update()

# --- Delete ---
def delete(e):
    row = e.args
    global statuses
    statuses = [s for s in statuses if s["id"] != row["id"]]
    # uppdatera sort_order
    for i, s in enumerate(statuses):
        s["sort_order"] = i
    table.rows = get_statuses()
    table.update()

# --- Body slot med edit, flytta och delete ---
table.add_slot("body", r'''
<q-tr :props="props">
    <q-td key="name" :props="props">
        {{ props.row.name }}
        <q-popup-edit v-model="props.row.name" v-slot="scope"
            @update:model-value="() => $parent.$emit('rename', props.row)">
            <q-input v-model="scope.value" dense autofocus counter @keyup.enter="scope.set" />
        </q-popup-edit>
    </q-td>
    <q-td key="is_default" :props="props">
        {{ props.row.is_default }}
        <q-popup-edit v-model="props.row.is_default" v-slot="scope"
            @update:model-value="() => $parent.$emit('rename', props.row)">
            <q-toggle v-model="scope.value" dense />
        </q-popup-edit>
    </q-td>
    <q-td auto-width>
        <q-btn size="sm" color="primary" round dense icon="arrow_upward"
            @click="() => $parent.$emit('move_up', props.row)" />
        <q-btn size="sm" color="primary" round dense icon="arrow_downward"
            @click="() => $parent.$emit('move_down', props.row)" />
        <q-btn size="sm" color="negative" round dense icon="delete"
            @click="() => $parent.$emit('delete', props.row)" />
    </q-td>
</q-tr>
''')

table.on("move_up", move_up)
table.on("move_down", move_down)
table.on("rename", rename)
table.on("delete", delete)

ui.run(port=8005)
