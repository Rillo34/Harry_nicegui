from tkinter import dialog
from nicegui import ui
import random
from faker import Faker
from numpy import diff
import pandas as pd
from typing import List
from pandas import DataFrame
from datetime import datetime, timedelta


#------------------
# FUNCTIONS GENERAL
#------------------

def generate_test_data(n_candidates: int, n_jobs: int):
    fake = Faker("sv_SE")
    start_date = pd.to_datetime("2025-10-01")
    end_date = pd.to_datetime("2026-12-31")
    today = datetime.today()
    candidates = [
        {"cand_id": f"cand_{i+1:04d}", "cand_name": fake.name(), "last_assignment_date": fake.date_between_dates(date_start=start_date, date_end=end_date)}
        for i in range(n_candidates)
    ]

    # IT-jobb
    it_roles = [
        "Backend Developer", "Frontend Developer", "Fullstack Developer",
        "DevOps Engineer", "Cloud Engineer", "Data Engineer",
        "QA Engineer", "IT Support Technician", "UX/UI Designer"
    ]
    it_customers_pool = [
        "Spotify", "Klarna", "Ericsson", "Volvo Cars", "IKEA Digital",
        "H&M Group Tech", "King", "Telia", "SEB", "Nordea",
        "Scania IT", "Tink", "Sinch", "Voi", "Blocket",
        "Skatteverket IT", "Försäkringskassan IT", "Polisen IT"
    ]
    jobs =[]
    for i in range(n_jobs):
        received_date = today - timedelta(days=random.randint(0, 10))
        due_date = today + timedelta(days=random.randint(0, 14))

        jobs.append({
            "job_id": f"job_{i+1:03d}",
            "title": fake.random_element(it_roles),
            "customer": fake.random_element(it_customers_pool),
            "received_date": received_date.strftime('%Y-%m-%d'),
            "due_date": due_date.strftime('%Y-%m-%d'),
        })
    return candidates, jobs

def generate_scores_df(candidates: list[dict], jobs: list[dict], nr_rows: int) -> pd.DataFrame:
    rows = []
    used = set()  # (cand_id, job_id)
    while len(rows) < nr_rows:
        cand = random.choice(candidates)
        job = random.choice(jobs)
        key = (cand["cand_id"], job["job_id"])
        if key in used:
            continue  # hoppa över dublett
        used.add(key)
        comp_score = random.randint(20, 100)
        avail_score = random.randint(20, 100)
        rows.append({
            "cand_name": cand["cand_name"],
            "job_title": job["title"],
            "customer": job["customer"],
            "received_date": job["received_date"],
            "due_date": job["due_date"],
            "comp_score": comp_score,
            "avail_score": avail_score,
            "combined_score": round((comp_score * 0.5) + (avail_score * 0.5), 0),
            "last_assignment_date": cand["last_assignment_date"],
            "cand_id": cand["cand_id"],
            "job_id": job["job_id"],
            "cv_sent": False,
            "cv_sent_by": "",
            "cv_sent_at": "",
            "id": f"{cand['cand_id']}_{job['job_id']}"
        })
        df = pd.DataFrame(rows)
        df['due_date'] = pd.to_datetime(df['due_date'])
        today = datetime.today().date()
        df['days_left'] = (df['due_date'] - pd.Timestamp(today)).dt.days
        df['due_date'] = df['due_date'].dt.strftime('%Y-%m-%d')
    return df

def handle_status_change(e, row):  # NOT USED NOW
    ui.notify(f'Status ändrad för rad {row["id"]}: {e.value}')
    # row['status'] = e.value   # om du vill uppdatera direkt

def open_popup(row): # NOT USED NOW
    with ui.dialog() as dialog, ui.card():
        ui.label(f'Redigerar rad {row["id"]} - {row["name"]}').classes('text-lg')
        ui.input('Namn').bind_value(row, 'name')
        ui.select(['Aktiv', 'Inaktiv', 'Väntar'], label='Status').bind_value(row, 'status')
        ui.button('Spara', on_click=dialog.close).classes('mt-4')
    dialog.open()



# --------------------------
# CLASSES
# ------------------------

class FilterControl:
    def __init__(self, on_change: dict[str, callable]):
        self.on_change_match = on_change.get('match')
        self.on_change_overall = on_change.get('overall')
        self.on_reset = on_change.get('reset')
        self.minimum_match_filter = 50
        self.minimum_overall_filter = 50
        self.start_match_filter = 50
        self.start_overall_filter = 50
        self.container = None

    def reset_filters(self):
        self.on_reset(match_value=self.start_match_filter, overall_value=self.start_overall_filter)   
        self.minimum_match_filter = self.start_match_filter
        self.minimum_overall_filter = self.start_overall_filter


    def build(self):
        # w-64 styr bredden, gap-1 gör det mer kompakt
        with ui.column().classes('w-96 p-4 bg-slate-50 rounded-xl mb-4 border gap-1 shadow-sm') as filter_container:
            with ui.row().classes('w-full items-center gap-2'):
                ui.label('Match rating:').classes('text-xs text-slate-500 w-30')
                self.minimum_match_slider = ui.slider(min=0, max=100, value=50)\
                    .props('dense')\
                    .classes('col')\
                    .bind_value(self, 'minimum_match_filter')\
                    .on('update:model-value', self.on_change_match)
                ui.label().classes('text-xs font-mono w-6')\
                    .bind_text_from(self.minimum_match_slider, 'value', backward=lambda v: f'{int(v)}')
            with ui.row().classes('w-full items-center gap-2'):
                ui.label('Overall rating:').classes('text-xs text-slate-500 w-30')
                self.minimum_overall_slider = ui.slider(min=0, max=100, value=50)\
                    .props('dense')\
                    .classes('col')\
                    .bind_value(self, 'minimum_overall_filter')\
                    .on('update:model-value', self.on_change_overall)
                ui.label().classes('text-xs font-mono w-6')\
                    .bind_text_from(self.minimum_overall_slider, 'value', backward=lambda v: f'{int(v)}')
            ui.button('Reset filters', on_click=self.reset_filters).classes('self-end mt-2')

    
class CandidatePopup:
    def __init__(self, data: DataFrame):
        self.df = data
        self.cand_id = data['cand_id'].iloc[0]
        self.name = data['name'].iloc[0]
        self.last_assignment_date = data['last_assignment_date'].iloc[0]
        self.availability = None
        self.color_code = None

    def build(self):
        columns = [{'name': col, 'label': col.replace('_', ' ').title(), 'field': col} for col in self.df.columns if col in ['cand_id', 'name', 'last_assignment_date']]
        ui.table(
            columns=columns,
            rows=[
                {'field': 'Candidate ID', 'value': self.cand_id},
                {'field': 'Name', 'value': self.name},
                {'field': 'Last Assignment Date', 'value': self.last_assignment_date},
                {'field': 'Availability', 'value': self.availability},
                {'field': 'Color Code', 'value': self.color_code},
            ]
        )

class CandidateTable:
    def __init__(self, data: DataFrame):
        self.data = data
        self.orig_df = data.copy()  # behåll originaldata för att kunna återställa efter filter
        # self.df = data.copy()  # behåll originaldata för att kunna återställa efter filter
        self.df = data.copy().reset_index(drop=True)
        self.table = None
        self.user = "Rickard"  # hårdkodad användare för test, i verklig app skulle detta komma från inloggning
        self.table_container = None
        self.minimum_match_filter = 50
        self.minimum_overall_filter = 50
        self.df['row_id'] = self.df.index.astype(str)
        self.set_availability()  # beräkna tillgänglighet och färgkod innan tabellen byggs
        self.apply_filters()  # initialt ingen filter, så filtered_df är samma som df
        

    def build(self):
        df = self.filtered_df.copy()
        from datetime import datetime
        def toggle(column: dict, visible: bool) -> None:
            column['classes'] = '' if visible else 'hidden'
            column['headerClasses'] = '' if visible else 'hidden'
            self.table.update()
        
        with ui.row().classes('w-full gap-4'):
            pass
        with ui.column().classes('w-full') as self.table_container:
            with ui.row().classes('w-full'):
                rows = df.to_dict(orient='records')
                self.table = ui.table(
                    columns = [
                        {'name': 'cand_name', 'label': 'Candidate', 'field': 'cand_name', 'sortable': True},
                        {'name': 'job_title', 'label': 'Job Title', 'field': 'job_title', 'sortable': True},
                        {'name': 'customer', 'label': 'Customer', 'field': 'customer', 'sortable': True},
                        {'name': 'days_left', 'label': 'Due in days', 'field': 'days_left', 'sortable': True},
                        {'name': 'comp_score', 'label': 'Match Rating', 'field': 'comp_score', 'sortable': True},
                        {'name': 'combined_score', 'label': 'Overall Rating', 'field': 'combined_score', 'sortable': True},
                        {'name': 'availability', 'label': 'Availability', 'field': 'weeks_since_last_assignment', 'sortable': True},
                        {'name': 'weeks_since_last_assignment', 'label': 'Weeks since assignment', 'field': 'weeks_since_last_assignment', 'sortable': True, 'visible': False},
                        {'name': 'months_since_last_assignment', 'label': 'Months since assignment', 'field': 'months_since_last_assignment', 'sortable': True},
                        {'name': 'cv_sent', 'label': 'CV Sent', 'field': 'cv_sent', 'sortable': True}
                    ],
                    rows=rows,
                    row_key='row_id',
                    pagination={'rowsPerPage': 20, 'sortBy': 'availability', 'descending': True},
                ).props('dense height=1200px').classes('height-full')
                menu_button = ui.button(icon='menu')

        hidden_columns = ['weeks_since_last_assignment']  # kolumner som är dolda initialt
        for column in self.table.columns:
            if column['name'] in hidden_columns:
                column['classes'] = 'hidden'
                column['headerClasses'] = 'hidden'
        with menu_button:
            with ui.menu(), ui.column().classes('gap-0 p-2'):
                for column in self.table.columns:
                    if column['name'] in hidden_columns:
                        value = False
                    else:
                        value = True
                    ui.switch(column['label'], value=value, on_change=lambda e,
                            column=column: toggle(column, e.value))

        self.table.add_slot('body-cell-availability', '''
            <q-td :props="props"
                :style="`background:${props.row.color_code}; color:black;`"
                class="text-center font-bold">
                {{ props.row.availability }}
            </q-td>
        ''')
        self.table.add_slot('body-cell-months_since_last_assignment', '''
            <q-td :props="props"
                :style="props.row.months_since_last_assignment > 0
                    ? `color:red; font-weight:900;`
                    : 'font-weight:900;'">
                {{ props.row.months_since_last_assignment }}
            </q-td>
        ''')
        self.table.add_slot('body-cell-cand_name', '''
            <q-td :props="props"
                class="cursor-pointer"
                @click="$parent.$emit('name_click', props.row)">
                {{ props.row.cand_name }}
            </q-td>
        ''')
        self.table.add_slot('body-cell-cv_sent', '''
            <q-td :props="props" class="cursor-pointer"
                @click="$parent.$emit('cv-click', props.row)">
                
                <q-icon 
                    :name="props.row.cv_sent ? 'check_circle' : 'radio_button_unchecked'"
                    :color="props.row.cv_sent ? 'green' : 'grey'"
                    :size="props.row.cv_sent ? '20px' : '20px'">
                    
                    <q-tooltip v-if="props.row.cv_sent" class="text-lg q-pa-md">
                        Sent by: {{ props.row.cv_sent_by }}<br>
                        At: {{ props.row.cv_sent_at }}
                    </q-tooltip>
                </q-icon>

            </q-td>
        ''')
        self.table.add_slot('body-cell-days_left', '''
            <q-td :props="props" class="text-right">
                <q-badge
                :color="props.row.days_left <= 2 ? 'red' :
                        props.row.days_left <= 6 ? 'orange' : 'grey-7'"
                text-color="white"
                style="font-weight:700; font-size:13px; min-width:40px;
                        display:inline-flex; justify-content:center;"
                >
                {{ props.row.days_left }}
                </q-badge>
            </q-td>
            ''')


        self.table.on('name_click', self.name_click)
        self.table.on('cv-click', self.cv_click)

    def on_change_match(self, e):
        min_match = e.args
        self.minimum_match_filter = min_match
        self.filtered_df = self.df[
            (self.df['comp_score'] >= min_match) &
            (self.df['combined_score'] >= self.minimum_overall_filter)
        ]
        self.table.rows = self.filtered_df.to_dict(orient='records')
        self.table.update()
    
    def on_change_overall(self, e):
        min_overall = e.args
        self.minimum_overall_filter = min_overall
        self.filtered_df = self.df[
            (self.df['combined_score'] >= min_overall) &
            (self.df['comp_score'] >= self.minimum_match_filter)
        ]
        self.table.rows = self.filtered_df.to_dict(orient='records')
        self.table.update()
    
    def reset_filters(self, match_value=None, overall_value=None):
        print (f"Resetting filters to match: {match_value}, overall: {overall_value}")
        self.minimum_match_filter = match_value 
        self.minimum_overall_filter = overall_value 
        filtered_df = self.df[
            (self.df['comp_score'] >= self.minimum_match_filter) &
            (self.df['combined_score'] >= self.minimum_overall_filter)
        ]
        self.table.rows = filtered_df.to_dict(orient='records')
        self.table.update()

    def name_click(self, e):
        ui.notify(f'Klickade på kandidat: {e.args["cand_name"]}, id: {e.args["cand_id"]}')
        cand_df = self.filtered_df[self.filtered_df['cand_id'] == e.args['cand_id']]
        with ui.dialog() as dialog, ui.card().classes("w-auto max-w-none"):
            with ui.column().classes("min-w-max"):
                ui.label(f'Filtered jobs for {e.args["cand_name"]}').classes("text-xl font-bold mb-2")
                cand_table = CandidateTable(cand_df)
                cand_table.build()
                ui.button("Close", on_click=dialog.close)
                dialog.open()

    def cv_click(self, e):
        ui.notify(f"CV click: {e.args['cand_name']}")
        print (f"CV click event args: {e.args}")    
        with ui.dialog() as dialog, ui.card().classes("w-[400px] p-4"):
            ui.label(f"CV sent for {e.args['cand_name']}").classes("text-lg font-bold mb-4")
            sent_checkbox = ui.checkbox("CV sent", value=e.args["cv_sent"])
            if sent_checkbox.value:
                sent_by = ui.input("Sent by", value=e.args.get("cv_sent_by", ""))
                sent_at = ui.input("Sent at", value=e.args.get("cv_sent_at", ""))
            else:
                sent_by = ui.input("Sent by", value=self.user)
                sent_at = ui.input("Sent at", value=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"))

            def save():
                rid = e.args["id"]
                self.filtered_df.loc[self.filtered_df["id"] == rid, "cv_sent"] = sent_checkbox.value
                self.filtered_df.loc[self.filtered_df["id"] == rid, "cv_sent_by"] = sent_by.value
                self.filtered_df.loc[self.filtered_df["id"] == rid, "cv_sent_at"] = sent_at.value

                self.update(self.filtered_df)
                dialog.close()

            ui.button("Save", on_click=save)
            ui.button("Cancel", on_click=dialog.close).props("flat")

        dialog.open()


    def apply_filters(self):
        min_match = self.minimum_match_filter
        min_overall = self.minimum_overall_filter
        self.filtered_df = self.df[
            (self.df['comp_score'] >= min_match) &
            (self.df['combined_score'] >= min_overall)
        ]

    def update(self, new_data: DataFrame):
        self.df = new_data
        self.df['row_id'] = self.df.index.astype(str)
        self.set_availability()  
        self.apply_filters()
        self.table.rows = self.filtered_df.to_dict(orient='records')
        self.table.update()

    def set_availability(self):
        def assign_color_code(diff):
            if diff >    0:
                return "#ff8a80"   # ljus röd
            elif diff <= 0 and diff >= -4:
                return "#ffb74d"   # ljus orange
            elif diff <-4 and diff >= -8:
                return "#fff176"   # ljus gul
            else:
                return "#81c784"   # ljus grön
        def assign_availability_label(diff):
            if diff < 0:
                return " NOW "
            elif diff <= 4:
                return "< 1 month"
            elif diff <= 8:
                return "< 2 months"
            elif diff <= 12:
                return "< 3 months"
            else:
                return "More than 3 months"
        for idx, row in self.df.iterrows():
            end_of_last_assignment = pd.to_datetime(row['last_assignment_date'])
            weeks_since_last_assignment = (pd.Timestamp.today() - end_of_last_assignment).days // 7
            time_to_available = (end_of_last_assignment-pd.Timestamp.today()).days
            available_in_weeks = -int(time_to_available // 7)
            if time_to_available < 0:
                self.df.at[idx, 'availability'] = "NOW"
            else:
                self.df.at[idx, 'availability'] = end_of_last_assignment.strftime("%Y-%m")
            self.df.at[idx, 'available_in'] = available_in_weeks
            self.df.at[idx, 'within'] = assign_availability_label(available_in_weeks)
            self.df.at[idx, 'weeks_since_last_assignment'] = available_in_weeks
            self.df.at[idx, 'months_since_last_assignment'] = int(available_in_weeks / 4) if weeks_since_last_assignment >= 0 else 0
            self.df.at[idx, 'color_code'] = assign_color_code(available_in_weeks)


candidates, jobs = generate_test_data(10, 10)
df = generate_scores_df(candidates, jobs, 100)
print (df.head())

@ui.page('/')
def main_page():
    def update_table():
        new_candidates, new_jobs = generate_test_data(10, 10)
        new_df = generate_scores_df(new_candidates, new_jobs, 100)
        candidate_table.update(new_df)
    ui.label('Candidates for IT jobs').classes('text-2xl font-bold mb-4')
    candidate_table = CandidateTable(df)
    callbacks = {
        'match': candidate_table.on_change_match,
        'overall': candidate_table.on_change_overall,
        'reset': candidate_table.reset_filters
    }
    filter_control = FilterControl(on_change=callbacks)
    filter_control.build()
    with ui.row():    
        ui.button('New data', on_click=update_table)
        ui.label('There are 100 rows in the table, take filter to ZERO to see all').classes('text-sm text-slate-500')
    candidate_table.build()
    
ui.run(port = 8005)
