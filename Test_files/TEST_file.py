# from nicegui import ui

# # Uppdaterad indata med din nya struktur
# input_data = {
#     'candidates': [
#         {
#             'candidate_id': 'DS_71',
#             'candidate_name': 'Göran',
#             'availability_assessment': 'OK',
#             'availability_score': 67,
#             'problem_months': ['2026-01', '2026-02'],
#             'competence_score': 85,
#             'competence_assessment': 'EXCELLENT',
#             'conflicting_projects': ['Gångaren'],
#             'summary': "Göran is heavily overbooked in Jan/Feb."
#         },
#         {
#             'candidate_id': 'AX_42',
#             'candidate_name': 'Anna',
#             'availability_assessment': 'BAD',
#             'availability_score': 20,
#             'problem_months': ['2026-01', '2026-03', '2026-04'],
#             'competence_score': 92,
#             'competence_assessment': 'EXCELLENT',
#             'conflicting_projects': ['Slussen Pro', 'Bulten'],
#             'summary': "Anna has major conflicts during spring 2026."
#         }
#     ],
#     'overall_summary': "Flera kandidater har schemakonflikter. Se detaljer nedan."
# }

# def create_ui():
#     ui.query('body').style('background-color: #f4f7f9;')

#     with ui.column().classes('w-full items-center q-pa-lg'):
#         # Header Area
#         with ui.row().classes('w-full max-w-6xl items-center justify-between bg-white q-pa-md shadow-sm rounded-lg q-mb-md'):
#             with ui.column():
#                 ui.label('Rekryteringsöversikt').classes('text-h5 text-weight-bold')
#                 ui.label(input_data['overall_summary']).classes('text-grey-6')

#         # Tabell-definition
#         columns = [
#             {'name': 'name', 'label': 'Namn', 'field': 'candidate_name', 'align': 'left'},
#             {'name': 'comp_score', 'label': 'Kompetens (%)', 'field': 'competence_score', 'sortable': True},
#             {'name': 'comp_assess', 'label': 'Komp. Bedömning', 'field': 'competence_assessment'},
#             {'name': 'avail_score', 'label': 'Tillgänglighet (%)', 'field': 'availability_score', 'sortable': True},
#             {'name': 'avail_assess', 'label': 'Tillgänglighet Status', 'field': 'availability_assessment'},
#             {'name': 'conflicts', 'label': 'Konfliktmånader', 'field': 'problem_months'},
#         ]

#         # Skapa tabellen
#         with ui.table(columns=columns, rows=input_data['candidates'], row_key='candidate_id').classes('w-full max-w-6xl shadow-md') as table:
            
#             # Custom slot för Kompetens Score (Progress bar i cellen)
#             table.add_slot('body-cell-comp_score', '''
#                 <q-td :props="props">
#                     <div class="row items-center no-wrap">
#                         <q-linear-progress :value="props.value / 100" color="blue" class="q-mr-sm" style="width: 60px" />
#                         {{ props.value }}%
#                     </div>
#                 </q-td>
#             ''')

#             # Custom slot för Kompetens Bedömning (Badge)
#             table.add_slot('body-cell-comp_assess', '''
#                 <q-td :props="props">
#                     <q-badge :color="props.value === 'EXCELLENT' ? 'purple' : 'blue'">
#                         {{ props.value }}
#                     </q-badge>
#                 </q-td>
#             ''')

#             # Custom slot för Tillgänglighet Score (Färgad text)
#             table.add_slot('body-cell-avail_score', '''
#                 <q-td :props="props" :class="props.value < 50 ? 'text-red text-weight-bold' : 'text-green'">
#                     {{ props.value }}%
#                 </q-td>
#             ''')

#             # Custom slot för Tillgänglighet Status (Badge)
#             table.add_slot('body-cell-avail_assess', '''
#                 <q-td :props="props">
#                     <q-badge :color="props.value === 'OK' ? 'green' : 'red'">
#                         {{ props.value }}
#                     </q-badge>
#                 </q-td>
#             ''')

#             # Custom slot för Konfliktmånader (Chips)
#             table.add_slot('body-cell-conflicts', '''
#                 <q-td :props="props">
#                     <div class="row gap-1">
#                         <q-chip v-for="month in props.value" :key="month" size="sm" icon="event" color="orange-1" text-color="orange-9">
#                             {{ month }}
#                         </q-chip>
#                     </div>
#                 </q-td>
#             ''')

# # Kör UI-bygget
# create_ui()

# # Starta på port 8006
# if __name__ in {"__main__", "__mp_main__"}:
#     ui.run(port=8006, title="Kandidattabell")

from nicegui import ui

# Uppdaterad indata med kommentarer
input_data = {
    'candidates': [
        {
            'candidate_id': 'DS_71',
            'candidate_name': 'Göran',
            'availability_assessment': 'OK',
            'availability_score': 67,
            'problem_months': ['2026-01', '2026-02'],
            'competence_score': 85,
            'competence_assessment': 'EXCELLENT',
            'competence_comment': 'Göran har spetskompetens inom stålkonstruktion men behöver avlastning i början på året.',
            'conflicting_projects': ['Gångaren'],
            'summary': "Göran is heavily overbooked in Jan/Feb due to Gångaren."
        },
        {
            'candidate_id': 'AX_42',
            'candidate_name': 'Anna',
            'availability_assessment': 'BAD',
            'availability_score': 20,
            'problem_months': ['2026-01', '2026-03', '2026-04'],
            'competence_score': 92,
            'competence_assessment': 'EXCELLENT',
            'competence_comment': 'Högsta tekniska poäng i gruppen. Mycket erfaren projektledare.',
            'conflicting_projects': ['Slussen Pro', 'Bulten'],
            'summary': "Anna has major conflicts during spring 2026 but is technically superior."
        }
    ],
    'overall_summary': "Analys klar: Anna är tekniskt starkast men Göran är mer tillgänglig. Överväg att flytta resurser från Gångaren för att frigöra Göran."
}

def create_ui():
    ui.query('body').style('background-color: #f0f2f5; font-family: "Segoe UI", Roboto, sans-serif;')

    with ui.column().classes('w-full items-center q-pa-lg'):
        
        # --- OVERALL SUMMARY SECTION ---
        with ui.card().classes('w-full max-w-6xl q-pa-md border-l-8 border-blue-600 shadow-sm'):
            with ui.row().classes('items-center no-wrap'):
                ui.icon('analytics', size='md').classes('text-blue-600 q-mr-sm')
                with ui.column():
                    ui.label('Övergripande Analys').classes('text-overline text-grey-7')
                    ui.label(input_data['overall_summary']).classes('text-body1 text-weight-medium')

        # --- TABLE SECTION ---
        columns = [
            {'name': 'name', 'label': 'Namn', 'field': 'candidate_name', 'align': 'left', 'sortable': True},
            {'name': 'comp_assess', 'label': 'Bedömning', 'field': 'competence_assessment', 'align': 'center'},
            {'name': 'comp_score', 'label': 'Matchning', 'field': 'competence_score', 'align': 'center', 'sortable': True},
            {'name': 'avail_assess', 'label': 'Status', 'field': 'availability_assessment', 'align': 'center'},
            {'name': 'comment', 'label': 'Kommentar', 'field': 'competence_comment', 'align': 'left'},
            {'name': 'conflicts', 'label': 'Konflikter', 'field': 'problem_months', 'align': 'left'},
        ]

        with ui.table(columns=columns, rows=input_data['candidates'], row_key='candidate_id').classes('w-full max-w-6xl shadow-md bg-white') as table:
            
            # 1. Kompetens Bedömning (Badge)
            table.add_slot('body-cell-comp_assess', '''
                <q-td :props="props">
                    <q-badge :color="props.value === 'EXCELLENT' ? 'indigo-10' : 'blue-6'">
                        {{ props.value }}
                    </q-badge>
                </q-td>
            ''')

            # 2. Kompetens Score (Färgad siffra)
            table.add_slot('body-cell-comp_score', '''
                <q-td :props="props">
                    <div class="text-weight-bold" :class="props.value > 80 ? 'text-green-8' : 'text-blue-7'">
                        {{ props.value }}%
                    </div>
                </q-td>
            ''')

            # 3. Tillgänglighet Status (Badge med ikon)
            table.add_slot('body-cell-avail_assess', '''
                <q-td :props="props">
                    <q-badge :color="props.value === 'OK' ? 'green-7' : 'red-7'" outline>
                        <q-icon :name="props.value === 'OK' ? 'check_circle' : 'warning'" size="xs" class="q-mr-xs" />
                        {{ props.value }}
                    </q-badge>
                </q-td>
            ''')

            # 4. Kommentar (Kursiv och lite diskretare)
            table.add_slot('body-cell-comment', '''
                <q-td :props="props" style="max-width: 300px; white-space: normal;">
                    <span class="text-italic text-grey-8">{{ props.value }}</span>
                </q-td>
            ''')

            # 5. Konfliktmånader (Chips)
            table.add_slot('body-cell-conflicts', '''
                <q-td :props="props">
                    <div class="row gap-1">
                        <q-chip v-for="month in props.value" :key="month" size="xs" color="red-1" text-color="red-9">
                            {{ month }}
                        </q-chip>
                    </div>
                </q-td>
            ''')

# Initialisera och kör
create_ui()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8006, title="Kandidatanalys")