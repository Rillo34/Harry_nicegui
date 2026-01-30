from nicegui import ui

# Pages
from niceGUI.pages.page_home import home_page
from niceGUI.pages.page_candidatejobs import candidate_jobs_page
from niceGUI.pages.page_jobs import jobs_page
from niceGUI.pages.page_allocations import allocations_page
from niceGUI.pages.page_datavalidation import datavalidation_page
# from niceGUI.pages.page_adminpanel import admin_panel_page
# from niceGUI.pages.page_jobs_automate import jobs_automate_page
# from niceGUI.pages.page_datamodel import datamodel_page
# from niceGUI.pages.page_reqmatrix import reqmatrix_page
# from niceGUI.pages.page_companyjobfit import company_jobfit_page


# Start app
ui.run(port=8007, reload=True)
