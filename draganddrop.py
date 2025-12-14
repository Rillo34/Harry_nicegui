from __future__ import annotations

from typing import Callable, Protocol

from nicegui import ui


class Item(Protocol):
    title: str


dragged: card | None = None


class column(ui.column):

    def __init__(self, name: str, on_drop: Callable[[Item, str], None] | None = None) -> None:
        super().__init__()
        with self.classes('bg-blue-grey-2 w-90 p-4 rounded shadow-2'):
            ui.label(name).classes('text-bold ml-1')
        self.name = name
        self.on('dragover.prevent', self.highlight)
        self.on('dragleave', self.unhighlight)
        self.on('drop', self.move_card)
        self.on_drop = on_drop

    def highlight(self) -> None:
        self.classes(remove='bg-blue-grey-2', add='bg-blue-grey-3')

    def unhighlight(self) -> None:
        self.classes(remove='bg-blue-grey-3', add='bg-blue-grey-2')

    def move_card(self) -> None:
        global dragged  # pylint: disable=global-statement # noqa: PLW0603
        self.unhighlight()
        dragged.parent_slot.parent.remove(dragged)
        with self:
            card(dragged.item)
        self.on_drop(dragged.item, self.name)
        dragged = None


class card(ui.card):

    def __init__(self, item: Item, badge_text: str = "", extra_label: str = "") -> None:
        super().__init__()
        self.item = item
        with self.props('draggable').classes('w-full cursor-pointer bg-grey-1'):
            # huvudtitel
            ui.label(item.title).classes('text-bold')

            # badge (liten färgad etikett)
            if badge_text:
                ui.badge(badge_text).classes('ml-auto bg-blue text-white')

            # extra label som styrs av variabel
            if extra_label:
                ui.label(extra_label).classes('text-caption text-grey')

        self.on('dragstart', self.handle_dragstart)
        self.on('click', self.handle_click)


    def handle_dragstart(self) -> None:
        global dragged  # pylint: disable=global-statement # noqa: PLW0603
        dragged = self
    
    def handle_click(self) -> None:
        ui.notify(f'Card "{self.item.title}" clicked')