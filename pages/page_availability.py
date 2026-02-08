from gc import callbacks
from nicegui import ui
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.app_state import API_client, ui_controller
from niceGUI.components.comp_cons_avail import DataTable
import pandas as pd
from tabulate import tabulate
import random

def build_contract_month_df(contract_df, contract_id):
        # Hitta raden
        row_mask = contract_df["contract_id"] == contract_id
        if not row_mask.any():
            raise ValueError(f"Kontrakt '{contract_id}' hittades inte i contract_df")

        row = contract_df.loc[row_mask].iloc[0]

        # Hitta månadskolumner (de som är YYYY-MM)
        month_cols = [
            c for c in contract_df.columns
            if len(c) == 7 and c[4] == "-" and c[:4].isdigit() and c[5:].isdigit()
        ]
        month_cols = [c for c in month_cols if row[c] != 0]
        if not month_cols:
            raise ValueError(f"Inga månadskolumner med värden hittades för kontrakt {contract_id}")

        contract_month_df = contract_df.loc[row_mask, ["contract_id"] + month_cols].copy()

        return contract_month_df, month_cols

@ui.page('/availability')
async def availability_page():
    drawer = LeftDrawer()
    ui.label("Availability Page")

    contracts = await API_client.get_contracts_table()
    jobs = await API_client.get_all_jobs()
    job_df = pd.DataFrame(jobs)
    contract_df = pd.DataFrame(contracts)
    month_cols = [col for col in contract_df.columns if col.startswith(("2025-", "2026-", "2027-"))]
    result = contract_df[["contract_id"] + month_cols]
    contract_df = result.copy()
    contract_df["total_hours"] = contract_df[month_cols].sum(axis=1)
    data = await API_client.get_allocations_perc_and_hours()
    allocations_hours_df = pd.DataFrame(data["allocation_hours"]).round(0)

    # print(tabulate(allocations_hours_df, headers="keys", tablefmt="psql"))
    
    # month_cols = [c for c in contract_df.columns if c.startswith("202")]

    # alloc_sum_df = (
    #     allocations_hours_df
    #     .groupby("contract_id")[month_cols]
    #     .sum()
    #     .reset_index()
    # )
    # alloc_sum_df["total_hours"] = alloc_sum_df[month_cols].sum(axis=1)

    contract_list = contract_df["contract_id"].tolist()
    job_list = job_df["job_id"].tolist()
    candidate_list = allocations_hours_df["candidate_id"].unique().tolist()
    
    # data2 = await API_client.get_availability2(random_contract, candidate_ids=random_candidates)
    # print ("Data for random contract and candidates:")

    # print(data2)

    


    
    async def test_availability_api():
        test_contract = random.choice(contract_list)
        test_job = random.choice(job_list)
        test_candidates = random.sample(candidate_list, 3)
        # print(f"Testing availability API with contract: {test_contract} and candidates: {test_candidates}")
        # data_test = await API_client.get_availability2(is_contract=True, contract_id =test_contract, candidate_ids=test_candidates)
        print(f"Testing availability API with contract: {test_job} and candidates: {test_candidates}")
        results = []
        for job_id in job_list:
            data_test = await API_client.get_availability_job_contract(is_contract=False, contract_id =job_id, candidate_ids=candidate_list)
            assessment_df = pd.DataFrame(data_test["assessment"]).round(0)
            assessment_df["job_id"] = job_id
            results.append(assessment_df.copy())
        big_df = pd.concat(results, ignore_index=True)
        print(big_df)
        # assessment_job_df = pd.DataFrame(data_test_job["assessment"]).round(0)
        matrix_df = big_df.pivot(
            index="candidate_id",
            columns="job_id",
            values="assessment"
        )
        print(matrix_df)

        # print("Test availability data:")
        # contract_df = pd.DataFrame(data_test["contract"]).round(0)
        # need_df = pd.DataFrame(data_test["contract_need"]).round(0)
        # availability_df = pd.DataFrame(data_test["availability"]).round(0)
        # diff_df = pd.DataFrame(data_test["diff"]).round(0)
        # month_df, cols = build_contract_month_df(contract_df, test_contract)
        
        # print("Original contract:")
        # print(contract_df)
        # print("Contract/job need (after subtracting allocations):")
        # print(need_df)
        # print("Availability")
        # print(availability_df)
        # print("diff")
        # print(diff_df)
        # print("Assessmen")
        # print(assessment_df)

    
       
        with ui.row().classes('flex flex-wrap items-center gap-2 w-full'):
            def add_colored_badges(table):
            # Hjälpfunktion för att slippa upprepa samma slot för varje kolumn
                status_colors = """
                    :color="
                        props.value === 'EXCELLENT' ? 'green' :
                        props.value === 'OK'        ? 'orange' :
                        props.value === 'BAD'       ? 'red' :
                        props.value === 'WEAK'      ? 'deep-orange' :
                        'grey'
                    "
                    :label="props.value || '-'"
                """

                for col_name in [job_list]:  # lägg till alla dina betygs-kolumner
                    with table.add_slot(f'body-cell-{col_name}'):
                        with table.cell():  # ← viktigt: INGEN parameter här
                            ui.badge().props(status_colors)

            ui.label(f"Testing availability API with contract: {test_job} and candidates: {test_candidates}")
            matrix_df = matrix_df.reset_index()  # gör candidate_id till kolumn
            columns = [{"name": c, "label": c, "field": c} for c in matrix_df.columns]
            table = ui.table(columns=columns, rows=matrix_df.to_dict("records"), row_key='candidate_id').props("v-html")
            add_colored_badges(table)
            with table.add_slot('body-cell-job1'):
                ui.html('''
                    <q-td :props="props" 
                        :class="{
                            'EXCELLENT': 'bg-green-1 text-green-10',
                            'OK':        'bg-orange-1 text-orange-10',
                            'BAD':       'bg-red-1 text-red-10',
                            'WEAK':      'bg-deep-orange-1 text-deep-orange-10'
                        }[props.value] || 'bg-grey-2'">
                        {{ props.value || '-' }}
                    </q-td>
                ''')
            print(f"Testing availability API with contract: {test_job} and candidates: {test_candidates}")


        # table.add_slot('body-cell-assessment', '''
        # <q-td :props="props" :style="props.row.assessment_style">
        # {{ props.value }}
        # </q-td>
        # ''')

# df_assessment innehåller: candidate_id, assessment



    ui.button("Get test data", on_click = test_availability_api)
   