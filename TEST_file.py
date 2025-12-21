from nicegui import ui

# =========================
# DATA (enda källan)
# =========================
scores = {
    ('Job Asakfjdaskjbdaksndlaksnda', 'Cand 1'): 90,
    ('Job Asakfjdaskjbdaksndlaksnda', 'Cand 2'): 65,
    ('Job Asakfjdaskjbdaksndlaksnda', 'Cand 3'): 30,
    ('Job Asakfjdaskjbdaksndlaksnda', 'Cand 4'): 75,
    ('Job B', 'Cand 1'): 55,
    ('Job B', 'Cand 2'): 85,
    ('Job B', 'Cand 3'): 40,
    ('Job B', 'Cand 4'): 60,
    ('Job C', 'Cand 1'): 20,
    ('Job C', 'Cand 2'): 45,
    ('Job C', 'Cand 3'): 70,
    ('Job C', 'Cand 4'): 95,
    ('Job D', 'Cand 1'): 88,
    ('Job D', 'Cand 2'): 52,
    ('Job D', 'Cand 3'): 66,
    ('Job D', 'Cand 4'): 10,
}

# =========================
# CSS (endast för rotation)
# =========================
# ui.add_head_html('''
# <style>
# .rotate-45 {
#     transform: rotate(-45deg);
#     transform-origin: bottom left;
#     white-space: nowrap;
# }
# </style>
# ''')

ui.add_head_html('''
<style>
.wrap-text {
    white-space: normal !important;
    word-break: break-word;
    max-width: 80px;        /* justera */
    text-align: center;
}
</style>
''')

# =========================
# FÄRGLOGIK
# =========================
def score_color(score: int) -> str:
    if score >= 80:
        return 'green-2'
    elif score >= 50:
        return 'yellow-2'
    return 'red-2'


# =========================
# UI – ALLT HÄR
# =========================
with ui.card().classes('w-full p-4'):
    ui.label('Job × Candidate Match Grid').classes('text-xl font-bold mb-4')

    # Dimensioner direkt från dicten
    jobs = sorted({job for job, _ in scores})
    candidates = sorted({cand for _, cand in scores})
    cols = len(jobs) + 1

    # Header
    with ui.grid(columns=cols).classes('gap-2'):
        # header
        ui.label('Candidate').classes('font-bold')
        for job in jobs:
            ui.label(job).classes('wrap-text text-sm')   

        # body
        for cand in candidates:
            ui.label(cand).classes('font-bold')
            for job in jobs:
                score = scores.get((job, cand), 0)
                color = score_color(score)
                card = ui.card().classes(f'p-2 text-center bg-{color} cursor-pointer')
                with card:
                    ui.label(f'{score}%').classes('text-lg font-bold')
                card.on('click', lambda e, c=cand, j=job, s=score: ui.notify(f'{c} vs {j}: {s}%'))



# =========================
# RUN
# =========================
ui.run(port=8007)
