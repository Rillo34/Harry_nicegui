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
    allocations_perc_df = pd.DataFrame(allocations_perc)
    print (f"allocations_perc_df.head(): {allocations_perc_df.head()}")
    workinghours_df = pd.DataFrame(working_hours)
    all_columns = allocation_df.columns.to_list()
    non_month_cols = [c for c in allocation_df.columns if not c.startswith('202')]
    month_cols = [c for c in allocation_df.columns if c.startswith('202')]
    visible_columns = month_cols + ["contract_id", "candidate_id"]
    hidden_columns = [c for c in all_columns if not c in visible_columns]

    async def refresh_allocation_tables():
        allocations = await API_client.get_all_allocations()
        allocations_perc = await API_client.get_all_allocations_perc()
        allocation_df = pd.DataFrame(allocations).round(1)
        allocations_perc_df = pd.DataFrame(allocations_perc).round(1)
        allocation_table.update(allocation_df)
        allocation_perc_table.update(allocations_perc_df)


    async def add_allocation(payload):
        candidates = await API_client.get_all_candidates()
        print(f"candidates: {candidates}")


    async def delete_allocation(selected_rows):
        payload = [ 
            {"contract_id": row["contract_id"], 
             "candidate_id": row["candidate_id"], 
             "change": None, } 
             for row in selected_rows 
            ]
        await API_client.delete_allocation(payload)
        await refresh_allocation_tables()

    async def change_cell_alloc(row, col, new_value):
        payload = [ 
            {"contract_id": row["contract_id"], 
             "candidate_id": row["candidate_id"], 
             "month": col, 
             "new_value": new_value } 
                ]
        await API_client.change_cell_alloc(payload)
        await refresh_allocation_tables()

    async def change_alloc(selected_rows, up_alloc):
        selected_before = allocation_perc_table.table.selected.copy()
        if up_alloc:
            print("UP")
            change = 0.1
        else:
            print("DOWN")
            change = -0.1
        payload = [ 
            {"contract_id": row["contract_id"], 
             "candidate_id": row["candidate_id"], 
             "change": change, } 
             for row in selected_rows 
            ]
        await API_client.change_allocation(payload)
        await refresh_allocation_tables()
        allocation_perc_table.table.selected = selected_before
        allocation_perc_table.table.update()


    callbacks = { "add_allocation": add_allocation, "delete_allocation": delete_allocation, "change_alloc": change_alloc, "change_cell_alloc": change_cell_alloc } 

    with ui.column().classes('w-full'):
        with ui.tabs().classes('w-full') as tabs:
            allocation_tab_perc = ui.tab('Allocations (edit) perc')
            allocation_tab = ui.tab('Allocations (edit)')
            contract_tab = ui.tab('Contracts')
            arbetsdagar_tab = ui.tab('Working hours')
        with ui.tab_panels(tabs, value = allocation_tab_perc).classes('w-full'):
            
            with ui.tab_panel(allocation_tab_perc): 
                allocation_perc_table = DataTable(allocations_perc_df, hidden_columns=hidden_columns, is_summary=True, alloc_table = True, perc_table=True, callbacks = callbacks)
            with ui.tab_panel(allocation_tab):
                allocation_table = DataTable(allocation_df, hidden_columns=hidden_columns, is_summary=True, alloc_table = True, callbacks = callbacks)
            with ui.tab_panel(contract_tab):
                contract_table = DataTable(contract_df, is_summary=True, callbacks = callbacks)
                # contract_table.table.selection = 'none'
            with ui.tab_panel(arbetsdagar_tab): 
                arbetsdagar_table = DataTable(workinghours_df, callbacks = callbacks)
            

