from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.app_state import API_client, ui_controller
from niceGUI.components.comp_cons_avail import DataTable
import pandas as pd

@ui.page('/availability')
async def availability_page():
    drawer = LeftDrawer()
    ui.label("Availability Page")
    contracts = await API_client.get_all_contracts()
    contract_df = pd.DataFrame(contracts)
    contract_list = contract_df["contract_id"].unique().tolist()
    contract_to_test = contract_list[0]
    ui.label(f"Testing availability for contract: {contract_to_test}")
    row_contract = contract_df[contract_df["contract_id"] == contract_to_test].iloc[0]
    month_cols = [c for c in contract_df.columns if c.startswith("202")]
    active_months = [c for c in month_cols if row_contract[c] > 0]
    print("active_months:", active_months)
    
    availability = await API_client.get_availability("JAC96")
    print ("availability data received:", availability)
    availability_df = pd.DataFrame(availability)
    
    
    # # availability_df = availability_df.drop(columns=["id"])
    # print("availability_df:")
    # print(availability_df.head())
    # comparison = availability_df[active_months].ge(row_contract[active_months])
    # print("comparison:")
    # print(comparison.head())
    
    # diff_df = availability_df[active_months].subtract(row_contract[active_months], axis=1)
    # diff_df["total_diff"] = diff_df.sum(axis=1)
    # diff_df.insert(0, "candidate_id", availability_df["candidate_id"].values)
    # print("diff_df:")
    # print(diff_df.head())

    # eligible_mask = comparison.all(axis=1)
    # eligible_candidates = availability_df[eligible_mask]
    # print("Eligible candidates:")
    # print(eligible_candidates.head())

    # print("availability_df with is_available:")
    # availability_df["is_available"] = comparison.all(axis=1)
    # print(availability_df.head())
    # # Visa tabellen


    availability_table = DataTable(availability_df, is_summary=True)
    # ui.label(f"Candidate Availability against contract list {contract_to_test} for {active_months}").classes("text-lg font-bold mt-4")
