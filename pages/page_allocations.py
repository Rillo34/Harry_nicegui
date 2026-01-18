from nicegui import ui
import pandas as pd
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.components.comp_cons_avail import DataTable
from niceGUI.app_state import API_client, ui_controller

@ui.page('/allocations')
async def allocations_page():
    drawer = LeftDrawer() 

    contracts = await API_client.get_all_contracts()
    allocations = await API_client.get_all_allocations()
    working_hours = await API_client.get_working_hours()
    allocations_perc = await API_client.get_all_allocations_perc()
    contract_df = pd.DataFrame(contracts)
    allocation_df = pd.DataFrame(allocations)
    workinghours_df = pd.DataFrame(working_hours)
    allocations_perc_df = pd.DataFrame(allocations_perc)
    all_columns = allocation_df.columns.to_list()
    non_month_cols = [c for c in allocation_df.columns if not c.startswith('202')]
    month_cols = [c for c in allocation_df.columns if c.startswith('202')]
    visible_columns = month_cols + ["contract_id", "candidate_id"]
    hidden_columns = [c for c in all_columns if not c in visible_columns]


    async def add_allocation(contract_id, candidate_id, allocation_percent):
        # await API_client.add_allocation(contract_id, candidate_id, allocation_percent)
        print(f"Added allocation {contract_id} - {candidate_id} - {allocation_percent}")

    async def delete_allocation(contract_id, candidate_id):
        # await API_client.delete_allocation(contract_id, candidate_id)
        print(f"Deleteded allocation {contract_id} - {candidate_id}")    
    
    async def change_alloc(contract_id, candidate_id, up_alloc):
        if up_alloc:
            print("UP")
            # await API_client.change_allocation(contract_id, candidate_id, 10)
        else:
            print("DOWN")
            # await API_client.change_allocation(contract_id, candidate_id, -10)
        print(f"Changed allocation for {contract_id} - {candidate_id}")

    callbacks = { "add_allocation": add_allocation, "delete_allocation": delete_allocation, "change_alloc": change_alloc} 

    with ui.column().classes('w-full'):
        with ui.tabs().classes('w-full') as tabs:
            contract_tab = ui.tab('Contracts')
            allocation_tab = ui.tab('Allocations (edit)')
            allocation_tab_perc = ui.tab('Allocations (edit) perc')
            arbetsdagar_tab = ui.tab('Working hours')
        with ui.tab_panels(tabs, value = allocation_tab).classes('w-full'):
            with ui.tab_panel(contract_tab):
                contract_table = DataTable(contract_df, is_summary=True, callbacks = callbacks)
                # contract_table.table.selection = 'none'
            with ui.tab_panel(allocation_tab):
                allocation_table = DataTable(allocation_df, hidden_columns=hidden_columns, is_summary=True, alloc_table = True, callbacks = callbacks)
            with ui.tab_panel(allocation_tab_perc): 
                allocation_perc_table = DataTable(allocations_perc_df, hidden_columns=hidden_columns, is_summary=True, perc_table=True, callbacks = callbacks)
            with ui.tab_panel(arbetsdagar_tab): 
                arbetsdagar_table = DataTable(workinghours_df, callbacks = callbacks)
            

