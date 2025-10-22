import nicegui
import json
import requests
import httpx
from nicegui import events, ui
from models import RequirementPayload, EvaluateResponse, ReSize, ReSizeResponse, ReEvaluateRequest, ReEvaluateResponse, CandidatesJobResponse
from pydantic import parse_obj_as


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
    
    async def get_all_mails(self):
        try:
            response = requests.get(
                'http://127.0.0.1:8080/get-mails'
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
        

class UploadController:
    def __init__(self):
        self.job_id = ""
        self.job_description = ""
        self.start_date = ""
        self.customer = ""
        self.requirements = []
        self.uploaded_job_description = None  # ska vara NiceGUI UploadedFile
        self.uploaded_cvs = []  # lista av UploadedFile
        self.shortlist_size = 3  # default
        self.candidates = []
        self.job_state = "Open"
        self.highest_candidate_status = ""

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