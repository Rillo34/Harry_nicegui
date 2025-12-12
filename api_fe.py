import nicegui
import json
import requests
import httpx
from nicegui import events, ui
from models import RequirementPayload, EvaluateResponse, ReSize, ReSizeResponse, ReEvaluateRequest, ReEvaluateResponse, CandidatesJobResponse
from models import CompanyProfile, CompanyJobFit, User, UsersPayload, NewSummary

    
# from models import J
from pydantic import parse_obj_as
import inspect


class APIController:
    def __init__(self, controller):
        self.controller = controller

    async def get_all_jobs(self):
        try:
            response = requests.get(
                'http://127.0.0.1:8080/get-jobs'
            )
            if response.status_code == 200:
                print(response)
                return response.json()
            else:
                print('Fel vid hämtning av jobb', response.status_code)
                return []  # returnera tom lista istället för False
        except Exception as e:
            print('Fel vid API-anrop:', e)
            return []
    
    async def get_datamodel_jobs(self):
        print("get_datamodel_jobs called from:", inspect.stack()[1].function)
        try:
            response = requests.get(
                'http://127.0.0.1:8080/get-job-states'
            )
            if response.status_code == 200:
                print("RESPONSE: ", response)
                return response.json()
            else:
                print('Fel vid hämtning av jobb', response.status_code)
                return []  # returnera tom lista istället för False
        except Exception as e:
            print('Fel vid API-anrop:', e)
            return []
    
    async def get_all_mails(self):
        print("in get all mails")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get('http://127.0.0.1:8080/get-mails')
            if response.status_code == 200:
                print(response)
                return response.json()
            else:
                print('Fel vid hämtning av jobb', response.status_code)
                return []
        except Exception as e:
            print('Fel vid API-anrop:', repr(e))
            return []
        
    
    async def requirement_matrix_eval(self):
        rm_uploaded = self.controller.uploaded_req_matrix or self.controller.uploaded_cvs_req_matrix
        print("in requirement_matrix_eval, rm_uploaded: ", rm_uploaded)
        if not rm_uploaded:
            ui.notify(f'You must upload Requirements matric', type='info')
        else:
            print("looking good")
            files_to_send = [
                ('cv_file', (
                    self.controller.uploaded_cvs_req_matrix.name,
                    self.controller.uploaded_cvs_req_matrix.content,
                    self.controller.uploaded_cvs_req_matrix.type
                )),
                ('kravmatris_file', (
                    self.controller.uploaded_req_matrix.name,
                    self.controller.uploaded_req_matrix.content,
                    self.controller.uploaded_req_matrix.type
                ))
            ]
            
            try:
                print("sending to backend kravmatris")
                response = requests.post(
                    'http://127.0.0.1:8080/kravmatris',  # byt till din riktiga BE-URL
                    files=files_to_send, # <-- Skickar alla filer i en enda dictionary
                )
                print("Responsens text: \n \n", response.text)
                if response.status_code != 200:
                    return False, f'Fel från backend: {response.status_code} - {response.text}'
                
                print("Raw response:", response)  
                return response 
                
            except Exception as e:
                return False, f'Ett fel uppstod: {e}'

    async def files_to_backend(self):
        files_uploaded = self.controller.uploaded_job_description or self.controller.uploaded_cvs

        if not files_uploaded:
            ui.notify(f'You must upload CVs and Job Description', type='info')
        else:
            print("requirements SOM SKICKAS TILL BE i send to backend: \n", self.controller.requirements)
            requirement_dicts = [r.dict() for r in self.controller.requirements]
            print("shortlist size: ”", self.controller.shortlist_size)
            files_to_send = [
                ('jd_file', (
                    self.controller.uploaded_job_description.name,
                    self.controller.uploaded_job_description.content,
                    self.controller.uploaded_job_description.type
                ))
            ]
            files_to_send.extend(self.controller.uploaded_cvs)
            data_to_send = {
                'shortlist_size': self.controller.shortlist_size,
                'requirements': json.dumps(requirement_dicts)
            }
            try:
                response = requests.post(
                    'http://127.0.0.1:8080/upload-files',  # byt till din riktiga BE-URL
                    files=files_to_send, # <-- Skickar alla filer i en enda dictionary
                    data=data_to_send
                )
                print("Responsens text: \n \n", response.text)
                if response.status_code != 200:
                    return False, f'Fel från backend: {response.status_code} - {response.text}'
                
                print("Raw response:", response)   
                response_data = EvaluateResponse(**response.json())
                new_requirements = response_data.updated_requirements
                
                self.controller.requirements = new_requirements
                self.controller.job_id = response_data.job.job_id
                self.controller.job_description = response_data.job.description
                self.controller.customer = response_data.job.customer
                self.controller.job_state = response_data.job.state
                self.controller.highest_candidate_status = response_data.job.highest_candidate_status
                self.controller.candidates = response_data.candidates
                
            except Exception as e:
                return False, f'Ett fel uppstod: {e}'
            
    
    async def api_resize(self):
        resize_payload = ReSize(
            job_id=self.controller.job_id,
            shortlist_size=self.controller.shortlist_size
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'http://127.0.0.1:8080/choose-shortlist-size',
                    json=resize_payload.dict()
                )

            if response.status_code == 200:
                resize_response = ReSizeResponse(**response.json())

                # Uppdatera controller med nya data
                self.controller.job_id = resize_response.job_id
                self.controller.shortlist_size = resize_response.shortlist_size
                self.controller.candidates = resize_response.candidates

                print("Resize lyckades")
                return resize_response
            else:
                ui.notify(f'Fel från backend: {response.status_code}', type='warning')
                return None

        except Exception as e:
            ui.notify(f'Nätverksfel: {e}', type='warning')
            return None
        
    async def api_reevaluate(self):
        reeval_payload = ReEvaluateRequest(
            job_id=self.controller.job_id,
            shortlist_size=self.controller.shortlist_size.value,
            requirements=self.controller.requirements
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'http://127.0.0.1:8080/re-evaluate',
                    json=reeval_payload.dict()
                )

            if response.status_code == 200:
                reeval_response = ReEvaluateResponse(**response.json())

                # Uppdatera controller med nya data
                self.controller.job_id = reeval_response.job_id
                self.controller.candidates = reeval_response.candidates

                print("Reeval lyckades")
                print(self.controller.candidates)
                return reeval_response
            else:
                ui.notify(f'Fel från backend: {response.status_code}', type='warning')
                return None

        except Exception as e:
            ui.notify(f'Nätverksfel: {e}', type='warning')
            return None
        
    async def api_get_candidates_job(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'http://127.0.0.1:8080/get-candidates-job',
                    params={"job_id": self.controller.job_id}
                )

            if response.status_code == 200:
                response = CandidatesJobResponse(**response.json())

                # Uppdatera controller med nya data
                self.controller.candidates = response.candidates
                self.controller.job_description = response.job.description
                self.controller.customer = response.job.customer
                self.controller.job_state = response.job.state
                self.controller.start_date = response.job.start_date
                self.controller.shortlist_size = response.job.shortlist_size
                self.controller.highest_candidate_status = response.job.highest_candidate_status 
                self.controller.requirements = response.job.requirements
                return response
            else:
                ui.notify(f'Fel från backend: {response.status_code}', type='warning')
                return None

        except Exception as e:
            ui.notify(f'Nätverksfel: {e}', type='warning')
            return None

    async def api_get_internal_candidates(self):
        print("in api_get_internal_candidates, controllerns job id: ", self.controller.job_id)
        print("---controllern 1 --")
        for attr, value in vars(self.controller).items():
            print(f"{attr}: {value}")        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'http://127.0.0.1:8080/evaluate-internal-candidates',
                    json={"job_id": self.controller.job_id}
                )
            if response.status_code == 200:
                response = ReEvaluateResponse(**response.json())

                # Uppdatera controller med nya data
                self.controller.candidates = response.candidates
                print("---controllern 2 --")
                for attr, value in vars(self.controller).items():
                    print(f"{attr}: {value}")
                return response
            else:
                ui.notify(f'Fel från backend: {response.status_code}', type='warning')
                return None

        except Exception as e:
        
            ui.notify(f'Nätverksfel: {e}', type='warning')
            print ("exception i api_get_internal_candidates: ", e)
            return None


    async def api_put_new_datamodel(self):
        print("in api_put new datamodel")
        payload = {
            "updated_statuses": self.controller.job_states_list,
            "name_mapping": self.controller.job_states_mapping_dict
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'http://127.0.0.1:8080/update-job-statuses',
                    json=payload
                )
            if response.status_code == 200:
                print("---ALL Good --")
            else:
                ui.notify(f'Fel från backend: {response.status_code}', type='warning')
                return None
        except Exception as e:
            ui.notify(f'Nätverksfel: {e}', type='warning')
            return None

    async def api_post_job_status_update(self):
        print("in api_put new job status")
        payload = {
            "job_id": self.controller.job_id,
            "status": self.controller.job_state
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'http://127.0.0.1:8080/update-job-status',
                    json=payload
                )
            if response.status_code == 200:
                print("---ALL Good updating job--")
            else:
                ui.notify(f'Fel från backend: {response.status_code}', type='warning')
                return None
        except Exception as e:
            ui.notify(f'Nätverksfel: {e}', type='warning')
            return None
    
    async def api_get_company_summary (self, company_id):
        print("in api_get_company_summary, company_id = ", company_id)
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"http://127.0.0.1:8080/company-profile?company_id={company_id}"
                )
                data = response.json()               # dict från BE
                company_profile = CompanyProfile(**data)  # mappa till din modell
                return company_profile

        except Exception as e:
            print("Fel vid anrop:", e)
            ui.notify(f'Nätverksfel: {e}', type='warning')
            return None

    async def match_company_to_jobs(self, company_id):
        print("in api_get_company_jobfit, company_id = ", company_id)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"http://127.0.0.1:8080/company-match-jobs?company_id={company_id}"
                )
                data = response.json()               # dict från BE
                print("data received from BE:", data)
                company_job_fits = [CompanyJobFit(**item) for item in data]                
                return company_job_fits
                
        except Exception as e:
            print("Fel vid anrop:", e)
            ui.notify(f'Nätverksfel: {e}', type='warning')
            return None

    async def get_users(self, company_id):
        print("in api_get_users, company_id = ", company_id)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"http://127.0.0.1:8080/get-company-users",
                    params={"company_id": company_id}
                )
                data = response.json()               # dict från BE
                print("data received from BE:", data)
                company_users = [User(**item) for item in data]                
                return company_users

        except Exception as e:
            print("Fel vid anrop:", e)
            ui.notify(f'Nätverksfel: {e}', type='warning')
            return None

    async def put_users(self, new_users):
        print("in api_put_users, company_id = ", self.controller.company_id)
        print("new users :", new_users)
        payload = {
            "new_users": new_users,
            "company_id": self.controller.company_id
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"http://127.0.0.1:8080/put-company-users",
                    json=payload 
                )
                data = response               # dict från BE
                print("data received from BE:", data)        
                return data
                
        except Exception as e:
            print("Fel vid anrop:", e)
            ui.notify(f'Nätverksfel: {e}', type='warning')
            return None
    
    async def put_new_summary(self, new_summary):
        print("in api_put_summary, company_id = ", self.controller.company_id)
        print("summary ", new_summary)
        payload = {
            "summary": new_summary,
            "company_id": self.controller.company_id
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"http://127.0.0.1:8080/put-new-summary",
                    json=payload 
                )
                data = response               # dict från BE
                print("data received from BE:", data)        
                return data
                
        except Exception as e:
            print("Fel vid anrop:", e)
            ui.notify(f'Nätverksfel: {e}', type='warning')
            return None



class UploadController:
    def __init__(self):
        self.job_id = ""
        self.job_description = ""
        self.uploaded_req_matrix = ""
        self.start_date = ""
        self.customer = ""
        self.requirements = []
        self.uploaded_job_description = None  # ska vara NiceGUI UploadedFile
        self.uploaded_cvs = []  # lista av UploadedFile
        self.uploaded_cvs_req_matrix = ""  # lista av UploadedFile för kravmatris, bara en fil nu
        self.shortlist_size = 3  # default
        self.candidates = []
        self.job_state = "NEW"
        self.job_states_list = []           # full dict of job states
        self.job_states_name_list = []      # list of job state names, to be used in other sections
        self.job_states_mapping_dict = {}  # mapping old states to new states
        self.candidate_states_list = []
        self.highest_candidate_status = ""
        self.company_id = ""
        self.company_name = ""
        self.company_summary = ""
        self.summary_exists=False
        self.company_industry =""
        self.matched_results = []
        self.user = ""

    def add_requirement(self, requirement_object):
        """Lägger till ett nytt krav i listan om det inte redan finns."""
        self.requirements.append(requirement_object)
        print (self.requirements)


    def clear_all_data(self):
        """Rensar all data som lagras i kontrollern."""
        self.requirements = []
        self.uploaded_job_description = None
        self.uploaded_cvs = []


    def send_to_backend(self):
        files_uploaded = self.uploaded_job_description or self.uploaded_cvs

        if not files_uploaded:
            ui.notify(f'You must upload CVs and Job Description', type='info')
        else:
            print("requirements SOM SKICKAS TILL BE i send to backend: \n", self.requirements)
            requirement_dicts = [r.dict() for r in self.requirements]
            print("shortlist size: ”", self.shortlist_size)
            files_to_send = [
                ('jd_file', (
                    self.uploaded_job_description.name,
                    self.uploaded_job_description.content,
                    self.uploaded_job_description.type
                ))
            ]
            
            files_to_send.extend(self.uploaded_cvs)
            data_to_send = {
                'shortlist_size': self.shortlist_size,
                'requirements': json.dumps(requirement_dicts)
            }
            try:
                response = requests.post(
                    'http://127.0.0.1:8080/upload-files',  # byt till din riktiga BE-URL
                    files=files_to_send, # <-- Skickar alla filer i en enda dictionary
                    data=data_to_send
                )
                print("Responsens text: \n \n", response.text)
                if response.status_code == 200:
                    return response
                else:
                    return False, f'Fel från backend: {response.status_code} - {response.text}'
            except Exception as e:
                return False, f'Ett fel uppstod: {e}'
            

    def re_evaluate(self):
        if not self.job_id or not self.requirements:
            return False, 'Job ID och krav måste vara satta innan re-evaluering.'
        try:
            payload = {
                'job_id': self.job_id,
                'shortlist_size': self.shortlist_size,
                'requirements': [r.dict() for r in self.requirements]
            }
            response = requests.post(
                'http://127.0.0.1:8080/re-evaluate',
                json=payload
            )

            if response.status_code == 200:
                return response
            else:
                return False, f'Fel från backend: {response.status_code} - {response.text}'

        except Exception as e:
            return False, f'Ett fel uppstod: {e}'    
         
    def re_size(self):
        if not self.job_id or not self.requirements:
            return False, 'Job ID och krav måste vara satta innan re-evaluering.'
        try:
            payload = {
                'job_id': self.job_id,
                'shortlist_size': self.shortlist_size,
            }
            response = requests.post(
                'http://127.0.0.1:8080/choose-shortlist-size',
                json=payload
            )

            if response.status_code == 200:
                return response
            else:
                return False, f'Fel från backend: {response.status_code} - {response.text}'

        except Exception as e:
            return False, f'Ett fel uppstod: {e}'        


