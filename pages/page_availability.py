from gc import callbacks
from dataclasses import dataclass
from typing import List, Dict, Any
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

    data = {
        "is_contract": True,
        "contract_id": "d33",
        "candidate_ids": ["BF_20", "ZQ_10", "QB_84", "GG_38", "DD_08", "RU_29", "RZ_61", "QW_48", "EM_94"],
        # "candidate_ids": ["DS_71", "GJ_99"],
        "job_id": ""
    }
    async def run_analysis():
        results_container.clear()
        with results_container:
            ui.spinner('dots', size='lg', color='red') # Visa att något händer
        
        # Kör det tunga anropet
        response = await API_client.get_availability_job_contract(data)
        candidates = response.get("candidates", [])
        # candidates.sort(key=lambda x: x.suitability_score if hasattr(x, 'suitability_score') else 0, reverse=True)
        overall_summary = response.get("overall_summary", "No summary provided")
        # candidates = input_data.get("candidates", [])
        render_availability_grid(candidates)
        results_container.clear()
        with results_container:
            ui.label(f"OVERALL CONCLUSION:").classes('text-md font-black bold text-black-700')
            ui.label(f"{overall_summary}").classes('text-md text-black-700')

    # ui.button('Starta AI-Analys', on_click=run_analysis)
    ui.button('Starta AI-Analys', on_click=run_analysis)
    results_container = ui.column()