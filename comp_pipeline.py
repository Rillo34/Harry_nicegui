from nicegui import ui

# Dummydata
lanes = {
    "To Do": [f"Uppgift {i+1}" for i in range(5)],
    "In Progress": [f"Uppgift {i+6}" for i in range(5)],
    "Done": [f"Uppgift {i+11}" for i in range(5)],
}

# State
dragged_card = {'text': None, 'from_lane': None}
status_text = ui.label().classes('text-lg font-mono p-2 bg-gray-100 rounded-md w-full')


def update_status():
    """Visa var varje kort befinner sig."""
    text_lines = []
    for lane_name, cards in lanes.items():
        for card in cards:
            text_lines.append(f'{card} → {lane_name}')
    status_text.set_text("\n".join(text_lines))


def update_ui():
    """Uppdatera layouten."""
    board.clear()
    with board:
        for lane_name, cards in lanes.items():
            with ui.column().classes(
                'w-1/8 bg-white p-4 rounded-2xl min-h-[300px] shadow-md transition-all '
                'hover:shadow-xl border border-gray-200'
            ).on('dragover.prevent', lambda e, lane=lane_name: e) \
             .on('drop', lambda e, lane=lane_name: on_drop(lane)):

                ui.label(lane_name).classes('text-xl font-bold mb-4 text-gray-800')

                for card in cards:
                    ui.label(card).classes(
                        'bg-gradient-to-r from-indigo-500 to-blue-500 text-white '
                        'p-3 m-2 rounded-xl shadow-md cursor-grab hover:scale-105 '
                        'transition-transform'
                    ).props('draggable=true') \
                        .on('dragstart', lambda e, c=card, l=lane_name: on_drag_start(c, l))
    update_status()


def on_drag_start(card: str, lane: str):
    dragged_card['text'] = card
    dragged_card['from_lane'] = lane


def on_drop(to_lane: str):
    card = dragged_card['text']
    from_lane = dragged_card['from_lane']
    if card and from_lane and from_lane != to_lane:
        lanes[from_lane].remove(card)
        lanes[to_lane].append(card)
        update_ui()


ui.label('Kanban Board').classes('text-2xl font-bold mb-4')

# Statusruta överst
ui.label('Kortstatus:').classes('text-lg font-semibold mt-2 mb-1')
status_text.set_text('')

# Själva kanbanbrädet
with ui.row().classes('w-full gap-6') as board:
    pass

update_ui()

ui.run(port=8001)