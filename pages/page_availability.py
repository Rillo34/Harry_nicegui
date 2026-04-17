from gc import callbacks
from dataclasses import dataclass
from typing import List, Dict, Any
from unittest import result
from nicegui import ui
from pyparsing import Any, Dict
from sqlalchemy import true
from niceGUI.components.comp_left_drawer import LeftDrawer
from niceGUI.app_state import API_client, ui_controller
import pandas as pd
from tabulate import tabulate
import random


input_data = {
    'candidates': [
        {
            'id': None,
            'candidate_id': 'DS_71',
            'candidate_name': 'Göran ',
            'assessment': 'OK',
            'problem_months': [
                '2026-01',
                '2026-02',
            ],
            'total_time': True,
            'conflicting_projects': [
                'Gångaren',
            ],
            'summary': (
                "Göran is heavily overbooked in January and February 2026. "
                "This is due to the project 'Gångaren'."
            ),
        },
        {
            'id': None,
            'candidate_id': 'GJ_99',
            'candidate_name': 'Catarina',
            'assessment': 'BAD',
            'problem_months': [
                '2026-01',
                '2026-02',
                '2026-06',
            ],
            'total_time': False,
            'conflicting_projects': [
                'Diverse Hjälp Johan och Magnus.',
                'Villa Nacka.',
                'Diverse',
            ],
            'summary': (
                "Catarina is overbooked in January, February, and June 2026. "
                "This is due to 'Diverse Hjälp Johan och Magnus', "
                "'Villa Nacka', and 'Diverse' projects."
            ),
        },
    ],
    'overall_summary': (
        "Both candidates have scheduling conflicts. "
        "It is recommended to find alternative candidates without these overbooked months."
    ),
}
def render_availability_grid(candidates):
    color_map = {
        'OK': '#2ecc71',
        'BAD': '#e74c3c',
        'WEAK': '#f39c12',
        'EXCELLENT': '#3498db',
        'WITH SHUFFLE': '#95a5a6'
    }

    # Grid-inställningar: 
    # repeat(3, min-content) = Namn, Status, Score tar bara platsen de behöver.
    # 180px = Conflicts får en fast box så de inte sprider ut sig.
    # 1fr = Analys tar resten.
    grid_style = 'repeat(3, min-content) 180px 1fr'
    
    with ui.grid(columns=grid_style).classes('w-full max-w-7xl bg-white p-4 items-center gap-x-8 gap-y-2'):
        
        # --- Header ---
        ui.label('Candidate').classes('text-xs font-black text-slate-400 uppercase pb-2')
        ui.label('Status').classes('text-xs font-black text-slate-400 uppercase pb-2 text-center')
        ui.label('Score').classes('text-xs font-black text-slate-400 uppercase pb-2 text-center')
        ui.label('Conflicts').classes('text-xs font-black text-slate-400 uppercase pb-2 text-center')
        ui.label('Analysis').classes('text-xs font-black text-slate-400 uppercase pb-2')

        ui.separator().classes('col-span-5')

        for cand in candidates:
            status = str(cand.get('assessment', 'UNKNOWN')).upper()
            bg_color = color_map.get(status, '#95a5a6')
            
            # 1. Namn - font-bold men kompakt py
            ui.label(cand.get('candidate_name')).classes('font-bold text-base py-2 min-w-[150px]')

            # 2. Status Badge - Fortfarande fet men mindre padding
            with ui.element('div').style(f'background-color: {bg_color};').classes('rounded-md px-3 py-1 min-w-[100px] text-center shadow-sm'):
                ui.label(status).classes('text-white text-[14px] font-black tracking-widest uppercase')

            # 3. Score - Kompakt men tydlig
            score = cand.get('suitability_score')
            score_text = f"{score:.0f}" if isinstance(score, (int, float)) else "N/A"
            ui.label(score_text).classes('text-center font-black text-lg text-slate-700 py-2')

            # 4. Conflicts - Flex-row som håller ihop chipsen
            with ui.row().classes('gap-1 justify-center items-center py-2'):
                problems = cand.get('problem_months', [])
                if not problems:
                    ui.icon('check_circle', color='green', size='24px')
                else:
                    for month in problems:
                        # Mindre badges för att hålla radhöjden nere
                        ui.badge(month, color='red').classes('text-[12px] font-bold px-1.5 py-0.5')

            # 5. Analysis - Tätare radhöjd (leading-tight)
            ui.label(cand.get('summary') or '-').classes('text-sm text-slate-700 leading-tight py-2 pr-4')

            # Tunn separator för att markera radslutet
            ui.separator().classes('col-span-5 opacity-20')


@ui.page('/availability')
async def availability_page():
    drawer = LeftDrawer()
    ui.label("Availability Page")

    candidates_to_test = await API_client.get_all_candidates_with_cv_and_basedata()
    job_select_list = await API_client.get_job_selector_list()
    contract_select_list = await API_client.get_contract_selector_list()
    candidate_ids = [c["candidate_id"] for c in candidates_to_test]
    print(f"Hämtade kandidater: {candidate_ids}")
    options_dict = {c['candidate_id']: c['name'] for c in candidates_to_test}

                # result = [
                # {"candidate_id": item["candidate_id"], "name": item["name"]}
#                 # for item in candidates_to_test
#                 # ]

    def on_change(e):
        selected_ids = e.value 
        selected_objs = [c for c in candidates_to_test if c["candidate_id"] in selected_ids]
        names = [c['name'] for c in selected_objs]
        if names:
            print(f"Valda namn: {', '.join(names)}")
        else:
            print("Inga kandidater valda.")

    with ui.row().classes('items-center gap-4'):
        candidate_select = ui.select(
            options=options_dict,
            label='choose candidate',
            multiple=True,
            on_change=on_change
        ).props('outlined').classes('w-64 text-lg')
        

        ui.label().bind_text_from(
            candidate_select, 
            'value', 
            backward=lambda ids: f"Valda: {', '.join(options_dict[i] for i in ids)}" if ids else "Ingen vald"
        ).classes('text-lg font-bold mt-4')

    with ui.row().classes('items-center gap-4 mt-6'):
        contract_select = ui.select(
            options={contract['contract_id']: contract['text'] for contract in contract_select_list},
            label='choose contract',
            on_change=lambda e: print(f"Vald kontrakt: {e.value}")
        ).props('outlined').classes('w-64 text-lg')
        job_select = ui.select(
            options={job['job_id']: job['text'] for job in job_select_list},
            label='choose job',
            on_change=on_change
        ).props('outlined').classes('w-64 text-lg')

    
    async def run_analysis():
        results_container.clear()
        with results_container:
        # Skapa spinnern först
            spinner = ui.spinner('dots', size='lg', color='red')
            ui.label("Analysing availability...").classes('text-lg text-slate-700 mt-2')
            if contract_select.value:
                job_to_test = contract_select.value
            else:
                job_to_test = job_select.value
            data = {
                "is_contract": True,
                "contract_id": contract_select.value,
                "candidate_ids": candidate_select.value,
                "job_id": None,
            }
            response = await API_client.get_availability_job_contract(data)
            print(f"Analysresultat: {response}")
            spinner.delete()
            results_container.clear()
            ui.label("Analys klar!").classes('text-green-600')

        candidates = response.get("candidates", [])
        overall_summary = response.get("overall_summary", "No summary provided")
        # candidates = input_data.get("candidates", [])
        results_container.clear()
        with results_container:
            ui.label(f"OVERALL CONCLUSION:").classes('text-md font-black bold text-black-700')
            ui.label(f"{overall_summary}").classes('text-lg text-black-700')
            render_availability_grid(candidates)


    # ui.button('Starta AI-Analys', on_click=run_analysis)
    ui.button('Starta AI-Analys', on_click=run_analysis)
    results_container = ui.column()