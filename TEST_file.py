from nicegui import ui

# # Dummydata för kandidater
# rows = [
#     {'id': 1, 'name': 'Anna'},
#     {'id': 2, 'name': 'Björn'},
#     {'id': 3, 'name': 'Cecilia'},
# ]

# # Dynamisk lista med statusar (t.ex. från databasen)
# status_list = [
#     {'key': 'contacted', 'label': 'Kontaktad'},
#     {'key': 'interviewed', 'label': 'Intervjuad'},
#     {'key': 'offered', 'label': 'Erbjuden'},
#     {'key': 'rejected', 'label': 'Avslagen'},
# ]

# # Tabell med meny längst till höger
# table = ui.table(
#     columns=[
#         {'name': 'id', 'label': 'ID', 'field': 'id'},
#         {'name': 'name', 'label': 'Namn', 'field': 'name'},
#         {'name': 'actions', 'label': '', 'field': 'actions'},
#     ],
#     rows=rows,
#     row_key='id'
# ).classes('w-full')

# # Generera menyval från status_list
# status_items_html = "\n".join([
#     f'''
#     <q-item clickable v-close-popup
#         @click="$parent.$emit('menu_action', {{action: 'set_status', row_id: props.row.id, status: '{status['key']}'}})">
#         <q-item-section>{status['label']}</q-item-section>
#     </q-item>
#     ''' for status in status_list
# ])

# # Lägg till meny i tabellens actions-kolumn
# table.add_slot(
#     "body-cell-actions",
#     f'''
#     <q-td :props="props">
#         <q-btn dense flat round icon="more_vert">
#             <q-menu>
#                 <q-list style="min-width: 150px">
#                     <q-item-label header>Status</q-item-label>
#                     {status_items_html}
#                 </q-list>
#             </q-menu>
#         </q-btn>
#     </q-td>
#     '''
# )

# # Hantera menyval
# # ui.on('menu_action', lambda e: ui.notify(f"Status för kandidat {e.args['row_id']} satt till: {e.args['status']}"))

import pandas as pd
import random
from datetime import date, timedelta

# -----------------------------
# Hjälpfunktioner
# -----------------------------
def months_between(start: date, end: date) -> list[str]:
    """Returnerar en lista med YYYY-MM mellan start och end."""
    months = []
    current = date(start.year, start.month, 1)
    while current <= end:
        months.append(current.strftime("%Y-%m"))
        # hoppa till nästa månad
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return months


def populate_dummy_contracts_df(num_contracts: int = 5, num_candidates: int = 12):
    candidates = [f"CAND_{i+1}" for i in range(num_candidates)]
    contracts = []
    assignments = []

    for i in range(num_contracts):
        start_date = date.today() - timedelta(days=random.randint(0, 60))
        end_date = start_date + timedelta(days=random.randint(60, 360))

        contract_id = i + 1
        project_name = f"Projekt{contract_id}"
        job_id = f"JOB_{random.randint(1, 10)}"
        contracts.append({
            "contract_id": contract_id,
            "project": project_name,
            "job_id": job_id,
            "description": f"Dummy contract {contract_id} for {job_id}",
            "start_date": start_date,
            "end_date": end_date,
            "contract_type": random.choice(["consulting", "employment"]),
            "status": random.choice(["active", "completed", "void"]),
            "estimated_value": round(random.uniform(50000, 250000), 2),
            "hours": random.randint(40, 160),
            "notes": random.choice([None, "Urgent", "Follow-up", "Initial phase"]),
        })

        assigned_candidates = random.sample(candidates, min(len(candidates), random.randint(1,3)))
        months = months_between(start_date, end_date)

        for cand in assigned_candidates:  # endast de valda kandidaterna
            allocation = random.choice([10, 20, 25, 30, 40, 50])
            for m in months:
                assignments.append({
                    "contract_id": project_name,
                    "candidate_id": cand,
                    "month": m,
                    "allocation_percent": allocation
                })

    df_contracts = pd.DataFrame(contracts)
    df_assignments = pd.DataFrame(assignments)

    return df_contracts, df_assignments

# -----------------------------
# Testa funktionen
# -----------------------------



# -----------------------------
# Bonus: Pivot per kandidat / månad
# -----------------------------
# df_pivot = df_assignments.pivot_table(
#     index=["candidate_id", "contract_id"],
#     columns="month",
#     values="allocation_percent",
#     fill_value=0
# ).reset_index()

# print("\n=== PIVOT ===")
# print(df_pivot)
