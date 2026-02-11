import nicegui
import json
import requests
import httpx
from nicegui import events, ui
from backend.models import RequirementPayload, EvaluateResponse, ReSize, ReSizeResponse, ReEvaluateRequest, ReEvaluateResponse, CandidatesJobResponse
from backend.models import CompanyProfile, CompanyJobFit, User, ContractAllocationChangeRequest, NewSummary, JobStatusUpdateRequest, ContractAllocationMonthRequest
from backend.models import ContractAllocationRequest

class APIController:
    BASE = "http://127.0.0.1:8080"

    def __init__(self, controller):
        self.controller = controller

    async def _request(self, method, endpoint, *, params=None, json=None, files=None, timeout=30):
        url = f"{self.BASE}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    files=files,
                )

            if response.status_code == 200:
                return response.json()
            else:
                ui.notify(f'Backend error {response.status_code}', type='warning')
                return None

        except Exception as e:
            ui.notify(f'Nätverksfel: {e}', type='warning')
            return None

    def _parse_list(self, data, model):
        return [model(**item) for item in data] if data else []

    # -----------------------------
    # JOBS
    # -----------------------------

    async def get_all_jobs(self):
        return await self._request("GET", "/get-jobs")

    async def get_datamodel_jobs(self):
        return await self._request("GET", "/get-job-states")

    async def get_all_mails(self):
        return await self._request("GET", "/get-mails", timeout=60)
    
    async def job_status_update(self, job_id, status):
        payload = JobStatusUpdateRequest(
            job_id=job_id,
            status=status
        )
        return await self._request("POST", "/update-job-status", json=payload.dict())

    async def get_jobs_from_directory(self):
        return await self._request("GET", "/get-new-jobs-from-directory", timeout=60)
    
    # -----------------------------
    # CONTRACTS AND ALLOCATIONS
    # -----------------------------

    async def get_contracts_table(self):
        return await self._request("GET", "/get-contracts-table")

    async def get_all_allocations(self):
        return await self._request("GET", "/get-allocations-table")
    
    async def get_allocations_perc_and_hours(self):
        return await self._request("GET", "/get-allocations-table-perc-and-hours")
    
    async def get_working_hours(self):
        return await self._request("GET", "/get-workinghour-table")
    
    async def delete_allocation(self, allocation_list):
        print("API   delete_allocation, allocation_list:", allocation_list)
        payload = [
            ContractAllocationRequest(
                contract_id=item["contract_id"],
                candidate_id=item["candidate_id"],
                change=None
            ).dict()
            for item in allocation_list
        ]
        print("Payload for delete_allocation:", payload)
        return await self._request("POST", "/delete-allocation", json=payload)
    
    async def change_allocation(self, change_list):
        payload = [
            ContractAllocationChangeRequest(
                contract_id=item["contract_id"],
                candidate_id=item["candidate_id"],
                change=item["change"]
            ).dict()
            for item in change_list
        ]
        return await self._request("PATCH", "/change-allocation", json=payload)
    
    async def change_cell_alloc(self, change_list):
        payload = [
            ContractAllocationMonthRequest(
                contract_id=item["contract_id"],
                candidate_id=item["candidate_id"],
                month=item["month"],
                new_value=item["new_value"]
            ).dict()
            for item in change_list
        ]
        return await self._request("PATCH", "/change-cell-allocation", json=payload)

    async def add_allocation_to_contract(self, allocation_list):
        print("API add_allocation_to_contract_allocation, allocation_list:", allocation_list)

        payload = [
            ContractAllocationRequest(
                contract_id=allocation_list["contract_id"],
                candidate_id=candidate_id,
                allocation_percent=allocation_list["allocation_percent"]
            ).dict()
            for candidate_id in allocation_list["candidate_ids"]
        ]

        print("Payload for add_allocation_to_contract_allocation:", payload)
        return await self._request("POST", "/add-allocation", json=payload)

    # -----------------------------
    # AVAILABILITY
    # -----------------------------

    async def get_availability(self, contract_id):
        return await self._request(
            "GET",
            "/availability-against-job",
            params={"contract_id": contract_id}
        )

    async def get_availability_job_contract(self, is_contract, contract_id, candidate_ids):
        payload= { 
            "is_contract": is_contract,
            "contract_id": contract_id, 
            "candidate_ids": candidate_ids } 
        return await self._request( "POST", "/availability-against-job-or-contract", json=payload)

    # -----------------------------
    # FILE UPLOAD / EVALUATION
    # -----------------------------

    async def files_to_backend(self):
        if not (self.controller.uploaded_job_description or self.controller.uploaded_cvs):
            ui.notify("You must upload CVs and Job Description", type="info")
            return None

        files_to_send = [
            ('jd_file', (
                self.controller.uploaded_job_description.name,
                self.controller.uploaded_job_description.content,
                self.controller.uploaded_job_description.type
            ))
        ]
        files_to_send.extend(self.controller.uploaded_cvs)

        requirement_dicts = [r.dict() for r in self.controller.requirements]

        data = await self._request(
            "POST",
            "/upload-files",
            files=files_to_send,
            json={
                "shortlist_size": self.controller.shortlist_size,
                "requirements": requirement_dicts,
            }
        )

        if not data:
            return None

        response = EvaluateResponse(**data)
        self.controller.job_id = response.job.job_id
        self.controller.job_description = response.job.description
        self.controller.customer = response.job.customer
        self.controller.job_state = response.job.state
        self.controller.highest_candidate_status = response.job.highest_candidate_status
        self.controller.candidates = response.candidates
        self.controller.requirements = response.updated_requirements

        return response

    # -----------------------------
    # RESIZE / REEVALUATE
    # -----------------------------

    async def api_resize(self):
        payload = ReSize(
            job_id=self.controller.job_id,
            shortlist_size=self.controller.shortlist_size
        )
        data = await self._request("POST", "/choose-shortlist-size", json=payload.dict())
        return ReSizeResponse(**data) if data else None

    async def api_reevaluate(self):
        payload = ReEvaluateRequest(
            job_id=self.controller.job_id,
            shortlist_size=self.controller.shortlist_size,
            requirements=self.controller.requirements
        )
        data = await self._request("POST", "/re-evaluate", json=payload.dict())
        return ReEvaluateResponse(**data) if data else None

    # -----------------------------
    # CANDIDATES
    # -----------------------------

    async def api_get_candidates_job(self):
        data = await self._request(
            "GET",
            "/get-candidates-job",
            params={"job_id": self.controller.job_id}
        )
        return CandidatesJobResponse(**data) if data else None

    async def api_get_internal_candidates(self):
        data = await self._request(
            "POST",
            "/evaluate-internal-candidates",
            json={"job_id": self.controller.job_id}
        )
        return ReEvaluateResponse(**data) if data else None
    
    async def get_all_candidates(self):
        data = await self._request("GET", "/get-all-candidates")
        print(data)
        return data

    # -----------------------------
    # COMPANY
    # -----------------------------

    async def api_get_company_summary(self, company_id):
        data = await self._request("GET", "/company-profile", params={"company_id": company_id})
        return CompanyProfile(**data) if data else None

    async def match_company_to_jobs(self, company_id):
        data = await self._request("GET", "/company-match-jobs", params={"company_id": company_id})
        return self._parse_list(data, CompanyJobFit)

    async def get_users(self, company_id):
        data = await self._request("GET", "/get-company-users", params={"company_id": company_id})
        return self._parse_list(data, User)

    async def put_users(self, new_users):
        payload = {"new_users": new_users, "company_id": self.controller.company_id}
        return await self._request("PUT", "/put-company-users", json=payload)

    async def put_new_summary(self, new_summary):
        payload = {"summary": new_summary, "company_id": self.controller.company_id}
        return await self._request("PUT", "/put-new-summary", json=payload)

    # -----------------------------
    # --- END
    # -----------------------------


class UploadController:
    def __init__(self):
        # Job-related state
        self.job_id: str = ""
        self.job_description: str = ""
        self.customer: str = ""
        self.start_date: str = ""
        self.job_state: str = "NEW"
        self.highest_candidate_status: str = ""

        # Requirements
        self.requirements: list = []

        # Uploaded files
        self.uploaded_job_description = None      # NiceGUI UploadedFile
        self.uploaded_cvs: list = []             # List[UploadedFile]
        self.uploaded_req_matrix = None          # UploadedFile
        self.uploaded_cvs_req_matrix = None      # UploadedFile

        # Candidates
        self.candidates: list = []
        self.shortlist_size: int = 3

        # Job state model
        self.job_states_list: list = []
        self.job_states_name_list: list = []
        self.job_states_mapping_dict: dict = {}

        # Company
        self.company_id: str = ""
        self.company_name: str = ""
        self.company_industry: str = ""
        self.company_summary: str = ""
        self.summary_exists: bool = False
        self.matched_results: list = []

        # User
        self.user: str = ""

    # -----------------------------
    # Helpers for frontend logic
    # -----------------------------

    def set_job_states(self, states): 
        self.job_states_list = states
        self.job_states_name_list = [s["name"] for s in states] 
        self.job_states_mapping_dict = {s["id"]: s["name"] for s in states}

    def add_requirement(self, requirement):
        """Add a requirement object to the list."""
        self.requirements.append(requirement)

    def clear_requirements(self):
        self.requirements = []

    def clear_uploaded_files(self):
        self.uploaded_job_description = None
        self.uploaded_cvs = []
        self.uploaded_req_matrix = None
        self.uploaded_cvs_req_matrix = None

    def clear_candidates(self):
        self.candidates = []

    def clear_all(self):
        """Reset all state (used for debugging or logout)."""
        self.__init__()
