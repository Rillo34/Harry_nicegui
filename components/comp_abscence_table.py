from nicegui import events, ui
from backend.models import CandidateAway


class AbsenceTable:
    def __init__(self, name_list, month_cols, vacation_rows, callbacks = None):
        print("Initializing AbsenceTable with data:")
        print("name_list:", name_list)
        print("month_cols:", month_cols)
        print("vacation_rows:", vacation_rows)
        self.name_list = name_list
        self.month_cols = month_cols
        self.vacation_rows = vacation_rows
        self.callbacks = callbacks
        self.render()

    
    def render(self):
        columns = [
            {'name': 'candidate_id', 'label': 'Candidate', 'field': 'candidate_id'},
            {'name': 'candidate_name', 'label': 'Candidate Name', 'field': 'candidate_name'},
            {'name': 'start_date', 'label': 'From', 'field': 'start_date'},
            {'name': 'end_date', 'label': 'To', 'field': 'end_date'},
            {'name': 'away_percent', 'label': 'Absence (%)', 'field': 'away_percent'},
            {'name': 'notes', 'label': 'Notes', 'field': 'notes'},
        ]
        rows = []
        for r in self.vacation_rows:
            r_copy = r.copy()
            r_copy["candidate_name"] = self.name_list.get(r["candidate_id"], "")
            rows.append(r_copy)
        name_options = self.name_list
        self.table = ui.table(columns=columns, rows=rows, row_key="id").classes('w-1/2')

        self.table.add_slot('body', r'''
            <q-tr :props="props">
                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                    {{ props.row[col.name] }}
                </q-td>
                <q-td auto-width>
                    <q-btn size="sm" color="warning" round dense icon="delete"
                        @click="() => $parent.$emit('delete', props.row)"
                    />
                    <q-btn size="sm" color="primary" round dense icon="edit"
                        @click="() => $parent.$emit('edit', props.row)"
                    />
                </q-td>
            </q-tr>
        ''')
        self.table.on('delete', self.delete_row)
        self.table.on('edit', self.edit_row)
        with ui.row().classes('w-full items-center mt-4'):
            ui.button("Add abscence", on_click=self.add_row).classes("mb-4 bg-blue-500 text-white")

    async def delete_row(self, e: events.GenericEventArguments):
        row = e.args
        id = row.get("id")
        print("Deleting row with id:", id)
        await self.callbacks["delete_abscence"](id)
        ui.notify("Absence deleted", type='negative')

    def edit_row(self, e: events.GenericEventArguments):
        print("e:", e)
        row= e.args
        with ui.dialog() as dialog:
            with ui.card().classes('p-4 w-96'):
                ui.label("Edit absence").classes("text-lg font-bold mb-4")
                candidate_select = ui.select(
                    options=self.name_list,
                    value=row['candidate_id'],
                    label="Candidate",
                ).classes("w-full")

                start_month_select = ui.select(
                    options=self.month_cols,
                    label="Start month",
                    # value=row['start_date'] if row['start_date'] else None
                ).classes("w-full")

                end_month_select = ui.select(
                    options=self.month_cols,
                    label="End month",
                    # value=row['end_date'] if row['end_date'] else None
                ).classes("w-full")

                percent_input = ui.number(
                    label="Percent",
                    format="%.1f",
                    step=5,
                    value=row['away_percent'],
                    min=0,
                    max=100
                ).classes("w-full")

                notes_input = ui.input(label="Notes", value=row['notes']).classes("w-full")

                with ui.row().classes("justify-end mt-4"):
                    ui.button("Cancel", on_click=dialog.close)
                    ui.button(
                        "Save",
                        on_click=lambda: self.save_edited_row(
                            row,
                            candidate_select.value,
                            start_month_select.value,
                            end_month_select.value,
                            percent_input.value,
                            notes_input.value,
                            dialog
                        )
                    ).classes("bg-blue-500 text-white")
        dialog.open()
    
    def update_table(self, vacation_rows):
        rows = []
        self.vacation_rows = vacation_rows
        for r in self.vacation_rows:
            r_copy = r.copy()
            r_copy["candidate_name"] = self.name_list.get(r["candidate_id"], "")
            rows.append(r_copy)
        self.table.rows = rows
        self.table.update()

    async def save_edited_row(self, row, cid, start, end, percent, notes, dialog):
        for r in self.table.rows:
            if r["id"] == row["id"]:
                r.update({
                    'candidate_id': cid,
                    'candidate_name': self.name_list.get(cid, ""),
                    'start_date': start,
                    'end_date': end,
                    'away_percent': percent,
                    'notes': notes,
                })
                break

        self.table.update()
        await self.callbacks["update_or_add_abscence"](CandidateAway(
            id=row["id"],
            candidate_id=cid,
            start_date=start,
            end_date=end,
            away_percent=percent,
            notes=notes
        ))
        ui.notify("Absence updated", type='positive')
        dialog.close()


    def add_row(self):

        with ui.dialog() as dialog:
            with ui.card().classes('p-4 w-96'):

                ui.label("Add absence").classes("text-lg font-bold mb-4")

                candidate_select = ui.select(
                    options=self.name_list,
                    label="Candidate",
                ).classes("w-full")

                start_month_select = ui.select(
                    options=self.month_cols,
                    label="Start month",
                ).classes("w-full")

                end_month_select = ui.select(
                    options=self.month_cols,
                    label="End month",
                ).classes("w-full")

                percent_input = ui.number(
                    label="Percent",
                    format="%.1f",
                    step=5,
                    value=50,
                    min=0,
                    max=100
                ).classes("w-full")

                notes_input = ui.input(label="Notes").classes("w-full")

                with ui.row().classes("justify-end mt-4"):
                    ui.button("Cancel", on_click=dialog.close)
                    ui.button(
                        "Add",
                        on_click=lambda: self.save_new_row(
                            candidate_select.value,
                            start_month_select.value,
                            end_month_select.value,
                            percent_input.value,
                            notes_input.value,
                            dialog
                        )
                    ).classes("bg-blue-500 text-white")
        dialog.open()
    
    async def save_new_row(self, cid, start, end, percent, notes, dialog):
        print(cid)
        new_row = {
            'name': f'{cid}: {self.name_list.get(cid, "Unknown")}',
            'start_month': start,
            'end_month': end,
            'away_percent': percent,
            'notes': notes,
        }

        self.vacation_rows.append(new_row)
        self.table.rows = self.vacation_rows
        self.table.update()
        await self.callbacks["update_or_add_abscence"](CandidateAway(
            id=None,  # Assuming a new row doesn't have an ID yet
            candidate_id=cid,
            start_date=start,
            end_date=end,
            away_percent=percent,
            notes=notes
        ))
        ui.notify("Absence added", type='positive')
        dialog.close()


       
