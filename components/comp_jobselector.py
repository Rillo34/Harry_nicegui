from nicegui import ui

class JobSelector:
    def __init__(self, jobs, on_select):
        self.on_select = on_select
        ui.select(
            options = {
                job["job_id"]: f'{job["title"]} ({job["customer"]})'
                for job in jobs
            },
            on_change=self._selected,
            label="Select job"
        )

    async def _selected(self, e):
        await self.on_select(e.value)
