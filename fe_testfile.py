
def get_jobrequest():
    jobs = [
    {
        "job_id": "job_1",
        "title": "Frontend Developer",
        "description": "Develop UI components using React.",
        "customer": "Acme Inc",
        "contact_person": "Alice",
        "start_date": "2025-11-30",
        "duration": "permanent",
        "due_date": "2025-10-20",
        "requirements": [
            {"reqname": "TypeScript", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Kubernetes", "isActive": True, "ismusthave": False, "source": "JD"},
            {"reqname": "Docker", "isActive": True, "ismusthave": False, "source": "USER"}
        ],
        "state": "1-Open",
        "candidates": 4,
        "shortlist_size": 5,
        "highest_candidate_status": "5 - Contracted",
        "assigned_to": "admin",
        "created_at": "2025-10-22T17:35:27.257619"
    },
    {
        "job_id": "job_2",
        "title": "Backend Engineer",
        "description": "Build backend services with Python.",
        "customer": "Acme Inc",
        "contact_person": "Bob",
        "start_date": "2025-11-09",
        "duration": "6 months",
        "due_date": "2025-10-19",
        "requirements": [
            {"reqname": "TypeScript", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "SQL", "isActive": True, "ismusthave": False, "source": "JD"},
            {"reqname": "Docker", "isActive": True, "ismusthave": True, "source": "USER"},
            {"reqname": "AWS", "isActive": True, "ismusthave": False, "source": "JD"}
        ],
        "state": "1-Open",
        "candidates": 4,
        "shortlist_size": 1,
        "highest_candidate_status": "4 - Submitted",
        "assigned_to": "recruiter1",
        "created_at": "2025-10-22T17:35:27.257979"
    },
    {
        "job_id": "job_3",
        "title": "Data Analyst",
        "description": "Analyze data and generate insights.",
        "customer": "Acme Inc",
        "contact_person": "Charlie",
        "start_date": "2025-11-16",
        "duration": "6 months",
        "due_date": "2025-10-19",
        "requirements": [
            {"reqname": "Docker", "isActive": True, "ismusthave": False, "source": "JD"},
            {"reqname": "TypeScript", "isActive": True, "ismusthave": False, "source": "JD"},
            {"reqname": "Kubernetes", "isActive": True, "ismusthave": False, "source": "USER"},
            {"reqname": "TypeScript", "isActive": True, "ismusthave": False, "source": "USER"},
            {"reqname": "TypeScript", "isActive": True, "ismusthave": False, "source": "USER"}
        ],
        "state": "Cancelled",
        "candidates": 4,
        "shortlist_size": 5,
        "highest_candidate_status": "4 - Submitted",
        "assigned_to": "admin",
        "created_at": "2025-10-22T17:35:27.258241"
    },
    {
        "job_id": "job_4",
        "title": "DevOps Specialist",
        "description": "Manage infrastructure and CI/CD.",
        "customer": "Acme Inc",
        "contact_person": "Diana",
        "start_date": "2025-11-12",
        "duration": "permanent",
        "due_date": "2025-10-16",
        "requirements": [
            {"reqname": "SQL", "isActive": True, "ismusthave": False, "source": "JD"},
            {"reqname": "React", "isActive": True, "ismusthave": False, "source": "USER"}
        ],
        "state": "1-Open",
        "candidates": 4,
        "shortlist_size": 5,
        "highest_candidate_status": "4 - Submitted",
        "assigned_to": "recruiter2",
        "created_at": "2025-10-22T17:35:27.258506"
    },
    {
        "job_id": "job_5",
        "title": "Product Manager",
        "description": "Define product strategy and roadmap.",
        "customer": "Acme Inc",
        "contact_person": "Ethan",
        "start_date": "2025-11-29",
        "duration": "contract",
        "due_date": "2025-11-03",
        "requirements": [
            {"reqname": "Python", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "SQL", "isActive": True, "ismusthave": True, "source": "USER"},
            {"reqname": "React", "isActive": True, "ismusthave": False, "source": "USER"}
        ],
        "state": "2-In Progress",
        "candidates": 4,
        "shortlist_size": 1,
        "highest_candidate_status": "5 - Contracted",
        "assigned_to": "recruiter1",
        "created_at": "2025-10-22T17:35:27.258769"
    },
    {
        "job_id": "abde1",
        "title": "Data Engineer",
        "description": "Data Engineer to build data products in Data Mesh concept on GCP.",
        "customer": "H&M",
        "contact_person": "Sofie Bergbom <Sofie.Bergbom@nexergroup.com>",
        "start_date": "2025-06-23",
        "duration": "2026-06-30",
        "due_date": None,
        "requirements": [
            {"reqname": "4+ years Data Engineer on GCP", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Experience in cloud technologies and infrastructure", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Experience in GCP tools (Bigquery, Pubsub)", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Experience in data query languages (SQL)", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Experience in data centric programming (Python)", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Required cloud certification: GCP", "isActive": True, "ismusthave": True, "source": "JD"}
        ],
        "state": "Okänd",
        "candidates": 0,
        "shortlist_size": None,
        "highest_candidate_status": "Ingen status",
        "assigned_to": "",
        "created_at": "2025-10-22T17:35:50.141974"
    },
    {
        "job_id": "f5238",
        "title": "Requirements Analyst for Next Generation Retail Program",
        "description": "Analyze business needs for new warehouse management system development at Apotek Hjärtat.",
        "customer": "Apotek Hjärtat AB",
        "contact_person": "Konsultinkop@ica.se",
        "start_date": "2025-06-02",
        "duration": "2025-12-31",
        "due_date": None,
        "requirements": [
            {"reqname": "Experience with IT and system implementation", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "High problem-solving ability and accuracy", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Experience working with IT vendors", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Good analytical ability and understanding of logistics", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Five years experience as requirements analyst", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Experience in retail or pharmacy operations", "isActive": True, "ismusthave": False, "source": "JD"}
        ],
        "state": "Okänd",
        "candidates": 0,
        "shortlist_size": None,
        "highest_candidate_status": "Ingen status",
        "assigned_to": "",
        "created_at": "2025-10-22T17:35:50.153680"
    },
    {
        "job_id": "8aab9",
        "title": "IT Specialist in IT Monitoring",
        "description": "IT Specialist for managing central IT monitoring platforms with focus on observability.",
        "customer": "Svenska kraftnät",
        "contact_person": "svk@magnitglobal.com",
        "start_date": "2025-08-31",
        "duration": "1 year",
        "due_date": None,
        "requirements": [
            {"reqname": "Experience in IT monitoring platforms", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Experience with Observatorium.io (thanos, grafana, loki)", "isActive": True, "ismusthave": False, "source": "JD"},
            {"reqname": "Experience in handling incidents and problems", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Experience providing general IT support", "isActive": True, "ismusthave": False, "source": "JD"},
            {"reqname": "Experience in IT security", "isActive": True, "ismusthave": True, "source": "JD"},
            {"reqname": "Experience with system documentation", "isActive": True, "ismusthave": True, "source": "JD"}
        ],
        "state": "Okänd",
        "candidates": 0,
        "shortlist_size": None,
        "highest_candidate_status": "Ingen status",
        "assigned_to": "",
        "created_at": "2025-10-22T17:35:50.158167"
    }
    ]

    return jobs


