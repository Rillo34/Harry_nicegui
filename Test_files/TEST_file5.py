from gc import callbacks
from griffe import Class
from matplotlib.pyplot import grid
from nicegui import ui
import plotly.express as px
from faker import Faker
from torch import classes
from backend.models import JobCandidateScore
import random
from typing import List
from nicegui import ui
import pandas as pd
import random
from typing import List

from faker import Faker
import pandas as pd
import random
from typing import List

fake = Faker() # English by default

def generate_test_data(n_candidates: int, n_jobs: int):
    # Skapa en svensk faker-instans
    fake = Faker('sv_SE')
    
    # Generera unika namn (set för att undvika dubbletter)
    candidate_id_list = [f'cand_{i+1:04d}' for i in range(n_candidates)]
    candidate_list = []
    while len(candidate_list) < n_candidates:
        name = fake.name()
        if name not in candidate_list:
            candidate_list.append(name)
            
    # Generera job_id med ledande nollor (t.ex. job_001, job_012)
    job_list = [f"job_{i+1:03d}" for i in range(n_jobs)]
    
    return candidate_list, job_list

def generate_scores_df(candidates: List[str], jobs: List[str]) -> pd.DataFrame:
    rows = []
    
    # Pre-generate Job/Project Metadata
    job_registry = {
        j_id: {
            "job_title": fake.job(),
            "customer": fake.company(),
        } for j_id in jobs
    }

    for cand in candidates:
        project_load = random.randint(0, 4)
        project_names = [fake.catch_phrase() for _ in range(project_load)]
        cand_id = f"cand_{hash(cand) % 10000:04d}"  # Enkel hash för ID
        for j_id in jobs:
            comp_score = round(random.uniform(1, 100), 0)
            base_avail = random.uniform(80, 100) if project_load == 0 else random.uniform(10, 90)
            # avail_score = max(15, round(base_avail - (project_load * 15), 0))
            avail_score = round(base_avail - project_load * 8, 0)
            avail_score = max(20, min(avail_score, 100))

            job = job_registry[j_id]
            competence_phrases_high = [
                "Exceeds all requirements and demonstrates deep, proven expertise.",
                "Meets every requirement and adds relevant specialist knowledge.",
                "Aligns well with the role and has clear experience from similar projects.",
                "Shows solid competence and is expected to deliver with minimal support.",
            ]
            competence_phrases_low = [
                "Meets several requirements and can perform with some onboarding.",
                "Has basic competence but lacks experience in key areas.",
                "Matches only a few requirements and will need significant support.",
                "Does not meet the competence level required for the project."
            ]
            availability_phrases_high = [
                "Fully available and able to start immediately.",
                "Able to start shortly with high availability.",
                "Available within a reasonable timeframe and can adapt to project needs.",
                "Has some current commitments but can prioritize this project effectively."
            ]
            availability_phrases_low = [
            
                "Available part‑time with potential to increase capacity later.",
                "Limited availability and can only contribute in a smaller scope.",
                "Only sporadically available, making planning difficult.",
                "Not available within the project’s required timeframe."
            ]

            # Contextual summaries
            comp_summary = (
                random.choice(competence_phrases_high) if comp_score > 60 else
                random.choice(competence_phrases_low)
            )

            avail_summary = (
                random.choice(availability_phrases_high) if avail_score > 60 else
                random.choice(availability_phrases_low)
            )

            rows.append({
                "candidate_name": cand,
                "candidate_id": cand_id,  # En enkel hash för ID
                "job_id": j_id,
                "job_title": job['job_title'],
                "customer": job['customer'],
                "comp_score": comp_score,
                "combined_score": round((comp_score * 0.5) + (avail_score * 0.5), 0),
                "availability_score": avail_score,
                "project_count": project_load,
                "comp_summary": comp_summary,
                "avail_summary": avail_summary,
            })

    return pd.DataFrame(rows)



def score_color(score: float) -> str:
    if score >= 90:
        return 'EXCELLENT'
    elif score >= 70:
        return 'WITH SHUFFLE'
    elif score >= 50:
        return 'OK'
    elif score >= 30:
        return 'WEAK'
    else:
        return 'BAD'
color_map = {
        'OK': '#2ecc71',
        'BAD': '#e74c3c',
        'WEAK': '#f39c12',
        'EXCELLENT': '#3498db',
        'WITH SHUFFLE': '#95a5a6'
    }

def get_sorted_candidates(df, job_id, metric="comp_score"):
    return (
        df[df.job_id == job_id]
        .sort_values(metric, ascending=False)['candidate_name']
        .tolist()
    )


# --------------------------
# --- UI Components ---
# --------------------------

class FilterControl:
    def __init__(self, on_change):
        self.on_change = on_change
        self.filters = {'min_comp': 0, 'min_avail': 0}
        self.sliders = {}
        self.container = None

    def build(self):
        # w-64 styr bredden, gap-1 gör det mer kompakt
        with ui.column().classes('w-64 p-4 bg-slate-50 rounded-xl mb-4 border gap-1 shadow-sm') as self.container:
            ui.label('Filters').classes('font-bold text-slate-700 mb-1')
            
            # Filter för Kompetens
            with ui.row().classes('w-full items-center gap-2'):
                ui.label('Comp:').classes('text-xs text-slate-500 w-10')
                self.sliders['comp'] = ui.slider(min=0, max=100)\
                    .props('dense')\
                    .classes('col')\
                    .bind_value(self.filters, 'min_comp')\
                    .on('update:model-value', self.on_change)
                # Dynamisk label som visar värdet
                ui.label().classes('text-xs font-mono w-6')\
                    .bind_text_from(self.filters, 'min_comp', backward=lambda v: f'{int(v)}')

            # Filter för Tillgänglighet
            with ui.row().classes('w-full items-center gap-2'):
                ui.label('Avail:').classes('text-xs text-slate-500 w-10')
                self.sliders['avail'] = ui.slider(min=0, max=100)\
                    .props('dense color=orange')\
                    .classes('col')\
                    .bind_value(self.filters, 'min_avail')\
                    .on('update:model-value', self.on_change)
                # Dynamisk label som visar värdet
                ui.label().classes('text-xs font-mono w-6')\
                    .bind_text_from(self.filters, 'min_avail', backward=lambda v: f'{int(v)}')

    def reset(self):
        self.filters['min_comp'] = 0
        self.filters['min_avail'] = 0
        # Uppdatera slider-komponenterna så de visuellt hoppar tillbaka
        self.sliders['comp'].value = 0
        self.sliders['avail'].value = 0
        self.on_change()                    

    def set_visible(self, value: bool):
        if self.container:
            self.container.set_visibility(value)
    
import plotly.express as px
from nicegui import ui

class ChartSection:
    def __init__(self, df, filter_ctrl, target_table):
        self.df = df
        self.filter_ctrl = filter_ctrl
        self.target_table = target_table
        self.chart = None

    def build(self): # Denna anropas i Tab 2
        
        self.chart = ui.plotly({}).classes('w-full h-[600px]')
        self.update() # Första ritningen
        self.chart.on('plotly_click', self._handle_click)

    def update(self):
        """Filtrerar data och ritar om grafen samt uppdaterar tabellen"""
        f = self.filter_ctrl.filters
        # 1. Filtrera data baserat på värdena i FilterControl
        filtered_df = self.df[
            (self.df['comp_score'] >= f['min_comp']) & 
            (self.df['availability_score'] >= f['min_avail'])
        ].copy()
        filtered_df['job_title'] = filtered_df['job_title'].fillna('').astype(str)
        filtered_df['customer'] = filtered_df['customer'].fillna('').astype(str)
        fig = px.scatter(
            filtered_df,
            x="comp_score",
            y="availability_score",
            color="combined_score",
            size="combined_score",
            hover_data=["candidate_name", "job_title", "customer"],
        )
        # 3. Styling av punkterna
        fig.update_traces(
            marker=dict(
                size=18, 
                opacity=0.7, 
                line=dict(width=1, color='white')
            ),
        )

        # 4. Lägg till dynamiska hjälplinjer som visar var filtret klipper
        fig.add_hline(
            y=f['min_avail'], 
            line_dash="dot", 
            line_color="red", 
            opacity=0.3,
            annotation_text=f"Min Avail: {f['min_avail']}%"
        )
        fig.add_vline(
            x=f['min_comp'], 
            line_dash="dot", 
            line_color="red", 
            opacity=0.3,
            annotation_text=f"Min Comp: {f['min_comp']}%",
            annotation_position="top left"
        )

        # 5. Justera layout
        fig.update_layout(
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis_title="Competence Score (%)",
            yaxis_title="Availability Score (%)",
            coloraxis_colorbar=dict(title="Match")
        )

        # 6. Skicka den nya figuren till NiceGUI-komponenten
        self.chart.figure = fig
        self.chart.update()
        
        # 7. Synka med tabellen (om den existerar)
        if self.target_table:
            self.target_table.render(filtered_df)

    def _handle_click(self, e):
        """Hanterar vad som händer när man klickar på en boll i grafen"""
        try:
            point = e.args['points'][0]
            # Hämta namnet från customdata som vi skickade med i update_traces
            cand_name = point.get('customdata', [point.get('text', 'Okänd')])[0]
            ui.notify(f'Selected: {cand_name}', color='primary', icon='person', position='top')
        except Exception as err:
            print(f"Plotly click error: {err}")


class PlotTable:
    def __init__(self, df):
        self.df = df
        self.table = None
        # self.render(df)

    def render(self, new_df=None):
        if new_df is not None:
            self.df = new_df
            
        if self.table is None:
            with ui.column().classes('w-full'):
                self.count_label = ui.label(f'Antal rader i table: {len(self.df)}').classes('text-sm text-gray-500 mb-2')
                self.table = ui.table.from_pandas(self.df)
                # Apply styles once
                for column in self.table.columns:
                    column['sortable'] = True
                    column['classes'] = 'ellipsis'
                    column['style'] = 'max-width: 150px'
                
                self.table.classes('w-full')
                self.table.props('dense flat bordered no-wrap sticky-header')
                self.table.style('max-width: 100%; height: 600px;')
        else:
            # Uppdatera rader och kolumner effektivt
            print("Updating existing table with new data")
            print(f"New DataFrame has {len(self.df)} rows and {len(self.df.columns)} columns")
            self.table.rows[:] = self.df.to_dict('records')
            self.table.update()
            self.count_label.text = f'Antal rader i table: {len(self.df)}'

class ScoreGrid:
    def __init__(self, df, flipped=False, mode='candidate'):
        self.df = df
        self.flipped = flipped
        self.mode = mode
        self.sort_job = None
        self.sort_candidate = None
        self.sort_metric = "comp_score"
        self.rendered = False
        self.comb_weight = 50
        self.selected_jobs = []
        self.selected_candidates = []
        print("Initializing ScoreGrid with DataFrame of shape:", df.shape)
        df.info()
        self.render()

    def update_comb_score(self, e):
        self.comb_weight = e.value
        ui.notify(f"Updating combined score: Comp {e.value}% - Avail {100 - e.value}%", color='primary')
        comp_part = self.orig_df['comp_score'] * (self.comb_weight / 100)
        avail_part = self.orig_df['availability_score'] * ((100 - self.comb_weight) / 100)
        self.orig_df['combined_score'] = round(comp_part + avail_part, 0)
        self.update_df()
        if self.sort_metric == 'combined_score':
            self.render()


    def update(self, flipped=None, sort_job=None, sort_candidate=None, sort_metric=None):
        if flipped is not None:
            self.flipped = flipped
        if sort_job is not None:
            if sort_job == self.sort_job:
                sort_job = None
                self.summary_label.text = ''
            self.sort_job = sort_job
            self.sort_candidate = None
        if sort_candidate is not None:
            if sort_candidate == self.sort_candidate:
                sort_candidate = None
                self.summary_label.text = ''
            self.sort_candidate = sort_candidate
            self.sort_job = None
        if sort_metric is not None:
            self.sort_metric = sort_metric
        self.render()
    
    def apply_selection(self):
        self.render()
        ui.notify(f"Applying selection: {len(self.selected_candidates.value)} candidates, {len(self.selected_jobs.value)} jobs", color='primary')
        
    def clear_selection(self):
        self.selected_candidates.value = []
        self.selected_jobs.value = []
        self.render()
        ui.notify("Cleared selection", color='primary')

    def render(self):
        if not self.rendered:
            self.container = ui.column().classes('w-full gap-4')

            with self.container:
                ui.label("ScoreGrid").classes('text-lg font-bold text-slate-700')

                with ui.row().classes('items-center gap-4 w-full'):
                    with ui.column().classes('gap-2 w-1/2'):
                        ui.label(
                            "Grid shows the best matches based on the selected metric. "
                            "Click on Flip View to change perspective."
                        ).classes('text-xs text-slate-500 w-full outline outline-1 outline-slate-200 p-2 rounded')

                    with ui.column().classes('gap-2 w-1/2'):
                        self.summary_label = ui.label('').classes(
                            'w-full text-md border-2 p-4 rounded-md border-blue-200 bg-slate-50 shadow-sm'
                        ).style('white-space: pre-line; margin-top: 10px; line-height: 1.5;')

                with ui.row().classes('items-end gap-8 mb-6'):
                    with ui.column().classes('gap-1'):
                        ui.label('Sort metric:').classes('text-[10px] font-bold text-slate-400 uppercase tracking-wider')
                        ui.radio(
                            ['comp_score', 'availability_score', 'combined_score'],
                            value=self.sort_metric,
                            on_change=lambda e: self.update(sort_metric=e.value)
                        ).props('dense').classes('text-sm')

                    ui.button(
                        'Flip View', icon='swap_horiz',
                        on_click=lambda: self.update(flipped=not self.flipped)
                    ).props('flat outline dense').classes('mb-1')

                    with ui.column().classes('gap-1'):
                        ui.label('Combined Score Weight:').classes('text-[12px] font-bold text-slate-400 uppercase tracking-wider')
                        comp_score_slider = ui.slider(
                            min=0, max=100, value=self.comb_weight, step=10,
                            on_change=self.update_comb_score
                        ).props('color=blue').classes('w-48')
                        ui.label().classes('text-xs font-mono w-full').style('white-space: pre-line').bind_text_from(
                            comp_score_slider, 'value',
                            backward=lambda v: f'{int(v)}% Comp\n{100 - int(v)}% Avail'
                        )
                    with ui.column().classes('gap-1'):
                        self.selected_candidates = ui.select(
                            options=list(self.df['candidate_name'].unique()),
                            label="Filter Candidates",
                            multiple=True
                        ).props('clearable dense outlined').classes('w-48')

                        self.selected_jobs = ui.select(
                            options=list(self.df['job_title'].unique()),
                            label="Filter Jobs",
                            multiple=True
                        ).props('clearable dense outlined').classes('w-48')
                    ui.button('Apply Selection', on_click=self.apply_selection).props('color=primary').classes('mt-2').bind_visibility_from(self.selected_candidates, 'value', backward=lambda v: bool(v) or bool(self.selected_jobs.value)) 
                    ui.button('Reset Selection', on_click=self.clear_selection).props('flat').classes('mt-2')
             
            self.grid_container = ui.column().classes('w-full overflow-auto')
            self.rendered = True

        candidates = self.selected_candidates.value if self.selected_candidates.value else list(self.df['candidate_name'].unique())[:5]
        jobs = self.selected_jobs.value if self.selected_jobs.value else list(self.df['job_title'].unique())[:5]

        # --- Sortering ---
        if self.sort_job:
            # sortera bara inom valda kandidater
            filtered = self.df[
                (self.df.job_title == self.sort_job) &
                (self.df.candidate_name.isin(candidates))
            ]
            sorted_df = filtered.sort_values(self.sort_metric, ascending=False)
            candidates = sorted_df['candidate_name'].tolist()

            customer_map = self.df.set_index('job_title')['customer'].to_dict()
            self.summary_label.text = (
                f"Best fit for {self.sort_job} - {customer_map.get(self.sort_job, 'Unknown Customer')} :\n"
                f"{', '.join(candidates[:3])} based on {self.sort_metric}"
            )

        if self.sort_candidate:
            # sortera bara inom valda jobb
            filtered = self.df[
                (self.df.candidate_name == self.sort_candidate) &
                (self.df.job_title.isin(jobs))
            ]
            sorted_jobs = filtered.sort_values(self.sort_metric, ascending=False)
            jobs = sorted_jobs['job_title'].tolist()

            job_customers = sorted_jobs['customer'].tolist()
            job_list = [f"{j} ({c})" for j, c in zip(jobs, job_customers)]
            self.summary_label.text = (
                f"Best matches for candidate {self.sort_candidate}:\n"
                f"{', '.join(job_list[:3])} based on {self.sort_metric}"
            )


        if not self.flipped:
            x_items, y_items = jobs, candidates
            x_col, y_col = 'job_title', 'candidate_name'
            focus_x, focus_y = self.sort_job, self.sort_candidate
        else:
            x_items, y_items = candidates, jobs
            x_col, y_col = 'candidate_name', 'job_title'
            focus_x, focus_y = self.sort_candidate, self.sort_job

        pivot = self.df.set_index([y_col, x_col])
        self.grid_container.clear()  # Rensa tidigare grid innan vi ritar nytt
        with self.grid_container:
            with ui.grid(columns=len(x_items) + 1).classes('gap-1 items-center'):
                ui.label('')
                # customer_map = self.df.set_index(x_col)['customer'].to_dict()
                customer_map = self.df.set_index('job_title')['customer'].to_dict()

                for x_val in x_items:
                    cls = "font-bold text-center w-24 text-xs"
                    if focus_x and x_val == focus_x:
                        cls += " ring-2 ring-blue-500 bg-white"
                    elif focus_x:
                        cls += " opacity-40"
                    customer_name = customer_map.get(x_val, "Unknown Customer")
                    if not self.flipped and x_col == 'job_title':
                        label_text = f"{x_val}\n - {customer_name}"
                    else:
                        label_text = x_val
                    with ui.label(label_text).classes(cls).on('click', lambda val=x_val: self.update(sort_job=val if x_col == 'job_title' else None, sort_candidate=val if x_col == 'candidate_name' else None)):
                        ui.tooltip('Click to sort').classes('text-sm p-2 bg-slate-800 shadow-xl')

                for y_val in y_items:
                    cls = "font-bold w-32 text-right pr-2 text-xs"
                    if focus_y and y_val == focus_y:
                        cls += " ring-2 ring-blue-500 bg-white"
                    elif focus_y:
                        cls += " opacity-40"
                    if self.flipped:
                        customer_name = customer_map.get(y_val, "Unknown Customer")
                        label_text = f"{y_val} - {customer_name}"
                    else:
                        label_text = y_val
                    ui.label(label_text).classes(cls).on('click', lambda val=y_val: self.update(sort_job=val if y_col == 'job_title' else None, sort_candidate=val if y_col == 'candidate_name' else None))

                    for x_val in x_items:
                        try:
                            row = pivot.loc[(y_val, x_val)]
                        except KeyError:
                            ui.label('-').classes('w-24 text-center opacity-20')
                            continue

                        comp_color = color_map.get(score_color(row.comp_score), 'bg-gray-200')
                        avail_color = color_map.get(score_color(row.availability_score), 'bg-gray-200')

                        cell_cls = "p-0 w-24 h-10 shadow-sm overflow-visible"
                        if (focus_x and x_val != focus_x) or (focus_y and y_val != focus_y):
                            cell_cls += " opacity-40"

                        with ui.card().classes(cell_cls):
                            with ui.element('div').classes('flex w-full h-full'):
                                cand_name = y_val if not self.flipped else x_val
                                job_name = x_val if not self.flipped else y_val

                                ui.tooltip(f"Candidate: {cand_name}\nJob: {job_name}\n\nCompetence: {row.comp_summary}\n\nAvailability: {row.avail_summary}").classes('text-xs p-3 bg-slate-800 shadow-xl').style('white-space: pre-line; max-width: 350px;')

                                with ui.element('div').style(f'background-color: {comp_color}').classes('flex-1 flex items-center justify-center'):
                                    ui.label(str(int(row.comp_score))).classes('text-white text-xs font-bold')

                                with ui.element('div').style(f'background-color: {avail_color}').classes('flex-1 flex items-center justify-center'):
                                    ui.label(str(int(row.availability_score))).classes('text-black text-xs font-bold')

                        
class MatchGrid:
    def __init__(self, df, mode='candidate'):
        self.orig_df = df
        self.df = df.copy()
        self.mode = mode
        self.container = ui.column().classes('w-full gap-2')
        self.comb_weight = 50
        self.sort_metric = 'comp_score'
        self.row_count = 10
        self.col_count = 3
        self.update_df()
        self.render()

    def update_df(self):
        clean_df = self.orig_df.drop_duplicates(subset=['candidate_name', 'job_title'])
        metric = self.sort_metric
        group_col = 'candidate_name' if self.mode == 'candidate' else 'job_title'
        top_entities_series = clean_df.groupby(group_col)[metric].max().sort_values(ascending=False)
        self.top_entities_order = top_entities_series.head(self.row_count).index.tolist()
        relevant_data = clean_df[clean_df[group_col].isin(self.top_entities_order)]
        self.df = relevant_data.copy()
            
    def update(self, mode=None, sort_metric=None):
        if mode:
            self.mode = mode
        if sort_metric:
            self.sort_metric = sort_metric
        self.update_df()
        self.render()
    
    def update_mode(self):
        self.mode = 'job' if self.mode == 'candidate' else 'candidate'
        ui.notify(f"Switched to {'Job' if self.mode == 'job' else 'Candidate'}-focused view", color='primary')
        self.update()
    
    def update_comb_score(self, e):
        self.comb_weight = e.value
        ui.notify(f"Updating combined score: Comp {e.value}% - Avail {100 - e.value}%", color='primary')
        comp_part = self.orig_df['comp_score'] * (self.comb_weight / 100)
        avail_part = self.orig_df['availability_score'] * ((100 - self.comb_weight) / 100)
        self.orig_df['combined_score'] = round(comp_part + avail_part, 0)
        self.update_df()
        if self.sort_metric == 'combined_score':
            self.render()
    
    def update_grid_size(self, rows=None, cols=None):
        if rows:
            self.row_count = rows
        if cols:            
            self.col_count = cols
        ui.notify(f"Updating grid size: {rows} rows x {cols} columns", color='primary')
        self.update_df()
        self.render()

    def render(self):
        self.container.clear()
        
        with self.container:
            # --- Kontroller (Header) ---
            with ui.column().classes('gap-2'):
                title = "Candidate-Centric Match Grid" if self.mode == 'candidate' else "Job-Centric Match Grid"
                ui.label(title).classes('text-lg font-bold text-slate-700')
                ui.label("Automatic sorting in grid. Click on Flip View to change perspective job/candidate.").classes('text-sm text-slate-500 w-full outline outline-1 outline-slate-200 p-2 rounded')
                with ui.row().classes('items-end gap-8 mb-6'):
                
                    with ui.column().classes('gap-1'):

                        ui.label('Sort metric:').classes('text-[10px] font-bold text-slate-400 uppercase tracking-wider')
                        ui.radio(['comp_score', 'availability_score', 'combined_score'], 
                                value=self.sort_metric, 
                                on_change=lambda e: self.update(sort_metric=e.value)
                                ).props('dense').classes('text-sm')
                    
                    ui.button('Flip View', icon='swap_horiz', on_click=self.update_mode) \
                        .props('flat outline dense').classes('mb-1')
                    
                    with ui.column().classes('gap-1'):
                        ui.label('Combined Score Weight:').classes('text-[12px] font-bold text-slate-400 uppercase tracking-wider')
                        comp_score_slider = ui.slider(
                            min=0, max=100, value=self.comb_weight, step=10, 
                            on_change=self.update_comb_score
                        ).props('color=blue').classes('w-48')
                        ui.label().classes('text-xs font-mono w-full').style('white-space: pre-line').bind_text_from(
                            comp_score_slider, 'value', 
                            backward=lambda v: f'{int(v)}% Comp\n{100 - int(v)}% Avail'
                        )
                    
                    with ui.column().classes('gap-1'):
                        option_list = list(range(1, 11))
                        ui.label('Rows:').classes('text-[10px] font-bold text-slate-400 uppercase')
                        ui.select(options=option_list, value=self.row_count,
                                on_change=lambda e: self.update_grid_size(rows=int(e.value))
                                ).props('dense outlined').classes('w-20')
                    
                    with ui.column().classes('gap-1'):
                        ui.label('Columns (Rank):').classes('text-[10px] font-bold text-slate-400 uppercase')
                        ui.select([1, 2, 3, 4, 5], value=self.col_count,
                                on_change=lambda e: self.update_grid_size(cols=int(e.value))
                                ).props('dense outlined').classes('w-20')

            # --- Dynamisk Grid ---
            total_cols = self.col_count + 1
            grid_style = f'grid-template-columns: 160px repeat({self.col_count}, 140px)'
            
            with ui.grid(columns=total_cols).style(grid_style).classes('gap-x-2 gap-y-3 items-center max-w-fit'):
                # 1. Rubrikrad
                ui.label(self.mode.capitalize()).classes('font-bold text-slate-400 text-[10px] uppercase pb-2')
                for i in range(self.col_count):
                    ui.label(f'Rank {i+1}').classes('font-bold text-center text-slate-400 text-[10px] uppercase pb-2')

                group_col = 'candidate_name' if self.mode == 'candidate' else 'job_title'
                match_col = 'job_title' if self.mode == 'candidate' else 'candidate_name'
                
                # 2. Datarader
                for entity in self.top_entities_order:
                    # Hämta matchningar för just denna person/jobb
                    subset = self.df[self.df[group_col] == entity].copy()
                    
                    # Kolumn 1: Namn/Jobb
                    display_name = entity   
                    if self.mode == 'job' and 'customer' in subset.columns:
                        customer = subset['customer'].iloc[0]
                        display_name = f"{entity}\n - {customer}"
                    
                    with ui.label(display_name).style('white-space: pre-line').classes('font-bold text-slate-700 text-xs truncate pr-4 border-r border-slate-100 h-full flex items-center'):
                        if self.mode == 'job' and 'customer' in subset.columns:
                            ui.tooltip(f"Job: {entity} - {customer}").classes('text-xs p-2 bg-slate-800 shadow-xl')
                    
                    # Kolumn 2 till N: Matchnings-kort
                    top_matches = subset.sort_values(self.sort_metric, ascending=False).head(self.col_count)
                    
                    for i in range(self.col_count):
                        if i < len(top_matches):
                            row = top_matches.iloc[i]
                            self._build_match_card(row, match_col)
                        else:
                            # Tom placeholder om det saknas matchningar för denna rank
                            ui.element('div').classes('w-32 h-14 rounded border border-dashed border-slate-200 bg-slate-50/50')

    def _build_match_card(self, row, match_col):
        c_color = color_map.get(score_color(row.comp_score), '#e5e7eb')
        a_color = color_map.get(score_color(row.availability_score), '#e5e7eb')
        
        with ui.card().classes('p-0 w-32 h-14 shadow-sm overflow-hidden border border-slate-200 group hover:border-blue-300 transition-colors'):
            with ui.column().classes('gap-0 w-full h-full'):
                with ui.element('div').classes('w-full bg-slate-50 px-2 py-1 border-b'):
                    text = row[match_col]
                    ui.label(text).classes('text-[10px] font-bold truncate text-slate-500')
                
                with ui.row().classes('w-full h-full flex-1 gap-0'):
                    with ui.element('div').style(f'background-color: {c_color}') \
                        .classes('flex-1 h-full flex items-center justify-center'):
                        ui.label(str(int(row.comp_score))).classes('text-white text-sm font-bold shadow-sm')
                    
                    with ui.element('div').style(f'background-color: {a_color}') \
                        .classes('flex-1 h-full flex items-center justify-center'):
                        ui.label(str(int(row.availability_score))).classes('text-slate-900 text-sm font-bold shadow-sm')

            ui.tooltip(f"Job: {row['job_title']} - {row['customer']}\nComp: {row.comp_summary}\nAvail: {row.avail_summary}") \
                .classes('text-xs p-2 bg-slate-800 shadow-xl') \
                .style('white-space: pre-line; max-width: 250px;')

    


def create_heatmap(df):
    # 1. Skapa matrisen (Jobb på X, Kandidater på Y)
    # Vi använder 'first' ifall det finns dubbletter
    heatmap_data = df.pivot_table(
        index='candidate_name', 
        columns='job_title', 
        values='combined_score', 
        aggfunc='first'
    )

    # 2. Rita Heatmap
    # fig = px.imshow(
    #     heatmap_data,
    #     labels=dict(x="Job Title", y="Candidate", color="Match Score"),
    #     x=heatmap_data.columns,
    #     y=heatmap_data.index,
    #     # hover_data={'combined_score': heatmap_data.values},
    #     hover_data=["candidate_name", "job_title", "customer"],
    #     color_continuous_scale='RdYlBu', # Rött (dåligt) till Blått (bra)
    #     aspect="auto" # Gör att den fyller ut containern snyggt
    # )
    fig = px.density_heatmap(
        df,
        x="job_title",
        y="candidate_name",
        z="combined_score",
        histfunc="avg",
        color_continuous_scale='RdYlBu',
        hover_data=["customer"]
    )
    fig.update_layout(
        title="Overall Match Matrix",
        xaxis_nticks=36, # Visar inte för många etiketter om det är trångt
        yaxis_nticks=36
    )
    return fig

candidates, jobs = generate_test_data(100, 100)
full_df = generate_scores_df(candidates, jobs)
all_candidates = full_df['candidate_name'].unique()
all_jobs = full_df['job_title'].unique()

sampled_candidates = random.sample(list(all_candidates), 10)
sampled_jobs = random.sample(list(all_jobs), 10)

sampled_candidates_df = full_df[
    full_df['candidate_name'].isin(sampled_candidates) & 
    full_df['job_title'].isin(sampled_jobs)
].copy()

plot_df = full_df.sample(n=100).copy()
sampled_candidates_df = sampled_candidates_df.drop_duplicates(subset=['candidate_name', 'job_title'], keep='first')    
plot_df.drop_duplicates(subset=['candidate_name', 'job_title'], keep='first', inplace=True)
plot_df.reset_index(drop=True, inplace=True)
plot_df['comp_score'] = plot_df['comp_score'].astype(float)
plot_df['availability_score'] = plot_df['availability_score'].astype(float)
# match_df = plot_df.copy()
match_df = full_df.copy()
counts = match_df.groupby('candidate_name').size()
print(counts[counts < 3].head(20))

@ui.page("/")
def index():
    chart = None
    plot_table = PlotTable(plot_df)  # Skapa tabellen en gång, den kommer att uppdateras av ChartSection
    detailed_table = PlotTable(plot_df)  # En extra tabell för att visa detaljerad data i Tab 3
    with ui.column().classes('w-full'):

        with ui.tabs() as tabs:
            t0 = ui.tab('Match Grid')
            t1 = ui.tab('Grid View')
            t2 = ui.tab('Plot View')
            t3 = ui.tab('Table View')
            t4 = ui.tab('Heatmap View')
            
        with ui.tab_panels(tabs, value=t1).classes('w-full'):

            with ui.tab_panel(t0):
                MatchGrid(match_df, mode='candidate')  # Visa kandidat-fokuserad grid först
            
            with ui.tab_panel(t1):
                # filter_test = FilterControl(on_change=lambda: grid.update() if grid else None)  # Skapa filterkontrollerna
                # filter_test.build()
                # filter_test.set_visible(False)
                ScoreGrid(sampled_candidates_df)
            with ui.tab_panel(t2):
                    title = "Plot with connected table" 
                    ui.label(title).classes('text-lg font-bold text-slate-700')
                    with ui.row().classes('w-full items-center gap-4 mb-4'):
                        ui.label("Use the filters to adjust the plot:").classes('text-sm text-slate-500')
                        filter_section = FilterControl(on_change=lambda: chart.update() if chart else None)
                        filter_section.build()
                    chart = ChartSection(plot_df, filter_section, plot_table)
                    chart.build()  # Bygg och rendera grafen i tabben där den ska användas
            
            with ui.tab_panel(t3):
                with ui.column().classes('w-full p-6 bg-slate-50 rounded-xl mt-4 border border-slate-200'):
                    def on_filter_change():
                        if detailed_table:
                            f = filter.filters
                            filtered_df = plot_df[
                                (plot_df['comp_score'] >= f['min_comp']) & 
                                (plot_df['availability_score'] >= f['min_avail'])
                            ]
                            detailed_table.render(filtered_df)
                    filter = FilterControl(on_change=on_filter_change)
                    filter.build()
                    detailed_table.render(plot_df)  # Rendera tabellen med den initiala datan
                    # filter_section.set_visible(True)  # Visa filterkontrollerna i denna tab
                    # plot_table.render(plot_df)  # Rendera tabellen med den initiala datan

            
            with ui.tab_panel(t4):
                title = "Heatmap of Competence vs Availability for Sampled Candidates and Jobs" 
                ui.label(title).classes('text-lg font-bold text-slate-700')                
                def update_comb_score():
                    heatmap_container.clear()
                    filtered_df = sampled_candidates_df.copy()
                    filtered_df['combined_score'] = round(
                        sampled_candidates_df['comp_score'] * comb_weight_slider.value / 100) + sampled_candidates_df['availability_score'] * ((100 - comb_weight_slider.value  ) / 100)  
                    with heatmap_container:
                        heatmap_fig = create_heatmap(filtered_df)
                        ui.plotly(heatmap_fig).classes('w-full h-[700px] bg-white rounded-lg shadow-sm border border-slate-100')
                comb_weight_slider = ui.slider(
                    min=0, max=100, value=50, step=10, 
                    on_change=update_comb_score
                ).props('color=blue').classes('w-48')
                ui.label().classes('text-xs font-mono w-full').style('white-space: pre-line').bind_text_from(
                    comb_weight_slider, 'value', 
                    backward=lambda v: f'{int(v)}% Comp\n{100 - int(v)}% Avail'
                )
                heatmap_fig = create_heatmap(sampled_candidates_df)  # Använd den data som är i tabellen (kan vara filtrerad)
                with ui.column().classes('w-full h-[700px] bg-white rounded-lg shadow-sm border border-slate-100') as heatmap_container:
                    ui.plotly(heatmap_fig).classes('w-full h-full')
                    # heatmap_container.style('overflow: auto')  # Lägg till scroll om det

# Se till att ui.run ligger längst ner utanför alla funktioner
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8007, title="Recruiter AI Dashboard")
    


