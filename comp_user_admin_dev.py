from nicegui import ui
import asyncio



class UserAdminDevComponent:

    def __init__(self, api_client):
        self.api_client = api_client
        self.ui_controller = self.api_client.controller
        self.users = []  # tom lista tills vi laddar async
        self.columns = [
            {'name': 'name', 'label': 'Name', 'field': 'name', 'sortable': True, 'align': 'left', 'headerStyle': 'background-color: lightblue;'},
            {'name': 'responsibility', 'label': 'responsibility', 'field': 'responsibility', 'sortable': False, 'align': 'left', 'headerStyle': 'background-color: lightblue;'},
            {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'sortable': False, 'align': 'center', 'headerStyle': 'background-color: lightblue;'},
        ]
        with ui.row().classes('w-full items-start gap-8'):
            with ui.card().classes('w-1/3 p-4 text-left'):
                self.name_input = ui.input(label='Name', placeholder='Enter user name').classes('w-full text-sm')
                self.responsibility_input = ui.textarea(
                    label='responsibility',
                    placeholder='Describe the role'
                ).classes('w-full text-sm').props('rows=2')
                ui.button('Add User', on_click=self.add_user).classes('mt-4')
            
            with ui.column().classes('w-1/2'):
                # 👇 Label som binder till company_id och uppdateras automatiskt
                ui.label().bind_text_from(self.ui_controller,'company_id',
                          backward=lambda i: f'Users for {i} (editable)')

                self.users_table = ui.table(columns=self.columns, rows=self.users).classes('w-full').props('wrap-cells header-class=bg-blue-200')
                self.users_table.add_slot('body-cell-actions', '''
                    <q-td :props="props">
                        <q-btn icon="edit" @click="() => $parent.$emit('notify', props.row)" flat />
                    </q-td>
                ''')
                self.users_table.on('notify', lambda e: self.edit_user(e.args))
                ui.button('Get users', on_click=self.load_users).props('icon=user_attributes')
        ui.separator().classes('my-4')


    async def load_users(self):
        users_from_backend = await self.api_client.get_users(self.ui_controller.company_id)
        # Gör om till dicts så NiceGUI kan serialisera
        self.users = [u if isinstance(u, dict) else u.model_dump() for u in users_from_backend]
        self.users_table.rows = self.users
        self.users_table.update()

    def on_company_change(self):
        # När company_id ändras, trigga ny laddning
        asyncio.create_task(self.load_users())

    async def add_user(self):
        name = self.name_input.value.strip()
        resp = self.responsibility_input.value.strip()
        if name:
            new_user = {'name': name, 'responsibility': resp if resp else 'No responsibility'}
            self.users.append(new_user)
            self.users_table.update()
            self.name_input.value = ''
            self.responsibility_input.value = ''
            await self.api_client.put_users(self.users)
            ui.notify(f'User "{name}" has been added!', color='positive')
        else:
            ui.notify('Please enter a name.', color='warning')

    def edit_user(self, row: dict):
        """Open a dialog to edit a user's responsibility."""
        print("Editing user:", row)
        with ui.dialog() as dialog, ui.card().classes('w-96 p-4'):
            ui.label(f'Edit User: {row["name"]}').classes('text-lg font-bold')
            edited_name = ui.input(label='Name', value=row['name']).props('readonly').classes('w-full')
            edited_responsibility = ui.textarea(
                label='responsibility',
                value=row['responsibility']
            ).classes('w-full').props('rows=3')

            def save_changes():
                new_resp = edited_responsibility.value.strip()
                for i, u in enumerate(self.users):
                    if u['name'] == row['name']:
                        self.users[i]['responsibility'] = new_resp
                        break

                self.users_table.rows = self.users
                self.users_table.update()
                asyncio.create_task(self.api_client.put_users(self.users))
                ui.notify(f'Changes saved for {row["name"]}', color='info')
                dialog.close()
            
            def delete_user():
                for i, u in enumerate(self.users):
                    if u['name'] == row['name']:
                        del self.users[i]                        
                        break
                self.users_table.rows = self.users
                self.users_table.update()
                asyncio.create_task(self.api_client.put_users(self.users))
                ui.notify(f'User "{row["name"]}" has been deleted.', color='negative')
                dialog.close()

            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('Save', on_click=save_changes).props('icon=save')
                ui.button('Cancel', on_click=dialog.close).props('icon=close').props('flat')
                ui.button('Delete user', on_click=delete_user).props('icon=delete').props('flat')


        dialog.open()

class CompanySummaryJobMatch:
    
    def __init__(self, api_client):

        self.api_client = api_client
        self.ui_controller = self.api_client.controller
        self.ui_controller.company_id = "structor"
        self.summary_exists = False
        companies = ['structor', 'nexer']
        ui.select(companies, 
                  label='Select company', 
                  value=self.ui_controller.company_id
                 ).bind_value(self.ui_controller, 'company_id').classes('w-64 text-lg')
        with ui.row().classes('items-center gap-2'):
                # company_id_input = ui.input('Company name', value=str(ui_controller.company_id)).classes('w-48')
            fetch_nexer_button = ui.button('Fetch Nexer Summary', on_click=lambda: self.fetch_company_summary("nexer")).classes('bg-blue-500 text-white')
            fetch_structor_button = ui.button('Fetch Structor Summary', on_click=lambda: self.fetch_company_summary("structor")).classes('bg-blue-500 text-white')
            ui.label().bind_text_from(self.ui_controller,'company_id',backward=lambda i: f'Company name: {i}  ')
            ui.label().bind_text_from(self.ui_controller,'industry',backward=lambda i: f'Industry name: {i}')
                
        with ui.row().classes('w-full items-start gap-2'):
            summary_area = ui.textarea('Company Summary').bind_value(self.ui_controller, 'company_summary').classes('flex-grow h-48 mt-4')
            ui.button('Edit summary', icon='edit_document', on_click=self.edit_summary).bind_visibility_from(self.ui_controller, 'company_summary', backward=bool)
        match_button = ui.button('Match Jobs to Company', icon='difference', on_click=lambda: self.match_jobs_to_company()).classes('bg-green-500 text-white mt-4').bind_visibility_from(self.ui_controller, 'company_summary', backward=bool)
        with ui.row().classes('w-full items-start gap-2'):
            columns = [
                {'name': 'job_id', 'label': 'Job_id', 'field': 'job_id', 'sortable': True, 'align': 'left'},
                {'name': 'job_fit', 'label': 'Job fit', 'field': 'job_fit', 'sortable': True, 'align': 'left'},
                {'name': 'customer', 'label': 'Customer', 'field': 'customer', 'sortable': True, 'align': 'left'},
                {'name': 'title', 'label': 'Title', 'field': 'title', 'sortable': True, 'align': 'left'},
                {'name': 'assessment', 'label': 'Assessment', 'field': 'assessment','sortable': True, 'align': 'left'},
                {'name': 'recruiter', 'label': 'Recruiter', 'field': 'recruiter', 'sortable': True, 'align': 'left'}
            ]
            self.job_fit_table = ui.table(rows=[], columns=columns).props('pagination.sortBy=job_fit pagination.descending=true wrap-cells')
            self.job_fit_table.classes('w-full h-64 text-left').style('text-align: left; white-space: normal; word-break: break-word;')
            
            # Lägg till din slot direkt vid deklarationen
            self.job_fit_table.add_slot('body-cell-job_fit', '''
                <q-td key="job_fit" :props="props">
                    <q-badge :color="
                        props.value === 'EXCELLENT' ? 'blue' :
                        props.value === 'GOOD' ? 'green' :
                        props.value === 'OK' ? 'orange' :
                        'red'
                    ">
                        {{ props.value }}
                    </q-badge>
                </q-td>
            ''')
    
    def edit_summary(self):
        print("Editing summary")
        with ui.dialog() as dialog, ui.card().classes('w-800 p-4'):
            ui.label(f'Edit summary for  {self.ui_controller.company_id}').classes('text-lg font-bold')
            edited_summary = ui.textarea(
                label='Company Summary',
                value=self.ui_controller.company_summary
            ).classes('w-full').props('rows=3')

            def save_changes():
                new_summary = edited_summary.value.strip()
                print("nya summary: ", new_summary)
                self.ui_controller.company_summary = new_summary
                asyncio.create_task(self.api_client.put_new_summary(new_summary))
                ui.notify(f'Changes saved for the new summary')
                dialog.close()
            
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('Save', on_click=save_changes).props('icon=save')
                ui.button('Cancel', on_click=dialog.close).props('icon=close').props('flat')

        dialog.open()

    async def fetch_company_summary(self, company_id):
        print("Fetching company summary for :", company_id)
        company_profile = await self.api_client.api_get_company_summary(company_id)
        if company_profile:
            self.ui_controller.company_summary = company_profile.summary
            self.ui_controller.company_id = company_profile.company_id
            self.ui_controller.company_industry = company_profile.industry
            ui.notify('Company summary fetched successfully')
            print("Company summary:", company_profile.summary)
        else:
            ui.notify('No summary found for the given company ID')
            print("No summary found for company_id:", company_id)

    async def match_jobs_to_company(self):
        if not self.ui_controller.company_summary:
            ui.notify('Please fetch the company summary first')
            return
        # jobs = await API_client.match_company_to_jobs(ui_controller.company_id)
        matched_results = await self.api_client.match_company_to_jobs(self.ui_controller.company_id)
        self.ui_controller.matched_results = [fit.model_dump() for fit in matched_results]
        job_fits = self.ui_controller.matched_results
        ui.notify(f"Matched {len(matched_results)} jobs to company profile")
        for result in matched_results:
            print(result)
    
        rows = [row for row in self.ui_controller.matched_results]
        self.job_fit_table.rows = rows
        self.job_fit_table.update()

# Instantiate the component
# UserAdminDevComponent()

# ui.run(port=8008)
