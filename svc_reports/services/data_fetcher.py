from typing import Dict, List, Optional
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from core.config import settings


class DataFetcherService:
    """
    Service for fetching data from svc_defects and svc_projects via HTTP.
    """

    def __init__(self, token: str):
        """
        Initialize with JWT token for authentication.

        Args:
            token: JWT bearer token for inter-service calls
        """
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
        self.timeout = 10.0  # 10 seconds timeout

    async def fetch_defects(
        self,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        author_id: Optional[UUID] = None,
        assignee_id: Optional[UUID] = None,
    ) -> List[Dict]:
        """
        Fetch defects from svc_defects with optional filters.

        Returns:
            List of defect dictionaries

        Raises:
            HTTPException 503: If svc_defects is unavailable
        """
        try:
            params = {"limit": 10000}  # Large limit to get all defects

            if project_id:
                params["project_id"] = str(project_id)
            if status:
                params["status"] = status
            if priority:
                params["priority"] = priority
            if author_id:
                params["author_id"] = str(author_id)
            if assignee_id:
                params["assignee_id"] = str(assignee_id)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{settings.DEFECTS_SERVICE_URL}/api/v1/defects",
                    headers=self.headers,
                    params=params,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
                else:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Defects service error: {response.status_code}",
                    )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Defects service timeout",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Defects service unavailable: {str(e)}",
            )

    async def fetch_project(self, project_id: UUID) -> Optional[Dict]:
        """
        Fetch single project by ID from svc_projects.

        Returns:
            Project dictionary or None if not found

        Raises:
            HTTPException 503: If svc_projects is unavailable
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{settings.PROJECTS_SERVICE_URL}/api/v1/projects/{project_id}",
                    headers=self.headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data")
                elif response.status_code == 404:
                    return None
                else:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Projects service error: {response.status_code}",
                    )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Projects service timeout",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Projects service unavailable: {str(e)}",
            )

    async def fetch_projects(self, manager_id: Optional[UUID] = None) -> List[Dict]:
        """
        Fetch all projects with optional manager filter.

        Returns:
            List of project dictionaries

        Raises:
            HTTPException 503: If svc_projects is unavailable
        """
        try:
            params = {"limit": 10000}
            if manager_id:
                params["manager_id"] = str(manager_id)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{settings.PROJECTS_SERVICE_URL}/api/v1/projects",
                    headers=self.headers,
                    params=params,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
                else:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"Projects service error: {response.status_code}",
                    )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Projects service timeout",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Projects service unavailable: {str(e)}",
            )
