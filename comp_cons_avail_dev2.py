from nicegui_tabulator import tabulator
from nicegui import ui

tabledata = [
    {"id": 1, "name": "Oli Bob", "age": "12", "col": "red", "dob": ""},
    {"id": 2, "name": "Mary May", "age": "1", "col": "blue", "dob": "14/05/1982"},
    {
        "id": 3,
        "name": "Christine Lobowski",
        "age": "42",
        "col": "green",
        "dob": "22/05/1982",
    },
    {
        "id": 4,
        "name": "Brendon Philips",
        "age": "125",
        "col": "orange",
        "dob": "01/08/1980",
    },
    {
        "id": 5,
        "name": "Margret Marmajuke",
        "age": "16",
        "col": "yellow",
        "dob": "31/01/1999",
    },
]

table_config = {
    "height": 205,  
    "data": tabledata, 
    "columns": [  
        {"title": "Name", "field": "name", "width": 150, "headerFilter": "input"},
        {"title": "Age", "field": "age", "hozAlign": "left", "formatter": "progress"},
        {"title": "Favourite Color", "field": "col"},
        {
            "title": "Date Of Birth",
            "field": "dob",
            "sorter": "date",
            "hozAlign": "center",
        },
    ],
}

table = tabulator(table_config).on_event("rowClick", lambda e: ui.notify(e))


def on_sort():
    table.run_table_method(
        "setSort",
        [
            {"column": "name", "dir": "desc"},
            {"column": "age", "dir": "asc"},
        ],
    )


ui.button("sort", on_click=on_sort)
ui.run()