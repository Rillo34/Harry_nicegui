from nicegui import ui

class JobSelector:
    def __init__(self, job_list, on_select):
        print("jobs in select")
        options_list = {
            job["job_id"]: job["text"]
            for job in job_list
        }
        self.on_select = on_select
        ui.select(
            options = options_list,
            on_change=self._selected,
            with_input=True,
            label="Select job to evaluate"
        )

    async def _selected(self, e):
        print("e: ", e)
        await self.on_select(e.value)
