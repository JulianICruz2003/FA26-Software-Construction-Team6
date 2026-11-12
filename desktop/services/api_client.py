
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv


class ApiClient:
    def __init__(self):
        # Load configuration from the project root
        env_path = Path(__file__).resolve().parents[2] / ".env"
        load_dotenv(env_path)

        self.base_url = os.getenv(
            "API_BASE_URL",
            "http://127.0.0.1:8000"
        ).rstrip("/")

    def _check_endpoint(self, endpoint):
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(
                    f"{self.base_url}{endpoint}"
                )
                response.raise_for_status()

            return True

        except httpx.HTTPError as exc:
            print(
                f"Connection check failed: {exc}",
                file=sys.stderr
            )
            return False

    def check_api(self):
        return self._check_endpoint("/health")

    def check_database(self):
        return self._check_endpoint("/health/db")


    def get_projects(self):
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                f"{self.base_url}/projects"
            )
            response.raise_for_status()
            return response.json()

    def create_project(self, name, description):
        with httpx.Client(timeout=5.0) as client:
            response = client.post(
                f"{self.base_url}/projects",
                json={
                    "name": name,
                    "description": description
                }
            )
            response.raise_for_status()
            return response.json()
        
    
    def get_tasks(self, project_id):
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                f"{self.base_url}/projects/{project_id}/tasks"
            )
            response.raise_for_status()
            return response.json()

    def create_task(self, project_id, title):
        with httpx.Client(timeout=5.0) as client:
            response = client.post(
                f"{self.base_url}/projects/{project_id}/tasks",
                json={"title": title}
            )
            response.raise_for_status()
            return response.json()

    def update_task(self, project_id, task_id, is_complete):
        with httpx.Client(timeout=5.0) as client:
            response = client.patch(
                f"{self.base_url}/projects/{project_id}/tasks/{task_id}",
                json={"is_complete": is_complete}
            )
            response.raise_for_status()
            return response.json()

    def get_users(self):
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                f"{self.base_url}/users"
            )
            response.raise_for_status()
            return response.json()

    def get_team_members(self, project_id):
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                f"{self.base_url}/projects/{project_id}/members"
            )
            response.raise_for_status()
            return response.json()

    def add_team_member(self, project_id, user_id, project_role):
        with httpx.Client(timeout=5.0) as client:
            response = client.post(
                f"{self.base_url}/projects/{project_id}/members",
                json={
                    "user_id": user_id,
                    "project_role": project_role
                }
            )
            response.raise_for_status()
            return response.json()

    def remove_team_member(self, project_id, membership_id):
        with httpx.Client(timeout=5.0) as client:
            response = client.delete(
                f"{self.base_url}/projects/{project_id}/members/{membership_id}"
            )
            response.raise_for_status()

    def create_user(self, name, email, account_role):
        with httpx.Client(timeout=5.0) as client:
            response = client.post(
                f"{self.base_url}/users",
                json={
                    "name": name,
                    "email": email,
                    "account_role": account_role
                }
            )
            response.raise_for_status()
            return response.json()
