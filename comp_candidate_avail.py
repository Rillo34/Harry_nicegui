import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
import numpy as np

# ---------- Dummydata ----------
consultants = ["Alice", "Bob", "Charlie", "Diana", "Eric"]
projects = ["Project A", "Project B", "Project C", "Project D", "Project E"]
colors = plt.cm.Set3(np.linspace(0, 1, len(projects)))

# Tidsaxel (exempel: 1 okt – 30 nov)
start_date = dt.date(2025, 10, 1)
end_date = dt.date(2025, 11, 30)

# Skapa lite slumpmässig men snygg dummy-allokering över tid
np.random.seed(2)
allocations = []
for i, name in enumerate(consultants):
    base = start_date
    for _ in range(3):  # varje konsult har ca 3 projekt under perioden
        dur = np.random.randint(10, 25)
        proj_start = base + dt.timedelta(days=np.random.randint(0, 20))
        proj_end = proj_start + dt.timedelta(days=dur)
        project = np.random.choice(projects)
        percent = np.random.choice([25, 50, 75, 100])
        allocations.append({
            "consultant": name,
            "project": project,
            "start": proj_start,
            "end": proj_end,
            "percent": percent
        })

# ---------- Rita diagram ----------
fig, ax = plt.subplots(figsize=(12, 6))

y_positions = np.arange(len(consultants)) * 10  # avstånd mellan konsulter

for i, name in enumerate(consultants):
    person_allocs = [a for a in allocations if a["consultant"] == name]
    for alloc in person_allocs:
        start = mdates.date2num(alloc["start"])
        end = mdates.date2num(alloc["end"])
        width = end - start
        color = colors[projects.index(alloc["project"])]
        
        ax.barh(
            y_positions[i],
            width,
            left=start,
            height=4,
            color=color,
            edgecolor='white',
            alpha=0.9,
        )
        # procenttext mitt på stapeln
        ax.text(
            start + width / 2,
            y_positions[i],
            f"{alloc['percent']}%",
            ha='center',
            va='center',
            fontsize=9,
            color='black',
            fontweight='bold',
        )

# ---------- Format & layout ----------
ax.set_yticks(y_positions)
ax.set_yticklabels(consultants)
ax.invert_yaxis()  # topp = första konsult
ax.set_xlabel("Date")
ax.set_title("Consultant Allocation Timeline", fontsize=15, pad=15)

# Datumformattering på x-axeln
ax.xaxis_date()
ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))

# Legend
handles = [plt.Rectangle((0, 0), 1, 1, color=colors[i]) for i in range(len(projects))]
ax.legend(handles, projects, title="Projects", bbox_to_anchor=(1.05, 1), loc="upper left")

# Rutnät, layout, styling
ax.grid(axis='x', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
