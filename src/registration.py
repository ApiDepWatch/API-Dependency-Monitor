import os
import requests as http_requests


class Registration:
    def __init__(self, org_id: int, project_name: str, org_name: str, user_id: int, username: str):
        self.backend_url = os.getenv("BACKEND_URL")
        self.org_id = org_id
        self.project_name = project_name
        self.org_name = org_name
        self.user_id = user_id
        self.username = username
        self.spec_path = os.getenv("PATH_TO_API_SPEC")


    def registar_repository(self):
        if not self.spec_path:
            print("Registering consumer repository with backend...")
            self.registar_consumer_repository_with_backend()
        else:
            print("Registering provider repository with backend...")
            self.registar_provider_repository_with_backend()

    def registar_provider_repository_with_backend(self):
        try:
            specfile = ""
            with open(self.spec_path) as f:
                specfile = f.read()
            params = {
                "orgId": self.org_id,
                "projectName": self.project_name,
                "orgName": self.org_name,
                "userId": self.user_id,
                "userName": self.username,
                "hostName": os.getenv("HOST_NAME")
            }
            print(f"::warning::hostname={os.getenv("HOST_NAME")}")
            
            response = http_requests.post(
                f"{self.backend_url}/RegisterProvider",
                params=params,
                headers={"Content-Type": "application/json"},
                data=specfile
            )
            print(f"::warning::RegisterProvider response: status={response.status_code} body={response.text}")
        except Exception as e:
            print(f"::warning::Error occurred while registering provider repository with backend: {e}")

    def registar_consumer_repository_with_backend(self):
        try:
            params={
                "orgId": self.org_id, 
                "projectName": self.project_name, 
                "orgName": self.org_name, 
                "userId": self.user_id, 
                "userName": self.username
            }

            response = http_requests.post(
                f"{self.backend_url}/RegisterConsumer",
                params=params,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                print(response.text)
            else:
                print(f"::warning::Failed to register consumer repository with backend. Status code: {response.status_code}")
        except Exception as e:
            print(f"::warning::Error occurred while registering consumer repository with backend: {e}")
    
