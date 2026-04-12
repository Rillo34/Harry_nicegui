from gc import callbacks
from griffe import Class
from matplotlib.pyplot import grid
from nicegui import ui
import plotly.express as px
from faker import Faker
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
        
        for j_id in jobs:
            comp_score = round(random.uniform(1, 100), 0)
            
            # Availability logic based on project load
            # Base score decreases by ~20% for every active project
            base_avail = random.uniform(80, 100) if project_load == 0 else random.uniform(10, 90)
            avail_score = max(0, round(base_avail - (project_load * 15), 0))

            job = job_registry[j_id]
            
            # Contextual summaries
            comp_summary = (
                f"Matches technical stack for {job['job_title']}."
                if comp_score > 60 else
                f"Gap identified in required niche skills for {job['customer']}."
            )

            if project_load == 0:
                avail_summary = "Fully available. No current project assignments."
            else:
                avail_summary = f"Capacity limited by {project_load} active projects: {', '.join(project_names)}."

            rows.append({
                "candidate_name": cand,
                "candidate_id": random.randint(1000, 9999),
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

    def build(self): # Denna anropas där den ska synas
        with ui.column().classes('w-full p-6 bg-slate-50 rounded-xl mb-4 border'):
            ui.label('Filters').classes('font-bold')
            self.sliders['comp'] = ui.slider(min=0, max=100).bind_value(self.filters, 'min_comp').on('update:model-value', self.on_change)
            self.sliders['avail'] = ui.slider(min=0, max=100).bind_value(self.filters, 'min_avail').on('update:model-value', self.on_change)

    def reset(self):
        self.filters['min_comp'] = 0
        self.filters['min_avail'] = 0
        # Uppdatera slider-komponenterna så de visuellt hoppar tillbaka
        self.sliders['comp'].value = 0
        self.sliders['avail'].value = 0
        self.on_change()

class FilterControl2:
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

        # 2. Skapa figuren med Plotly Express
        fig = px.scatter(
            filtered_df, 
            x="comp_score", 
            y="availability_score", 
            color="combined_score",
            range_x=[-5, 105], 
            range_y=[-5, 105],
            size='combined_score',
            hover_data=['candidate_name', 'job_title', 'customer'],
            hover_name='candidate_name',
            template='plotly_white',
            color_continuous_scale='RdYlBu' # Röd-Gul-Blå skala
        )

        # 3. Styling av punkterna
        fig.update_traces(
            marker=dict(
                size=18, 
                opacity=0.7, 
                line=dict(width=1, color='white')
            ),
            # Skicka med namnet i customdata så klick-eventet kan läsa det enkelt
            customdata=filtered_df[['candidate_name']].values 
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
            print("Creating table for the first time")
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
    def __init__(self, df, flipped=False):
        print("Initializing ScoreGrid with DataFrame")
        self.df = df
        self.flipped = flipped
        self.sort_job = None
        self.sort_candidate = None
        self.sort_metric = "comp_score"
        self.rendered = False
        self.render()

    def update(self, flipped=None, sort_job=None, sort_candidate=None, sort_metric=None):
        print("Updating ScoreGrid")
        if flipped is not None:
            self.flipped = flipped
        if sort_job is not None:
            if sort_job == self.sort_job:
                sort_job = None  # Toggle off if same job clicked again
                self.summary_label.text = ''  # Clear summary when toggling off
            self.sort_job = sort_job
            self.sort_candidate = None  # Reset other sort
        if sort_candidate is not None:
            if sort_candidate == self.sort_candidate:
                sort_candidate = None  # Toggle off if same candidate clicked again
                self.summary_label.text = ''  # Clear summary when toggling off 
            self.sort_candidate = sort_candidate
            self.sort_job = None  # Reset other sort
        if sort_metric is not None:
            self.sort_metric = sort_metric
        
        self.render()

    def render(self):
        # 1. Använd self.container istället för att skapa ny
        if not self.rendered:
            with ui.row().classes('m-4 gap-4'):
                ui.button('Flip View', icon='swap_horiz', on_click=lambda: self.update(flipped=not self.flipped))
                # ui.button('Reset', icon='refresh', on_click=lambda: self.update())
                # select = ui.select(['comp_score', 'availability_score'], label='Sort Metric', 
                                # value=self.sort_metric, on_change=lambda e: self.update(sort_metric=e.value)).classes('w-48')
                with ui.column().classes('gap-1'):
                    ui.label('Sort metric:').classes('text-sm text-gray-600')
                    ui.radio(['comp_score', 'availability_score'], value=self.sort_metric, on_change=lambda e: self.update(sort_metric=e.value)).classes('w-48')
                ui.label('Click on headers to sort.\nClick again to toggle.').style('white-space: pre-line')                
                # ui.label('Click again to toggle off sorting.').classes('text-sm text-gray-600')
                self.summary_label = ui.label('') \
                    .classes('text-md border-2 p-4 rounded-md border-blue-200 bg-slate-50 shadow-sm') \
                    .style('white-space: pre-line; margin-top: 10px; line-height: 1.5;')
            self.rendered = True
            self.container = ui.column().classes('gap-2')


        self.container.clear()

        # 2. Använd self.df och self.sort_job etc. direkt
        jobs = list(self.df['job_title'].unique())
        candidates = list(self.df['candidate_name'].unique())

        # --- Sorteringslogik (Använd self överallt) ---
        if self.sort_job:
            sorted_df = self.df[self.df.job_title == self.sort_job].sort_values(self.sort_metric, ascending=False)
            candidates = sorted_df['candidate_name'].tolist()
            customer_map = self.df.set_index('job_title')['customer'].to_dict()
            self.summary_label.text = f"Best fit for {self.sort_job} - {customer_map.get(self.sort_job, 'Unknown Customer')} :\n{', '.join(candidates[:3])} based on {self.sort_metric}"

        if self.sort_candidate:
            sorted_jobs = self.df[self.df.candidate_name == self.sort_candidate].sort_values(self.sort_metric, ascending=False)
            jobs = sorted_jobs['job_title'].tolist()
            job_customers = sorted_jobs['customer'].tolist()
            job_list = [f"{j} ({c})" for j, c in zip(jobs, job_customers)]
            self.summary_label.text = f"Best matches for candidate {self.sort_candidate}:\n{', '.join(job_list[:3])} based on {self.sort_metric}"
        # --- Bestäm Axlar ---
        if not self.flipped:
            x_items, y_items = jobs, candidates
            x_col, y_col = 'job_title', 'candidate_name'
            focus_x, focus_y = self.sort_job, self.sort_candidate
        else:
            x_items, y_items = candidates, jobs
            x_col, y_col = 'candidate_name', 'job_title'
            focus_x, focus_y = self.sort_candidate, self.sort_job

        pivot = self.df.set_index([y_col, x_col])

        # 3. Rita inuti self.container
        with self.container:
            with ui.grid(columns=len(x_items) + 1).classes('gap-1 items-center'):
                ui.label('')
                customer_map = self.df.set_index(x_col)['customer'].to_dict()
                # 🔝 HEADER
                for x_val in x_items:
                    cls = "font-bold text-center w-24 text-xs"
                    if focus_x and x_val == focus_x:
                        cls += " ring-2 ring-blue-500 bg-white"
                    elif focus_x:
                        cls += " opacity-40"
                    customer_name = customer_map.get(x_val, "Unknown Customer")
                    # ui.label(str(x_val)).classes(cls).on('click', lambda val=x_val: handle_click(val, x_col))
                    # ui.label(str(x_val)).on('click', lambda val=x_val: ui.notify(f"Clicked on {x_col}: {val}")).classes(cls)
                    with ui.label(f'{x_val} - {customer_name}').classes(cls).on('click', lambda val=x_val: self.update(sort_job=val if x_col == 'job_title' else None, sort_candidate=val if x_col == 'candidate_name' else None)):
                        ui.tooltip(f'Click to sort').classes('text-sm p-2 bg-slate-800 shadow-xl') \
                # 🔽 ROWS
                for y_val in y_items:
                    cls = "font-bold w-32 text-right pr-2 text-xs"
                    if focus_y and y_val == focus_y:
                        cls += " ring-2 ring-blue-500 bg-white"
                    elif focus_y:
                        cls += " opacity-40"
                    ui.label(str(y_val)).classes(cls).on('click', lambda val=y_val: self.update(sort_job=val if y_col == 'job_title' else None, sort_candidate=val if y_col == 'candidate_name' else None))

                    for x_val in x_items:
                        try:
                            # Här matchar nu y_val (namn) och x_val (id/namn) med pivot-indexet
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
                                # Tooltip logik
                                cand_name = y_val if not self.flipped else x_val
                                job_name = x_val if not self.flipped else y_val
                                
                                ui.tooltip(f"Candidate: {cand_name}\nJob: {job_name}\n\nCompetence: {row.comp_summary}\n\nAvailability: {row.avail_summary}") \
                                    .classes('text-xs p-3 bg-slate-800 shadow-xl') \
                                    .style('white-space: pre-line; max-width: 350px;')

                                with ui.element('div').style(f'background-color: {comp_color}') \
                                    .classes('flex-1 flex items-center justify-center'):
                                    ui.label(str(int(row.comp_score))).classes('text-white text-xs font-bold')

                                with ui.element('div').style(f'background-color: {avail_color}') \
                                    .classes('flex-1 flex items-center justify-center'):
                                    ui.label(str(int(row.availability_score))).classes('text-black text-xs font-bold')
                        
class MatchGrid:
    def __init__(self, df, mode='candidate'):
        self.orig_df = df
        self.df = df.copy()
        self.mode = mode
        self.container = ui.column().classes('w-full gap-2')
        self.sort_metric = 'comp_score'
        self.update_df()
        self.render()

    def update_df(self):
        clean_df = self.orig_df.drop_duplicates(subset=['candidate_name', 'job_title'])
        metric = self.sort_metric
        print("clean_df shape:", clean_df.shape)
        if self.mode == 'candidate':
            # 1. Sortera hela skiten först
            sorted_df = clean_df.sort_values(metric, ascending=False)
            
            # 2. Hitta vilka 10 kandidater som har bäst snitt eller bäst topp-match
            # Detta säkerställer att vi tar de 10 mest relevanta personerna
            top_10_names = sorted_df.groupby('candidate_name')[metric].max().nlargest(10).index
            
            relevant_data = sorted_df[sorted_df['candidate_name'].isin(top_10_names)]
            
            # 4. Ta ut de 3 bästa per person från detta urval
            self.df = relevant_data.groupby('candidate_name').head(3).copy()

        elif self.mode == 'job':
            sorted_df = clean_df.sort_values(metric, ascending=False)
            top_10_jobs = sorted_df.groupby('job_title')[metric].max().nlargest(10).index
            relevant_data = sorted_df[sorted_df['job_title'].isin(top_10_jobs)]
            self.df = relevant_data.groupby('job_title').head(3).copy()
            
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

    def render(self):
        self.container.clear()
        
        with self.container:
            with ui.row().classes('items-end gap-8 mb-6'):
                with ui.column().classes('gap-1'):
                    ui.label('Sort metric:').classes('text-[10px] font-bold text-slate-400 uppercase tracking-wider')
                    ui.radio(['comp_score', 'availability_score', 'combined_score'], 
                             value=self.sort_metric, 
                             on_change=lambda e: self.update(sort_metric=e.value)
                            ).props('dense').classes('text-sm')
                
                ui.button('Flip View', icon='swap_horiz', on_click=self.update_mode) \
                    .props('flat outline dense').classes('mb-1')

            grid_cls = 'grid grid-cols-[160px_140px_140px_140px] gap-x-2 gap-y-3 items-center max-w-fit'
            
            with ui.element('div').classes(grid_cls):
                ui.label(self.mode.capitalize()).classes('font-bold text-slate-400 text-[10px] uppercase pb-2')
                ui.label('Rank 1').classes('font-bold text-center text-slate-400 text-[10px] uppercase pb-2')
                ui.label('Rank 2').classes('font-bold text-center text-slate-400 text-[10px] uppercase pb-2')
                ui.label('Rank 3').classes('font-bold text-center text-slate-400 text-[10px] uppercase pb-2')

                group_col = 'candidate_name' if self.mode == 'candidate' else 'job_title'
                match_col = 'job_title' if self.mode == 'candidate' else 'candidate_name'
                
                unique_entities = sorted(self.df[group_col].unique())
                
                
                for entity in unique_entities:
                    subset = self.df[self.df[group_col] == entity].copy()
                    display_name = entity   
                    if self.mode == 'job':
                        customer = subset['customer'].iloc[0]
                        display_name = f"{entity}\n - {customer}"
                    with ui.label(display_name).style('white-space: pre-line').classes('font-bold text-slate-700 text-xs truncate pr-4 border-r border-slate-100 h-full flex items-center'):
                        ui.tooltip(f'Job: {display_name}\n\n').classes('text-sm p-2 bg-slate-800 shadow-xl')
                    
                    top_3 = subset.sort_values(self.sort_metric, ascending=False).head(3)
                    
                    for i in range(3):
                        if i < len(top_3):
                            row = top_3.iloc[i]
                            self._build_match_card(row, match_col)
                        else:
                            ui.element('div').classes('w-32 h-14 rounded border border-dashed border-slate-200 bg-slate-50/50')

    def _build_match_card(self, row, match_col):
        c_color = color_map.get(score_color(row.comp_score), '#e5e7eb')
        a_color = color_map.get(score_color(row.availability_score), '#e5e7eb')
        
        with ui.card().classes('p-0 w-32 h-14 shadow-sm overflow-hidden border border-slate-200 group hover:border-blue-300 transition-colors'):
            with ui.column().classes('gap-0 w-full h-full'):
                with ui.element('div').classes('w-full bg-slate-50 px-2 py-1 border-b'):
                    text = row[match_col]
                    ui.label(text).classes('text-[10px] font-bold truncate text-slate-500')
                
                with ui.row().classes('w-full flex-1 gap-0'):
                    with ui.element('div').style(f'background-color: {c_color}') \
                        .classes('flex-1 flex items-center justify-center'):
                        ui.label(str(int(row.comp_score))).classes('text-white text-sm font-bold shadow-sm')
                    
                    with ui.element('div').style(f'background-color: {a_color}') \
                        .classes('flex-1 flex items-center justify-center'):
                        ui.label(str(int(row.availability_score))).classes('text-slate-900 text-sm font-bold shadow-sm')

            ui.tooltip(f"{row[match_col]}\nJob: {row['job_title']} - {row['customer']}\nComp: {row.comp_summary}\nAvail: {row.avail_summary}") \
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
    fig = px.imshow(
        heatmap_data,
        labels=dict(x="Job Title", y="Candidate", color="Match Score"),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        color_continuous_scale='RdYlBu', # Rött (dåligt) till Blått (bra)
        aspect="auto" # Gör att den fyller ut containern snyggt
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

# Sampla från dessa listor istället
sampled_candidates = random.sample(list(all_candidates), 10)
sampled_jobs = random.sample(list(all_jobs), 10)

sampled_candidates_df = full_df[
    full_df['candidate_name'].isin(sampled_candidates) & 
    full_df['job_title'].isin(sampled_jobs)
].copy()

plot_df = full_df.sample(n=500).copy()
plot_df.drop_duplicates(subset=['candidate_name', 'job_title'], keep='first', inplace=True)
plot_df.reset_index(drop=True, inplace=True)
plot_df['comp_score'] = plot_df['comp_score'].astype(float)
plot_df['availability_score'] = plot_df['availability_score'].astype(float)
match_df = plot_df.copy()

@ui.page("/")
def index():
    chart = None
    plot_table = PlotTable(plot_df)  # Skapa tabellen en gång, den kommer att uppdateras av ChartSection
    # MatchGrid(match_df, mode='candidate')  # Visa kandidat-fokuserad grid först


    with ui.column().classes('w-full'):

        with ui.tabs() as tabs:
            t0 = ui.tab('Match Grid')
            t1 = ui.tab('Grid View')
            t2 = ui.tab('Plot View')
            t3 = ui.tab('Table View')
            t4 = ui.tab('Heatmap View')
            
        with ui.tab_panels(tabs, value=t0).classes('w-full'):

            with ui.tab_panel(t0):
                MatchGrid(match_df, mode='candidate')  # Visa kandidat-fokuserad grid först
            
            with ui.tab_panel(t1):
                ui.markdown("### Recruiter Dashboard Matrix")
                filter_test = FilterControl2(on_change=lambda: grid.update() if grid else None)  # Skapa filterkontrollerna
                filter_test.build()
                filter_test.set_visible(False)
                # ScoreGrid(sampled_candidates_df)
            
            with ui.tab_panel(t3):
                with ui.column().classes('w-full p-6 bg-slate-50 rounded-xl mt-4 border border-slate-200'):
                    ui.markdown("### Detailed Scores Table")
                    filter_section = FilterControl2(on_change=lambda: chart.update() if chart else None)
                    filter_section.build()
    
                    filter_section.set_visible(True)  # Visa filterkontrollerna i denna tab
                    plot_table.render(plot_df)  # Rendera tabellen med den initiala datan

            with ui.tab_panel(t2):
                    filter_section
                    chart = ChartSection(plot_df, filter_section, plot_table)
                    chart.build()  # Bygg och rendera grafen i tabben där den ska användas

            with ui.tab_panel(t4):
                ui.markdown("### Competence vs Availability Heatmap")
                # Heatmapen skapas direkt här
                heatmap_fig = create_heatmap(plot_table.df)  # Använd den data som är i tabellen (kan vara filtrerad)
                ui.plotly(heatmap_fig).classes('w-full h-[700px] bg-white rounded-lg shadow-sm border border-slate-100')

# Se till att ui.run ligger längst ner utanför alla funktioner
ui.run(port=8007, title="Recruiter AI Dashboard")
    


