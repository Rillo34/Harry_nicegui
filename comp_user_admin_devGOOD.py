from nicegui import ui


class UserAdminDevComponent:

    def __init__(self):
        self.users = [
            {'name': 'Anna Lind', 'responsibilities': 'Project management and client communication'},
            {'name': 'Björn Kvist', 'responsibilities': 'Backend development and databases'},
            {'name': 'Cecilia Dahl', 'responsibilities': 'Frontend design and UX'},
        ]

        self.columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left'},
            {'name': 'responsibilities', 'label': 'Responsibilities', 'field': 'responsibilities', 'sortable': False, 'align': 'left'},
            {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'sortable': False, 'align': 'center'},
        ]

        with ui.card().classes('w-full max-w-lg mx-auto p-4'):
            ui.label('Add New User').classes('text-2xl font-bold')
            self.name_input = ui.input(label='Name', placeholder='Enter user name').classes('w-full')
            self.responsibilities_input = ui.textarea(label='Responsibilities', placeholder='Describe the role').classes('w-full').props('rows=2')

            ui.button('Add User', on_click=self.add_user).classes('w-full mt-4')

        ui.separator()
        ui.label('Registered Users (Editable)').classes('text-xl mt-4')

        self.users_table = ui.table(columns=self.columns, rows=self.users).classes('w-1/2').props('wrap-cells')

        self.users_table.add_slot('body-cell-actions', '''
            <q-td :props="props">
                <q-btn icon="edit" @click="() => $parent.$emit('notify', props.row)" flat />
            </q-td>
        ''')
        # self.users_table.on('notify', lambda e: ui.notify(f'Hi {e.args["name"]}!'))
        # self.users_table.on('notify', lambda e: self.edit_user(e.args))
        self.users_table.on('notify', lambda e: self.edit_user(e.args))

   

    def add_user(self):
        name = self.name_input.value.strip()
        resp = self.responsibilities_input.value.strip()
        if name:
            new_user = {'name': name, 'responsibilities': resp if resp else 'No responsibilities'}
            self.users.append(new_user)
            self.users_table.update()
            self.name_input.value = ''
            self.responsibilities_input.value = ''
            ui.notify(f'User "{name}" has been added!', color='positive')
        else:
            ui.notify('Please enter a name.', color='warning')

    def edit_user(self, row: dict):
        """Open a dialog to edit a user's responsibilities."""
        print("Editing user:", row)
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label(f'Edit User: {row["name"]}').classes('text-lg font-bold')
            edited_name = ui.input(label='Name', value=row['name']).props('readonly').classes('w-full')
            edited_responsibilities = ui.textarea(
                label='Responsibilities',
                value=row['responsibilities']
            ).classes('w-full').props('rows=3')

            def save_changes():
                new_resp = edited_responsibilities.value.strip()
                for i, u in enumerate(self.users):
                    if u['name'] == row['name']:
                        self.users[i]['responsibilities'] = new_resp
                        break

                self.users_table.rows = self.users
                self.users_table.update()
                ui.notify(f'Changes saved for {row["name"]}', color='info')
                dialog.close()
            
            def delete_user():
                for i, u in enumerate(self.users):
                    if u['name'] == row['name']:
                        del self.users[i]                        
                        break
                self.users_table.rows = self.users
                self.users_table.update()

                ui.notify(f'User "{row["name"]}" has been deleted.', color='negative')
                dialog.close()

        


            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('Save', on_click=save_changes).props('icon=save')
                ui.button('Cancel', on_click=dialog.close).props('icon=close').props('flat')
                ui.button('Delete user', on_click=delete_user).props('icon=delete').props('flat')


        dialog.open()


# Instantiate the component
UserAdminDevComponent()

ui.run(port=8008)
