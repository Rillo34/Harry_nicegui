import nicegui
import json
import requests
import httpx
import pandas as pd
import asyncio
from nicegui import events, ui
# from models import RequirementPayload, EvaluateResponse, ReSize, ReSizeResponse, ReEvaluateRequest, ReEvaluateResponse, CandidatesJobResponse
# from models import J
from pydantic import parse_obj_as
from comp_cons_avail_dev6 import ContractAllocationTable, ContractHoursTable, AbsenceTable

import os
import sys
from faker import Faker
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))


async def get_contract_alloc():
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'http://127.0.0.1:8080/get-allocations'
            )

        if response.status_code == 200:
            print(response)
            print("det lyckades")
            return response.json()
        else:
            # ui.notify(f'Fel från backend: {response.status_code}', type='warning')
            return None

    except Exception as e:
        # ui.notify(f'Nätverksfel: {e}', type='warning')
        return None

async def get_contracts():
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'http://127.0.0.1:8080/get-contracts'
            )

        if response.status_code == 200:
            print(response)
            print("det lyckades")
            return response.json()
        else:
            # ui.notify(f'Fel från backend: {response.status_code}', type='warning')
            return None

    except Exception as e:
        # ui.notify(f'Nätverksfel: {e}', type='warning')
        return None

async def get_abscence():
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'http://127.0.0.1:8080/get-abscence'
            )

        if response.status_code == 200:
            print(response)
            print("det lyckades")
            return response.json()
        else:
            # ui.notify(f'Fel från backend: {response.status_code}', type='warning')
            return None

    except Exception as e:
        # ui.notify(f'Nätverksfel: {e}', type='warning')
        return None

data = asyncio.run(get_contract_alloc())
df = pd.DataFrame(data)
df_contract_alloc=df.fillna("")
print("---CONTRACT ALLOC ---\n")
print(df_contract_alloc)

data2 = data = asyncio.run(get_contracts())
df2 = pd.DataFrame(data2)
df_contract_hours=df2.fillna("")
print("---CONTRACT HOURS ---\n")
print(df_contract_hours)

# data3 = asyncio.run(get_abscence())
# df3 = pd.DataFrame(data3)
# df_abscence=df3.fillna("")
# print("---ABSCENCE---\n")
# print(df_abscence)

# df_contract_alloc =df_contract_alloc.drop(columns = ["allocation_percent"])
# df_contract_subset = df_contract_hours[['contract_id', 'description', 'hours']].rename(columns={'hours':'contract_hours'})
# df_merged_contract_alloc = df_contract_alloc.merge(df_contract_subset, on='contract_id', how='left')

# first_cols = ['id','contract_id','description', 'contract_hours', 'candidate_id', 'hours']
# other_cols = [c for c in df_merged_contract_alloc.columns if c not in first_cols]
# df_merged_contract_alloc = df_merged_contract_alloc[first_cols + other_cols]
    
# print("---df_merged contract---\n")
# print(df_merged_contract_alloc)


with ui.tabs() as tabs:
    tab_alloc = ui.tab('alloc', label='Allocation')
    tab_hours = ui.tab('contracts', label='Contracts')
    tab_abs = ui.tab('absence', label='Absence')

with ui.tab_panels(tabs, value='alloc').classes('w-full'):
    with ui.tab_panel('alloc'):
        alloc_table = ContractAllocationTable(df_contract_alloc)
    with ui.tab_panel('contracts'):
        contract_table = ContractHoursTable(df_contract_hours)
    # with ui.tab_panel('absence'):
    #     AbsenceTable(df_abscence)
alloc_table.contract_table = contract_table

ui.run(port=8007)