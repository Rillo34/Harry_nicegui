from gc import callbacks
from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.app_state import API_client, ui_controller
from niceGUI.components.comp_cons_avail import DataTable
from niceGUI.components.comp_abscence_table import AbsenceTable
import pandas as pd
from tabulate import tabulate
import random


@ui.page('/availability')
async def availability_page():
    drawer = LeftDrawer()
    ui.label("Availability Page")
    contract_table, hidden_cols = await API_client.get_contracts_table()
    contract_df = pd.DataFrame(contract_table)
    allocation_tables = await API_client.get_allocations_perc_and_hours()
    allocation_df_perc = pd.DataFrame(allocation_tables["allocation_perc"])
    allocation_df_orig = allocation_df_perc.copy()
    allocation_df_hours = pd.DataFrame(allocation_tables["allocation_hours"]).round(0)
    working_hours_df = pd.DataFrame(await API_client.get_workinghour_table())
    candidates = await API_client.get_internal_candidates()
    candidate_name_list = {c["candidate_id"]: c["name"] for c in candidates}
    month_list = [col for col in contract_df.columns if col.startswith("202")]
    vacations = await API_client.get_abscence()
    print("candidate_name_list:", candidate_name_list)
    print("month_list:", month_list)

           
    async def delete_row (self):
        print("ska deleta rows:", self.selected_rows)
        await self.delete_allocation (self.selected_rows)
    
    async def inc_alloc(self):
        print("ska öka rows")
        await self.change_alloc(self.selected_rows, up_alloc = True)

    async def change_cell_alloc(self, row, col, new_value):
        print("ska ändra en cell")
        await self.change_cell_alloc(row, col, new_value)

    async def dec_alloc (self):
        print("ska minska row")
        await self.change_alloc(self.selected_rows, up_alloc = False)

    async def add_alloc(self):
        print("ska lägga till alloc:")
        # Här kan du implementera logiken för att lägga till en ny allocation, t.ex. öppna en dialog för att samla in nödvändig information och sedan skicka den till backend.
    
    async def update_or_add_abscence(data):  #Function takes CandidateAway object as input
        print("ska uppdatera abscence:")
        data_dict = data.model_dump()  # Convert CandidateAway object to dictionary
        await API_client.update_or_add_abscence(data_dict)
        vacations = await API_client.get_abscence()  # Refresh the abscence data after update/add
        abscence_table.update_table(vacations)  # Update the table with the new/updated data

    async def delete_abscence(abscence_id):
        print("ska ta bort abscence:", abscence_id)
        await API_client.delete_abscence(abscence_id)
        vacations = await API_client.get_abscence()  # Refresh the abscence data after update/add
        abscence_table.update_table(vacations)

    callbacks_alloc = {
        "delete_row": delete_row,
        "inc_alloc": inc_alloc,
        "dec_alloc": dec_alloc,
        "change_cell_alloc": change_cell_alloc,
        "add_alloc": add_alloc
    }
    callbacks_abscence = {
        "update_or_add_abscence": update_or_add_abscence,
        "delete_abscence": delete_abscence
    }

    with ui.column().classes('w-full'):
        with ui.tabs().classes('w-full') as tabs:
            allocation_perc_tab = ui.tab('Allocations % (edit)')
            allocation_hour_tab = ui.tab('Allocations hours')
            contract_tab = ui.tab('Contracts')
            working_days_tab = ui.tab('Working days')
            abscence_tab = ui.tab('Abscence')
        with ui.tab_panels(tabs, value=contract_tab).classes('w-full'):
            
            with ui.tab_panel(allocation_perc_tab):
                ui.label("Allocation %").classes("text-lg font-bold mb-2")
                with ui.row().classes('w-full'):
                    allocation_table = DataTable(allocation_df_perc, hidden_columns=hidden_cols, is_summary=True,alloc_table=True, perc_table=True, callbacks=callbacks_alloc)   
            with ui.tab_panel(allocation_hour_tab):
                ui.label("Allocation hours").classes("text-lg font-bold mb-2")
                with ui.row().classes('w-full'):
                    allocation_table = DataTable(allocation_df_hours, hidden_columns=hidden_cols, is_summary=True)
            with ui.tab_panel(contract_tab):
                ui.label("Contracts").classes("text-lg font-bold mb-2")
                with ui.row().classes('w-full'):
                    contract_table = DataTable(contract_df, hidden_columns=hidden_cols, is_summary=True)

            with ui.tab_panel(working_days_tab):
                ui.label("Working days").classes("text-lg font-bold mb-2")
                with ui.row().classes('w-full'):
                    arbetsdagar_table = DataTable(working_hours_df)
            with ui.tab_panel(abscence_tab):
                ui.label("Abscence").classes("text-lg font-bold mb-2")
                with ui.row().classes('w-full'):
                    abscence_table = AbsenceTable(name_list=candidate_name_list, month_cols=month_list, vacation_rows=vacations, callbacks=callbacks_abscence)
                

    # def add_alloc(self):
    #     print("ska lägga till alloc:")

    #     with ui.dialog() as dialog:
    #         with ui.card().classes("p-4"):   # <-- VIKTIG
    #             ui.label("Add new allocation")

    #             contract_list = sorted(self.df['contract_id'].unique().tolist())
    #             all_contracts = contract_list
    #             all_candidates = sorted(self.df['candidate_id'].dropna().unique().tolist())

    #             def get_candidates_for_contract(contract_id):
    #                 used = set(self.df[self.df['contract_id'] == contract_id]['candidate_id'].dropna())
    #                 print("used candidates for contract", contract_id, ":", used)
    #                 return [c for c in all_candidates if c not in used]

    #             def update_candidate_select(contract_id):
    #                 candidates = get_candidates_for_contract(contract_id)
    #                 candidate_select.options = candidates
    #                 candidate_select.value = None
    #                 candidate_select.update()

    #             contract_select = ui.select(
    #                 options=all_contracts,
    #                 label="Contract id",
    #                 value=contract_list[0] if contract_list else None,
    #                 on_change=lambda e: update_candidate_select(e.value)
    #             ).classes("w-48")

    #             candidate_select = ui.select(
    #                 options=get_candidates_for_contract(contract_select.value) if contract_select.value else [],
    #                 multiple=True,
    #                 value=None,
    #                 clearable=True,
    #                 on_change=lambda e: ui.notify(f"Selected candidates: {e.value}. Contract = {contract_select.value}"),
    #                 label="Candidates to add:"
    #             ).classes("w-72") 

    #             alloc_percent = ui.number(
    #                 "Alloc_percent",
    #                 format="%.1f",
    #                 step=0.1,
    #                 value=0.5,
    #                 min=0,
    #                 max=1
    #             ).classes("w-72")

    #             with ui.row():
    #                 ui.button("Cancel", on_click=dialog.close)
    #                 async def _on_save(e):
    #                     await self.add_allocation(  # skicka payload till funktionen
    #                         {
    #                             "contract_id": contract_select.value,
    #                             "candidate_ids": candidate_select.value,
    #                             "allocation_percent": alloc_percent.value
    #                         }
    #                     )
    #                     dialog.close()

    #                 ui.button("Save", on_click=_on_save).classes("bg-blue-500 text-white")
    #     dialog.open()
                #     with ui.row():    
                #         ui.radio(['Group by contract', 'Candidate', 'None'], value = 'None', on_change= add_groupby_radio).props('dense').classes("m-2")
                #         selected_label = ui.label("No selection yet").props('dense').classes("m-2")
                #         def get_candidates_for_contract(contract_id):
                #             allocated_candidates = allocation_df[
                #                 allocation_df['contract_id'] == contract_id
                #             ]['candidate_id'].tolist()
                #             return allocated_candidates

                #         def update_candidate_select(contract_id):
                #             candidates = get_candidates_for_contract(contract_id)
                #             candidate_select.options = all_candidates
                #             candidate_select.value = candidates  # rensa val
                #             candidate_select.update()
                #             print("allocation df:\n", allocation_df_orig)
                        
                #         def update_alloc_df_orig(e):
                #             global allocation_df_orig, allocation_df, month_cols

                #             new_candidates = e.value
                #             contract_id = contract_select.value

                #             # 1. Uppdatera rådata
                #             allocation_df_orig = update_allocations_for_contract(
                #                 allocation_df_orig,
                #                 contract_id,
                #                 new_candidates
                #             )

                #             # 2. Bygg om allocation_df (med månadskolumner)
                #             allocation_df = get_allocation_df(allocation_df_orig.to_dict(orient="records"))

                #             allocation_df = allocation_df.sort_values("contract_id")
                #             allocation_df = allocation_df[['id', 'contract_id', 'candidate_id'] + month_cols]
                #             allocation_table.update(allocation_df)

                            
                #         with ui.row().classes("ml-10 gap-4"): # flyttar åt höger + luft mellan
                #             contract_select = ui.select(
                #                 options=all_contracts,
                #                 label="Contract id",
                #                 value=all_contracts[0] if all_contracts else None,
                #                 on_change=lambda e: update_candidate_select(e.value)
                #             ).classes("w-48")  # bredd
                #             candidate_select = ui.select(
                #                 options=all_candidates,
                #                 multiple=True,
                #                 value=get_candidates_for_contract(contract_select.value) if contract_select.value else [],
                #                 # on_change=lambda e: ui.notify(f"Selected candidates: {e.value}. Contract = {contract_select.value}"),
                #                 on_change=lambda e: update_alloc_df_orig(e),
                #                 label="Candidates on contract"
                #             ).classes("w-72")  # bredare
                #     allocation_table = DataTable(allocation_df, is_summary=True)
                #     # allocation_table.add_select()
                # with ui.tab_panel(arbetsdagar_tab): 
                #     arbetsdagar_table = DataTable(working_hours_df)

    
   


    
    
       
        # with ui.row().classes('flex flex-wrap items-center gap-2 w-full'):
        #     def add_colored_badges(table):
        #     # Hjälpfunktion för att slippa upprepa samma slot för varje kolumn
        #         status_colors = """
        #             :color="
        #                 props.value === 'EXCELLENT' ? 'green' :
        #                 props.value === 'OK'        ? 'orange' :
        #                 props.value === 'BAD'       ? 'red' :
        #                 props.value === 'WEAK'      ? 'deep-orange' :
        #                 'grey'
        #             "
        #             :label="props.value || '-'"
        #         """

        #         for col_name in [job_list]:  # lägg till alla dina betygs-kolumner
        #             with table.add_slot(f'body-cell-{col_name}'):
        #                 with table.cell():  # ← viktigt: INGEN parameter här
        #                     ui.badge().props(status_colors)

        #     ui.label(f"Testing availability API with contract: {test_job} and candidates: {test_candidates}")
        #     matrix_df = matrix_df.reset_index()  # gör candidate_id till kolumn
        #     columns = [{"name": c, "label": c, "field": c} for c in matrix_df.columns]
        #     table = ui.table(columns=columns, rows=matrix_df.to_dict("records"), row_key='candidate_id').props("v-html")
        #     add_colored_badges(table)
        #     with table.add_slot('body-cell-job1'):
        #         ui.html('''
        #             <q-td :props="props" 
        #                 :class="{
        #                     'EXCELLENT': 'bg-green-1 text-green-10',
        #                     'OK':        'bg-orange-1 text-orange-10',
        #                     'BAD':       'bg-red-1 text-red-10',
        #                     'WEAK':      'bg-deep-orange-1 text-deep-orange-10'
        #                 }[props.value] || 'bg-grey-2'">
        #                 {{ props.value || '-' }}
        #             </q-td>
        #         ''')
        #     print(f"Testing availability API with contract: {test_job} and candidates: {test_candidates}")

   