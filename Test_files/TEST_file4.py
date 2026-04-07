from nicegui import ui
from typing import List, Dict

# --- UTÖKAD TESTDATA ---
input_data = {
    'candidates': [
        {'candidate_id': 'DS_71', 'candidate_name': 'Göran', 'assessment': 'OK', 'problem_months': ['2026-01', '2026-02'], 'conflicting_projects': ['Gångaren'], 'summary': "Överbokad i jan/feb.", 'combined_score': 87},
        {'candidate_id': 'GJ_99', 'candidate_name': 'Catarina', 'assessment': 'BAD', 'problem_months': ['2026-01', '2026-02', '2026-06'], 'conflicting_projects': ['Villa Nacka'], 'summary': "Flera projektkonflikter.", 'combined_score': 64},
        {'candidate_id': 'BE_22', 'candidate_name': 'Bengt', 'assessment': 'EXCELLENT', 'problem_months': [], 'conflicting_projects': [], 'summary': "Helt tillgänglig och hög kompetens.", 'combined_score': 95},
        {'candidate_id': 'LI_55', 'candidate_name': 'Linda', 'assessment': 'OK', 'problem_months': ['2026-03'], 'conflicting_projects': ['Slussen'], 'summary': "Kort konflikt i mars.", 'combined_score': 82},
        {'candidate_id': 'MA_10', 'candidate_name': 'Marcus', 'assessment': 'BAD', 'problem_months': ['2026-01', '2026-02', '2026-03', '2026-04'], 'conflicting_projects': ['T-Bana'], 'summary': "Långvarig överbokning.", 'combined_score': 45},
    ],
    'overall_summary': "Analys: Bengt är det självklara valet. Catarina och Marcus bör undvikas p.g.a. låga poäng och schemakonflikter."
}

def candidate_card(c: Dict):
    """Renderar ett snyggt kort för en kandidat."""
    color = 'green' if c['assessment'] in ['OK', 'EXCELLENT'] else 'red'
    
    with ui.card().classes('w-full mb-4 p-0 shadow-md border-l-8 overflow-hidden transition-all hover:scale-[1.01]') \
        .style(f'border-color: var(--q-{color})'):
        
        with ui.row().classes('w-full p-4 items-center gap-6 bg-white'):
            # Score Badge
            with ui.column().classes('items-center justify-center bg-slate-100 rounded-lg p-2 min-w-[70px]'):
                ui.label(str(c['combined_score'])).classes('text-2xl font-black text-slate-800')
                ui.label('SCORE').classes('text-[8px] font-bold text-slate-400')

            # Namn & Info
            with ui.column().classes('flex-grow gap-0'):
                ui.label(c['candidate_name']).classes('text-xl font-bold text-slate-900')
                ui.label(f"ID: {c['candidate_id']}").classes('text-xs text-slate-400')

            # Konflikt-indikator
            with ui.column().classes('items-center'):
                conflict_count = len(c['problem_months'])
                icon_color = 'text-green-500' if conflict_count == 0 else 'text-red-500'
                ui.icon('event_busy' if conflict_count > 0 else 'event_available', size='sm').classes(icon_color)
                ui.label(f'{conflict_count} månader').classes('text-[10px] font-bold')

            # Assessment Badge
            ui.badge(c['assessment'], color=color).classes('px-4 py-2 text-xs font-bold')

        # Expansion för detaljer
        with ui.expansion('Visa detaljer och analys', icon='insights').classes('w-full bg-slate-50 text-slate-500 border-t'):
            with ui.row().classes('w-full p-4 gap-8'):
                with ui.column().classes('flex-1'):
                    ui.label('SAMMANFATTNING').classes('text-[10px] font-bold text-slate-400 mb-1')
                    ui.label(c['summary']).classes('text-sm text-slate-700 leading-relaxed')
                
                with ui.column().classes('flex-1'):
                    ui.label('KONFLIKT-PROJEKT').classes('text-[10px] font-bold text-slate-400 mb-1')
                    if not c['conflicting_projects']:
                        ui.label('Inga kända konflikter').classes('text-xs italic text-green-600')
                    else:
                        for p in c['conflicting_projects']:
                            ui.label(f"• {p}").classes('text-xs text-slate-600')

# --- MAIN UI CLASS ---
class CandidateDashboard:
    def __init__(self, data):
        self.candidates = data['candidates']
        self.overall_summary = data['overall_summary']
        self.sort_key = 'combined_score'
        self.filter_text = ''
        self.build_ui()

    def build_ui(self):
        ui.query('body').style('background-color: #f1f5f9;')

        with ui.column().classes('w-full max-w-5xl mx-auto py-10 px-6'):
            # Header & AI Summary
            ui.label('Kandidatutvärdering').classes('text-4xl font-black text-slate-900 mb-2')
            with ui.card().classes('w-full mb-8 p-6 bg-indigo-900 text-white shadow-xl'):
                with ui.row().classes('items-center no-wrap'):
                    ui.icon('psychology', size='lg').classes('text-amber-400')
                    ui.label(self.overall_summary).classes('text-lg font-medium ml-4')

            # KONTROLLER (Sök, Sortering, Filter)
            with ui.row().classes('w-full mb-6 gap-4 items-center bg-white p-4 rounded-xl shadow-sm'):
                # Sök
                self.search_box = ui.input(placeholder='Sök namn...', on_change=self.update_list) \
                    .props('outlined dense bg-white').classes('flex-grow')
                
                # Sortering
                ui.label('Sortera:').classes('text-xs font-bold text-slate-400 uppercase ml-4')
                self.sorter = ui.select(
                    {'combined_score': 'Högst Score', 'conflicts': 'Minst konflikter'},
                    value=self.sort_key,
                    on_change=self.update_list
                ).props('dense options-dense outlined').classes('w-44')

            # Behållare för listan
            self.list_container = ui.column().classes('w-full')
            self.update_list()

    def update_list(self):
        """Hjärnan: Filtrerar, sorterar och ritar om listan."""
        query = self.search_box.value.lower()
        sort_by = self.sorter.value
        
        # 1. Filtrera
        filtered = [c for c in self.candidates if query in c['candidate_name'].lower()]
        
        # 2. Sortera
        if sort_by == 'combined_score':
            filtered.sort(key=lambda x: x['combined_score'], reverse=True)
        elif sort_by == 'conflicts':
            filtered.sort(key=lambda x: len(x['problem_months']))

        # 3. Rita om
        self.list_container.clear()
        with self.list_container:
            if not filtered:
                ui.label('Inga kandidater matchar sökningen.').classes('text-slate-400 italic mt-10 w-full text-center')
            else:
                for c in filtered:
                    candidate_card(c)

# Starta
CandidateDashboard(input_data)
ui.run(title="Candidate AI Pro", port=8006)