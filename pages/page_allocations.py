from gc import callbacks
from dataclasses import dataclass
from typing import List, Dict, Any
from nicegui import ui
from pyparsing import Any, Dict
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.app_state import API_client, ui_controller
from niceGUI.components.comp_cons_avail import DataTable
# from niceGUI.components.comp_cons_avail import DataTable2
from niceGUI.components.comp_abscence_table import AbsenceTable
import pandas as pd
from tabulate import tabulate
import random

class AbsenceHandler:
    async def load_data(self):
        self.candidates = await API_client.get_internal_candidates()
        self.candidate_name_list = {c["candidate_id"]: c["name"] for c in self.candidates}
        self.vacations = await API_client.get_abscence()
        self.vacation_dict = {v["id"]: v for v in self.vacations}

    async def update_or_add_abscence(self, data):
        data_dict = data.model_dump()
        candidate_away = await API_client.update_or_add_abscence(data_dict)
        # self.allocation_handler.load_data(self.allocation_handler.contract_handler)  # ladda om allocation data efter ändring
        return candidate_away
    async def delete_abscence(self, abscence_id):
        await API_client.delete_abscence(abscence_id)


class ContractHandler:
    def __init__(self):
        self.contract_table = None
        self.hidden_cols = None
        
    async def load_data(self):
        contract_table, self.hidden_cols = await API_client.get_contracts_table()
        print("hiddden cols in load_data:", self.hidden_cols)
        self.contract_df = pd.DataFrame(contract_table)
        self.working_hours_df = pd.DataFrame(await API_client.get_workinghour_table())

    async def update_table(self):
        contract_table, hidden_cols = await API_client.get_contracts_table()
        self.contract_df = pd.DataFrame(contract_table)
        self.contract_table.update(self.contract_df, hidden_cols=hidden_cols)

    async def add_contract(self, contract_data):
        await API_client.add_contract(contract_data)
        await self.update_table()  # uppdatera tabellen med ny data
        await self.allocation_handler.load_data(self)  # ladda om allocation data efter ändring
        self.allocation_handler.update_tables()  # uppdatera tabellerna med ny data
        ui.notify("Contract added (this is a placeholder, implement backend logic)", type='success')
    
    async def edit_contract(self, contract_id, updated_data):
        await API_client.edit_contract(contract_id, updated_data)
        await self.update_table()  # uppdatera tabellen med ny data
        await self.allocation_handler.load_data(self)  # ladda om allocation data efter ändring
        self.allocation_handler.update_tables()  # uppdatera tabellerna med ny datav
        ui.notify("Contract updated (this is a placeholder, implement backend logic)", type='success')
    
    async def delete_contract(self, contract_id):
        print(f"Deleting contract {contract_id}")
        await API_client.delete_contract(contract_id)  # ladda om både kontrakt och allocation data efter ändring
        await self.update_table()  # uppdatera tabellen med ny data
        await self.allocation_handler.load_data(self)  # ladda om allocation data efter ändring
        self.allocation_handler.update_tables()  # uppdatera tabellerna med ny data
        ui.notify("Contract deleted (this is a placeholder, implement backend logic)", type='success')

    async def update_notes(self, row, col, new_value):
        contract_id = row["contract_id"]
        await API_client.update_notes(contract_id, candidate_id="CONTRACT", new_value=new_value)


class AllocationHandler:
    def __init__(self):
        self.perc_table = None
        self.hour_table = None
        self.hidden_cols = ["contract_id", "candidate_id", "id", "start_date", "end_date"]  # dölja dessa kolumner i allocationstabellerna
    async def load_data(self, contract_handler: ContractHandler):
        allocation_tables = await API_client.get_allocations_perc_and_hours()
        self.allocation_df_perc = pd.DataFrame(allocation_tables["allocation_perc"])
        self.allocation_df_hours = pd.DataFrame(allocation_tables["allocation_hours"]).round(0)
        self.month_list = [col for col in contract_handler.contract_df.columns if col.startswith("202")]
        total = await API_client.get_total_capacity_and_average()
        self.capacity_dict = total["capacity"]
        self.utilisation_dict = total["average"]
        self.top_rows = {
            "capacity": self.capacity_dict,
            "utilisation": self.utilisation_dict
        }
    def update_tables(self):
        self.perc_table.update(self.allocation_df_perc, top_rows=self.top_rows)
        # self.perc_table.update(self.allocation_df_perc)
        self.hour_table.update(self.allocation_df_hours)
        
    async def delete_row(self, rows):
        await API_client.delete_allocations(rows)
        # await self.contract_handler.load_data()  # ladda om data efter borttagning
        # await self.load_data(self.contract_handler)  # ladda om data efter borttagning
        # self.update_tables()  # uppdatera tabellerna med ny data
        ui.notify(f"Deleted {len(rows)} allocation(s)", type='success')
        
    async def change_alloc(self, rows, step):
        change_list = [
            {"contract_id": r["contract_id"], "candidate_id": r["candidate_id"], "change": step}
            for r in rows
        ]
        await API_client.change_allocation(change_list)
        await self.contract_handler.load_data()  # ladda om data efter borttagning
        await self.load_data(self.contract_handler)  # ladda om data efter borttagning
        self.update_tables()  # uppdatera tabellerna med ny data


    async def change_cell_alloc(self, row, col, new_value):
        await API_client.change_cell_alloc([{
            "contract_id": row["contract_id"],
            "candidate_id": row["candidate_id"],
            "month": col,
            "new_value": new_value
        }])
        # await self.contract_handler.load_data()  # ladda om data efter borttagning
        # await self.load_data(self.contract_handler)  # ladda om data efter borttagning
        # self.update_tables()  # uppdatera tabellerna med ny data

    async def add_alloc(self, selected_row, candidate_ids, percent):
        old_row = selected_row[0]
        contract_id = old_row["contract_id"]
        old_candidate_id = old_row["candidate_id"]
        await API_client.add_allocation_to_contract({
            "contract_id": contract_id,
            "old_candidate_id": old_candidate_id,
            "candidate_ids": candidate_ids,
            "allocation_percent": percent/100  # konvertera till decimal
        })
        # await self.load_data(self.contract_handler)  # ladda om data efter ändring
        # await self.contract_handler.load_data()  # ladda om data efter borttagning
        # await self.load_data(self.contract_handler)  # ladda om data efter borttagning
        # self.update_tables()  # uppdatera tabellerna med ny data

    async def get_dialog_data(self, row):
        print("get_dialog_data called with row:", row)
        name_list = self.abscence_handler.candidate_name_list
        current_candidate = row[0]['candidate_id']
        filtered = {k: v for k, v in name_list.items() if k != current_candidate}
        return filtered
        
    async def update_notes(self, row, col, new_value):
        contract_id = row["contract_id"]
        candidate_id = row["candidate_id"]
        await API_client.update_notes(contract_id, candidate_id, new_value)
        print(f"Updating notes for allocation")
        
 

@ui.page('/allocations')

async def allocations_page():
    def tab_change(e):
        print(f"Tab changed to: {e.value}")
        if e.value == "Allocations % (edit)":
            allocation_handler.update_tables()
            ui.notify("Switching to Allocations % (edit) tab")
        elif e.value == "Allocations hours":
            # self.hour_table.update(self.allocation_df_hours)
            ui.notify("Switching to Allocations hours tab")

    drawer = LeftDrawer()
    ui.label("Allocations Page")
    absence_handler = AbsenceHandler()
    contract_handler = ContractHandler()
    allocation_handler = AllocationHandler()
    allocation_handler.contract_handler = contract_handler  # ge allocation_handler tillgång till contract_handler för att kunna ladda data efter ändringar
    allocation_handler.abscence_handler = absence_handler
    contract_handler.allocation_handler = allocation_handler  # ge contract_handler tillgång till allocation_handler för att kunna ladda data efter ändringar
    absence_handler.allocation_handler = allocation_handler  # ge abscence_handler tillgång till allocation_handler för att kunna ladda data efter ändringar
    # Ladda data
    await absence_handler.load_data()
    await contract_handler.load_data()
    await allocation_handler.load_data(contract_handler)

    # Callbacks
    callbacks_alloc = {
        "delete_row": allocation_handler.delete_row,
        "change_alloc": allocation_handler.change_alloc,
        "change_cell_alloc": allocation_handler.change_cell_alloc,
        "add_alloc": allocation_handler.add_alloc,
        "get_dialog_data": allocation_handler.get_dialog_data,
        "update_notes": allocation_handler.update_notes
    }
    callbacks_abscence = {
        "update_or_add_abscence": absence_handler.update_or_add_abscence,
        "delete_abscence": absence_handler.delete_abscence,
    }

    callbacks_contract = {
        "add_contract": contract_handler.add_contract,
        "edit_contract": contract_handler.edit_contract,
        "delete_contract": contract_handler.delete_contract,
        "update_notes": contract_handler.update_notes
    }
    # UI
    with ui.column().classes('w-full'):
        with ui.tabs().classes('w-full') as tabs:
            allocation_perc_tab = ui.tab('Allocations % (edit)')
            allocation_hour_tab = ui.tab('Allocations hours')
            contract_tab = ui.tab('Contracts')
            working_days_tab = ui.tab('Working days')
            abscence_tab = ui.tab('Abscence')

        with ui.tab_panels(tabs, value=allocation_perc_tab, on_change=tab_change).classes('w-full'):

            with ui.tab_panel(allocation_perc_tab):
                allocation_handler.perc_table = DataTable(
                allocation_handler.allocation_df_perc,
                hidden_columns=allocation_handler.hidden_cols,
                is_summary=True,
                alloc_table=True,
                perc_table=True,
                top_rows=allocation_handler.top_rows,
             
                callbacks=callbacks_alloc
            )

            with ui.tab_panel(allocation_hour_tab):
                allocation_handler.hour_table = DataTable(
                    allocation_handler.allocation_df_hours,
                    hidden_columns=allocation_handler.hidden_cols,
                    is_summary=True
                )

            with ui.tab_panel(contract_tab):
                contract_handler.contract_table = DataTable(
                    contract_handler.contract_df,
                    hidden_columns=contract_handler.hidden_cols,
                    callbacks=callbacks_contract,
                    contract_table=True,
                    is_summary=True
                )

            with ui.tab_panel(working_days_tab):
                DataTable(contract_handler.working_hours_df)

            with ui.tab_panel(abscence_tab):
                ui.button()
                AbsenceTable(
                    name_list=absence_handler.candidate_name_list,
                    month_cols=allocation_handler.month_list,
                    vacation_rows=absence_handler.vacations,
                    callbacks=callbacks_abscence
                )

