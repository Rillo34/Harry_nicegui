from nicegui import ui
import pandas as pd
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.components.comp_cons_avail import DataTable
from niceGUI.app_state import API_client, ui_controller

@ui.page('/allocations')
async def allocations_page():

    def build_hours_lookup(wh_df):
        lookup = {}
        for _, row in wh_df.iterrows():
            year = str(row["year"])
            for month in [f"{i:02d}" for i in range(1, 13)]:
                if month in row:
                    lookup[f"{year}-{month}"] = row[month]
        return lookup


    drawer = LeftDrawer() 

    contracts = await API_client.get_contracts_table()
    contract_df = pd.DataFrame(contracts)

    working_hours = await API_client.get_working_hours()
    workinghours_df = pd.DataFrame(working_hours)

    data = await API_client.get_allocations_perc_and_hours()
    print(data)
    allocations_perc_df = pd.DataFrame(data["allocation_perc"]).round(1)
    allocations_hours_df = pd.DataFrame(data["allocation_hours"]).round(0)


    # hours_lookup = build_hours_lookup(workinghours_df)
    # allocation_hours_df = allocations_perc_df.copy()
    
    non_month_cols = [c for c in contract_df.columns if not c.startswith('202')]
    month_cols = [c for c in contract_df.columns if c.startswith('202')]
    # for col in month_cols:
    #     allocation_hours_df[col] = (allocations_perc_df[col].astype(float) * hours_lookup[col]).round(0)

    print (f"workinghours_df.info():")
    workinghours_df.info()
    print("allocation_perc_df:")
    allocations_perc_df.info()
    all_columns = contract_df.columns.to_list()
    
    visible_columns = month_cols + ["contract_id", "candidate_id"]
    hidden_columns = [c for c in all_columns if not c in visible_columns]

    async def refresh_allocation_tables():
        data = await API_client.get_allocations_perc_and_hours()
        allocations_perc_df = pd.DataFrame(data["allocation_perc"]).round(1)
        allocations_hours_df = pd.DataFrame(data["allocation_hours"]).round(0)
        allocations_hour_table.update(allocations_hours_df)
        allocations_perc_table.update(allocations_perc_df)


    async def add_allocation(new_allocations):
        await API_client.add_allocation_to_contract(new_allocations)
        print(f"allocations: {new_allocations}")
        await refresh_allocation_tables()

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
        selected_before = allocations_perc_table.table.selected.copy()
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
        allocations_perc_table.table.selected = selected_before
        allocations_perc_table.table.update()


    callbacks = { "add_allocation": add_allocation, "delete_allocation": delete_allocation, "change_alloc": change_alloc, "change_cell_alloc": change_cell_alloc } 

    with ui.column().classes('w-full'):
        with ui.tabs().classes('w-full') as tabs:
            allocation_tab_perc = ui.tab('Allocations (edit) perc')
            allocation_tab_hour = ui.tab('Allocations (hour)')
            contract_tab = ui.tab('Contracts')
            arbetsdagar_tab = ui.tab('Working hours')
        with ui.tab_panels(tabs, value = allocation_tab_perc).classes('w-full'):
            
            with ui.tab_panel(allocation_tab_perc): 
                allocations_perc_table = DataTable(allocations_perc_df, hidden_columns=hidden_columns, is_summary=True, alloc_table = True, perc_table=True, callbacks = callbacks)
            with ui.tab_panel(allocation_tab_hour):
                allocations_hour_table = DataTable(allocations_hours_df, hidden_columns=hidden_columns, is_summary=True, alloc_table = True, callbacks = callbacks)
            with ui.tab_panel(contract_tab):
                contract_table = DataTable(contract_df, is_summary=True, callbacks = callbacks)
                # contract_table.table.selection = 'none'
            with ui.tab_panel(arbetsdagar_tab): 
                arbetsdagar_table = DataTable(workinghours_df, callbacks = callbacks)
            

