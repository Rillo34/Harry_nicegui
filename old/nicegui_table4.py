from nicegui import ui
import uuid
from typing import Dict, List, Set

# Sample data (as provided)
candidates = [
    {
        "id": str(uuid.uuid4()),
        "name": "Alice Smith",
        "education": "MSc Computer Science",
        "score": 85,
        "email": "alice@example.com",
        "phone": "123-456-7890",
        "skills": ["Python", "Java"],
        "is_shortlisted": False,
        "requirements": [
            {"reqname": "Programming", "status": "YES", "ismusthave": True, "source": "JD"},
            {"reqname": "Teamwork", "status": "MAYBE", "ismusthave": False, "source": "USER"},
            {"reqname": "Leadership", "status": "NO", "ismusthave": True, "source": "JD"}
        ]
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Bob Johnson",
        "education": "BFA Graphic Design",
        "score": 78,
        "email": "bob@example.com",
        "phone": "234-567-8901",
        "skills": ["UI/UX", "Figma"],
        "is_shortlisted": False,
        "requirements": [
            {"reqname": "Design", "status": "YES", "ismusthave": True, "source": "JD"},
            {"reqname": "Coding", "status": "NO", "ismusthave": False, "source": "USER"}
        ]
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Carol White",
        "education": "MBA",
        "score": 92,
        "email": "carol@example.com",
        "phone": "345-678-9012",
        "skills": ["Leadership", "Agile"],
        "is_shortlisted": True,
        "requirements": [
            {"reqname": "Management", "status": "YES", "ismusthave": True, "source": "JD"},
            {"reqname": "Coding", "status": "NO", "ismusthave": False, "source": "USER"}
        ]
    }
]

def get_candidate_table(candidates):

    # Prepare data for table (convert skills list to string)
    rows = [
        {**candidate, "skills": ", ".join(candidate["skills"])} for candidate in candidates
    ]

    # Get unique requirement names for filters
    req_names: Set[str] = set()
    for candidate in candidates:
        for req in candidate["requirements"]:
            req_names.add(req["reqname"])
    req_names = sorted(req_names)  # Sort for consistent display

    # Define table columns
    columns = [
        {"name": "id", "label": "ID", "field": "id", "align": "left"},
        {"name": "name", "label": "Name", "field": "name", "align": "left", "sortable": True},
        {"name": "education", "label": "Education", "field": "education", "align": "left"},
        {"name": "score", "label": "Score", "field": "score", "align": "center"},
        {"name": "email", "label": "Email", "field": "email", "align": "left"},
        {"name": "phone", "label": "Phone", "field": "phone", "align": "left"},
        {"name": "skills", "label": "Skills", "field": "skills", "align": "left"},
        {"name": "is_shortlisted", "label": "Shortlisted", "field": "is_shortlisted", "align": "center"},
        {
            "name": "requirements",
            "label": "Compliance with Requirements",
            "field": "requirements",
            "align": "left",
        },
    ]

    # Add custom CSS for larger tooltip text
    ui.add_head_html("""
    <style>
        .custom-tooltip {
            font-size: 16px !important;
        }
    </style>
    """)

    # Reactive state for filters
    filters: Dict[str, List[str]] = {req_name: [] for req_name in req_names}

    # Filter function
    def apply_filters():
        filtered_rows = []
        for candidate in candidates:
            include = True
            for req_name, selected_statuses in filters.items():
                if selected_statuses:  # Only apply filter if statuses are selected
                    req_status = next(
                        (req["status"] for req in candidate["requirements"] if req["reqname"] == req_name),
                        None
                    )
                    if req_status is None or req_status not in selected_statuses:
                        include = False
                        break
            if include:
                filtered_rows.append({**candidate, "skills": ", ".join(candidate["skills"])})
        table.rows = filtered_rows
        table.update()

    # Create filter interface (rendered at the top of the UI)
    with ui.card().classes("w-full mb-4"):
        ui.label("Filter by Requirements").classes("text-lg font-bold")
        with ui.row().classes("flex flex-wrap gap-4"):
            for req_name in req_names:
                with ui.column():
                    ui.label(req_name).classes("text-sm")
                    ui.select(
                        ["YES", "NO", "MAYBE"],
                        multiple=True,
                        # label=f"{req_name}",
                        value=filters[req_name],
                        on_change=lambda e, rn=req_name: filters.update({rn: e.value}) or apply_filters()
                    ).classes("w-40")

    # Create table (rendered below the filter interface)
    table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")
    with table:
        table.add_slot(
            "body-cell-requirements",
            r'''
            <q-td :props="props">
                <div class="flex flex-wrap gap-1">
                    <q-icon
                        v-for="req in props.row.requirements"
                        :name="req.status === 'YES' ? 'check_circle' : req.status === 'NO' ? 'cancel' : 'help'"
                        :color="req.status === 'YES' ? 'green' : req.status === 'NO' ? 'red' : 'yellow'"
                        size="sm"
                        class="q-mr-xs"
                    >
                        <q-tooltip class="custom-tooltip">{{ req.status }} {{ req.reqname }}</q-tooltip>
                    </q-icon>
                </div>
            </q-td>
            '''
        )

