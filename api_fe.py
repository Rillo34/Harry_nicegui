import nicegui
import json
import requests
from nicegui import events, ui
# from models import RequirementPayload, EvaluateResponse
from pydantic import parse_obj_as


class APIController:
    def get_all_jobs(self):
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


class UploadController:
    def __init__(self):
        self.job_id = ""
        self.job_description = ""
        self.customer = ""
        self.requirements = []
        self.uploaded_job_description = None  # ska vara NiceGUI UploadedFile
        self.uploaded_cvs = []  # lista av UploadedFile
        self.shortlist_size = 3  # default

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