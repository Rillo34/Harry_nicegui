from tokenize import group
from xml.parsers.expat import model
from nicegui import ui
from typing import List, Dict
from datetime import date, timedelta
import sys, os
from typing import Dict, List, Set
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent / 'backend'))
from nicegui import ui
from typing import List, Dict
from datetime import date
from backend.models import CandidateResultLong, RequirementResult
from nicegui import ui
from typing import List, Dict
import asyncio
from datetime import date
from niceGUI.api_fe import APIController, UploadController
from niceGUI import fe_testfile
import pandas as pd



FIT_COLORS = {
    "EXCELLENT": "#3b82f6",  # blå
    "GOOD": "#22c55e",       # grön
    "OK": "#eab308",         # gul
    "POOR": "#ef4444",       # röd
}
FIT_VALUES = ["POOR", "OK", "GOOD", "EXCELLENT"]
FIT_VALUES_START = ["GOOD", "EXCELLENT"]


class JobFitGrid:
    def __init__(self, df_gross):
        self.grid_container = ui.column()
        self.df = df_gross
        self.thresholds = { "OK": 25, "GOOD": 50, "EXCELLENT": 75 }
        results = []
        for job_id, group in df_gross.groupby("job_id"):
            best_comp, best_avail = self.best_fit_from_df(group)
            print(f"Job {job_id}: Best Competence Fit = {best_comp}, Best Availability Fit = {best_avail}")
            max_count = group[ (group["job_fit"] == best_comp) & (group["availability_fit"] == best_avail) ].shape[0]
            job_title = group["job_title"].iloc[0]
            customer = group["customer"].iloc[0]
            results.append((job_id, best_comp, best_avail, max_count, job_title, customer))
        self.df_max = pd.DataFrame(results, columns=["job_id", "best_comp", "best_avail", "max_count", "job_title", "customer"])
        self.df_smaller = self.df[["job_id", "job_title", "customer"]].drop_duplicates().reset_index(drop=True)
        self.build_ui()
        self.update_match_counts()
        self.sort_by("competence_fit")
        self.render_grid()



    def best_fit_from_df(self, df):
        best_job_fit = max( df["job_fit"], key=lambda v: FIT_VALUES.index(v) )
        best_candidates = df[df["job_fit"] == best_job_fit]
        best_avail_fit = max( best_candidates["availability_fit"], key=lambda v: FIT_VALUES.index(v) )
        return best_job_fit, best_avail_fit
    
    
    def update_match_counts(self):
        selected_job_fits = set(self.job_select.value)
        print("Selected job fits:", selected_job_fits)
        selected_avail_fits = set(self.avail_select.value) 
        print("Selected availability fits:", selected_avail_fits)   
        mask = ( df_gross["job_fit"].isin(selected_job_fits) & df_gross["availability_fit"].isin(selected_avail_fits) ) 
        df_filtered = df_gross[mask]
        print(df_filtered)
        match_counts = df_filtered.groupby("job_id").size()
        print(match_counts)
        self.df_max["filter_match"] = self.df_max["job_id"].map(match_counts).fillna(0).astype(int)

        # self.build_ui()


    def job_fit_color(self, fit: str) -> str:
        return {
            "EXCELLENT": "bg-blue-400",
            "GOOD": "bg-green-400",
            "OK": "bg-yellow-300",
            "POOR": "bg-red-400",
        }.get(fit, "bg-gray-300")

    
    def build_ui(self):

        with ui.row().classes('w-full items-center'):
            model = {'sort_by': 'competence_fit'}
            label = ui.label().bind_text_from(model, 'sort_by', lambda v: f'Sorting by: {v}').classes('text-lg p-2 font-bold')
            ui.switch(on_change=lambda e: (model.update(sort_by='availability_fit' if e.value else 'competence_fit'), self.sort_by(model['sort_by'])))
            ui.space()
            self.job_select = ui.select(FIT_VALUES, multiple=True, value=FIT_VALUES_START, label='Competence fit', on_change=self.on_filter_change) \
            .classes('w-64').props('use-chips')
            self.avail_select = ui.select(FIT_VALUES, multiple=True, value=FIT_VALUES_START, label='Availability fit', on_change=self.on_filter_change) \
            .classes('w-64').props('use-chips')
        self.grid_container = ui.column()
        with ui.column().classes("w-80 p-4 border rounded gap-2"):
            min_max_range = ui.range(min=0, max=100, value={'min': 20, 'max': 80})
            ui.label().bind_text_from(min_max_range, 'value', backward=lambda v: f'min: {v["min"]}, max: {v["max"]}')



    def render_grid(self):
        self.grid_container.clear()
        exclude_cols = ["job_title"]
        with self.grid_container:
            grid = ui.grid(columns=len(self.df_max.columns)+1).classes('gap-1 p-2')
            with grid:
                # Header
                for col in self.df_max.columns:
                    ui.label(col).classes('font-bold max-w-60 truncate')
                ui.label("Select")

                # Rows
                for row_idx, row in self.df_max.iterrows():
                    for col, value in row.items():

                        # färgade celler för best_comp / best_avail
                        if col in ("best_comp", "best_avail"):
                            label = ui.label(f"max: {value}").classes(
                                f"p-2 rounded text-black font-boldborder-4 cursor-pointer {self.job_fit_color(value)}"
                            ).on('click', lambda e, c=col: self.sort_by(c))
                        elif col == "max_count":
                            label = ui.label(f'candidates on max: {value}').classes("text-center text-lg p-2 rounded bg-gray-100")

                        else:
                            label = ui.label(str(value)).classes("text-center text-lg p-2 rounded bg-gray-100")

                        with label:
                            ui.tooltip(f'{row["job_title"]} at {row["customer"]}').style(
                                'max-width: 400px; font-size: 16px; padding: 16px; white-space: normal;'
                            )
                        
                    ui.checkbox()
                    print("df_smaller", self.df_smaller)


    def sort_by(self, column):
        print(f"Sorting by {column}")

        if column == "competence_fit":
            primary = "best_comp"
            secondary = "best_avail"
        else:
            primary = "best_avail"
            secondary = "best_comp"

        sort_key = lambda v: FIT_VALUES.index(v)

        self.df_max["_sort_primary"] = self.df_max[primary].map(sort_key)
        self.df_max["_sort_secondary"] = self.df_max["best_avail"].map(sort_key)

        # sortera
        self.df_max = (
            self.df_max
            .sort_values(by=["_sort_primary", "_sort_secondary"], ascending=False)
            .drop(columns=["_sort_primary", "_sort_secondary"])
            .reset_index(drop=True)
        )

        self.render_grid()
    

    def on_filter_change(self, e):
        print("Filter changed")
        self.update_match_counts()
        self.render_grid()            

        
jobs = fe_testfile.get_jobrequest()
print("antal jobb", len(jobs))
pairs = [(job["title"], job["customer"]) for job in jobs]
print(pairs)
df_max_list =[]
rows = []
list_of_matches = []
for job in jobs:
    job_id = job["job_id"]
    job_title = job["title"]
    customer = job["customer"]
    dummy_data = fe_testfile.get_grid_values(job_id)
    list_of_matches.append(dummy_data)
    for fitlist in dummy_data:
        # max_comp_for_the_job, max_avail_for_the_job = best_fit_value(fitlist.candidate_fit)
        # values = [job_id, max_comp_for_the_job, max_avail_for_the_job,job_title, customer]
        for cand in fitlist.candidate_fit:  # cand = ShortCandidateAssessment
            rows.append({
                "candidate_id": cand.candidate_id,
                "job_title": job_title,
                "customer": customer,
                "job_id": job_id,
                "job_fit": cand.job_fit,
                "availability_fit": cand.availability_fit,
                "score": cand.score,
                "recruiter": cand.recruiter,
            })

df_gross = pd.DataFrame(rows) 
print(df_gross)
job_fit_grid = JobFitGrid(df_gross)
# print("----LIST OF MATCHES----\n", list_of_matches)
# grid_container = ui.column()
# 

# print("---DUMMY DATA---\n", list_of_matches)
# render_fit_grid(dummy_data)
# df_max = pd.DataFrame(df_max_list, columns=["job_id", "best_comp", "best_avail", "title", "customer"])
# df_smaller = df_max.copy()
# df_smaller.drop(columns=["title", "customer"], inplace=True)
# df_smaller["match_count"] = 0
# print(df_max)
# render_fit_grid()
ui.run(port=8001)
