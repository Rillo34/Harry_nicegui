import nicegui
from nicegui import ui

ui.add_css('''
.my-sticky-table
  /* height or max-height is important */
  height: 310px

  /* specifying max-width so the example can
    highlight the sticky column on any browser window */
  max-width: 600px

  td:first-child
    /* bg color is important for td; just specify one */
    background-color: #00b4ff

  tr th
    position: sticky
    /* higher than z-index for td below */
    z-index: 2
    /* bg color is important; just specify one */
    background: #00b4ff

  /* this will be the loading indicator */
  thead tr:last-child th
    /* height of all previous header rows */
    top: 48px
    /* highest z-index */
    z-index: 3
  thead tr:first-child th
    top: 0
    z-index: 1
  tr:first-child th:first-child
    /* highest z-index */
    z-index: 3

  td:first-child
    z-index: 1

  td:first-child, th:first-child
    position: sticky
    left: 0

  /* prevent scrolling behind sticky top row on focus */
  tbody
    /* height of all previous header rows */
    scroll-margin-top: 48px
''')

columns = [
    {'name': 'name', 'label': 'Name', 'field': 'name', 'align': 'left'},
    {'name': 'age', 'label': 'Age', 'field': 'age'},
    {'name': 'gender', 'label': 'Gender', 'field': 'gender'},
]
rows = [
    {'name': 'Alice', 'age': 18, 'gender': 'female'},
    {'name': 'Bob', 'age': 21, 'gender': 'male'},
    {'name': 'Carol', 'age': 42, 'gender': 'female'},
    {'name': 'Dave', 'age': 33, 'gender': 'male'},
]
ui.table(columns=columns, rows=rows, row_key='name').classes('my-sticky-table w-40 h-40')