from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from api.deps import get_current_user_from_token, require_role, validate_manager_exists
from db.database import get_db
from models.projects import ProjectStage, ProjectStatus, Projects
from schemas.projects import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])
security = HTTPBearer()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
    _role_check=Depends(require_role("MANAGER", "ADMIN")),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Создание нового проекта (доступно только для MANAGER и ADMIN).

    Проверяет:
    - Существование manager_id через запрос к svc_auth
    - Уникальность code (если указан)

    Returns:
        {"success": True, "data": ProjectRead}

    Raises:
        HTTPException 400: Если code уже существует
        HTTPException 404: Если manager не найден
        HTTPException 403: Если роль не MANAGER/ADMIN
    """
    token = credentials.credentials

    # Валидация manager_id через svc_auth
    await validate_manager_exists(project.manager_id, token)

    # Проверка уникальности code (если указан)
    if project.code:
        existing_project = db.query(Projects).filter(Projects.code == project.code).first()
        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project with code '{project.code}' already exists"
            )

    # Создание проекта
    db_project = Projects(
        name=project.name,
        code=project.code,
        address=project.address,
        customer_name=project.customer_name,
        stage=project.stage,
        status=project.status,
        manager_id=project.manager_id,
        start_date=project.start_date,
        end_date=project.end_date,
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return {"success": True, "data": ProjectRead.model_validate(db_project)}


@router.get("/", response_model=dict)
async def get_projects(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    status: Optional[ProjectStatus] = Query(None, description="Фильтр по статусу"),
    stage: Optional[ProjectStage] = Query(None, description="Фильтр по этапу"),
    customer_name: Optional[str] = Query(None, description="Фильтр по имени заказчика (частичное совпадение)"),
    manager_id: Optional[UUID] = Query(None, description="Фильтр по ID менеджера"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Получение списка проектов с фильтрацией и пагинацией.

    Права доступа:
    - MANAGER и ADMIN: видят все проекты
    - SUPERVISOR и CUSTOMER: видят только проекты, где manager_id == current_user.user_id

    Returns:
        {"success": True, "data": [ProjectRead, ...]}
    """
    query = db.query(Projects)

    # Фильтрация по ролям
    user_role = current_user["role"]
    if user_role in ["SUPERVISOR", "CUSTOMER"]:
        # SUPERVISOR и CUSTOMER видят только свои проекты
        query = query.filter(Projects.manager_id == current_user["user_id"])

    # Применение фильтров
    if status:
        query = query.filter(Projects.status == status)

    if stage:
        query = query.filter(Projects.stage == stage)

    if customer_name:
        query = query.filter(Projects.customer_name.ilike(f"%{customer_name}%"))

    if manager_id:
        query = query.filter(Projects.manager_id == manager_id)

    # Пагинация
    projects = query.offset(skip).limit(limit).all()

    return {
        "success": True,
        "data": [ProjectRead.model_validate(p) for p in projects]
    }


@router.get("/{project_id}", response_model=dict)
async def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Получение деталей конкретного проекта по ID.

    Returns:
        {"success": True, "data": ProjectRead}

    Raises:
        HTTPException 404: Если проект не найден
    """
    project = db.query(Projects).filter(Projects.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )

    return {"success": True, "data": ProjectRead.model_validate(project)}


@router.patch("/{project_id}", response_model=dict)
async def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
    _role_check=Depends(require_role("MANAGER", "ADMIN")),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Обновление проекта (доступно только для MANAGER и ADMIN).

    Поддерживает частичное обновление (PATCH).
    Обновляет только переданные поля.

    Returns:
        {"success": True, "data": ProjectRead}

    Raises:
        HTTPException 404: Если проект не найден
        HTTPException 400: Если новый code уже используется другим проектом
        HTTPException 403: Если роль не MANAGER/ADMIN
    """
    token = credentials.credentials

    # Поиск проекта
    project = db.query(Projects).filter(Projects.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found"
        )

    # Получение данных для обновления (только переданные поля)
    update_data = project_update.model_dump(exclude_unset=True)

    # Валидация manager_id если он меняется
    if "manager_id" in update_data:
        await validate_manager_exists(update_data["manager_id"], token)

    # Проверка уникальности code если он меняется
    if "code" in update_data and update_data["code"] != project.code:
        existing_project = db.query(Projects).filter(
            Projects.code == update_data["code"],
            Projects.id != project_id
        ).first()

        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project with code '{update_data['code']}' already exists"
            )

    # Обновление полей
    for field, value in update_data.items():
        setattr(project, field, value)

    # Обновление timestamp
    project.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(project)

    return {"success": True, "data": ProjectRead.model_validate(project)}
