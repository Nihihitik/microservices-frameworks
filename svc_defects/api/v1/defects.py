from datetime import datetime, UTC
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from api.deps import (
    check_valid_status_transition,
    get_current_user_from_token,
    require_role,
    validate_project_exists,
    validate_user_exists,
)
from db.database import get_db
from models.comments import Comment
from models.defect_history import DefectHistory
from models.defects import DefectPriority, Defects, DefectStatus
from schemas.defects import DefectCreate, DefectRead, DefectUpdate

router = APIRouter(prefix="/defects", tags=["Defects"])
security = HTTPBearer()


def _create_history_entry(
    db: Session,
    defect_id: UUID,
    changed_by_id: UUID,
    field_name: str,
    old_value: Optional[str],
    new_value: Optional[str],
):
    """
    Вспомогательная функция для создания записи в истории изменений дефекта.

    Args:
        db: Сессия базы данных
        defect_id: ID дефекта
        changed_by_id: ID пользователя, внесшего изменение
        field_name: Название изменённого поля
        old_value: Старое значение (строка)
        new_value: Новое значение (строка)
    """
    history_entry = DefectHistory(
        defect_id=defect_id,
        changed_by_id=changed_by_id,
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
    )
    db.add(history_entry)


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_defect(
    defect: DefectCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
    _role_check=Depends(require_role("ENGINEER", "MANAGER", "ADMIN")),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Создание нового дефекта (доступно для ENGINEER, MANAGER и ADMIN).

    Проверяет:
    - Существование project_id через запрос к svc_projects
    - Существование assignee_id через запрос к svc_auth (если указан)
    - author_id автоматически берётся из JWT токена

    Автоматически создаёт первую запись в DefectHistory о создании дефекта.

    Returns:
        {"success": True, "data": DefectRead}

    Raises:
        HTTPException 404: Если project или assignee не найдены
        HTTPException 403: Если роль не ENGINEER/MANAGER/ADMIN
    """
    token = credentials.credentials

    # Валидация project_id через svc_projects
    await validate_project_exists(defect.project_id, token)

    # Валидация assignee_id через svc_auth (если указан)
    if defect.assignee_id:
        await validate_user_exists(defect.assignee_id, token)

    # author_id берём из токена, игнорируем то что пришло в запросе
    author_id = current_user["user_id"]

    # Создание дефекта
    db_defect = Defects(
        project_id=defect.project_id,
        title=defect.title,
        description=defect.description,
        priority=defect.priority,
        status=defect.status,  # По умолчанию NEW из схемы
        author_id=author_id,
        assignee_id=defect.assignee_id,
        due_date=defect.due_date,
        location=defect.location,
    )

    db.add(db_defect)
    db.flush()  # Получаем ID для истории

    # Создание первой записи в истории
    _create_history_entry(
        db=db,
        defect_id=db_defect.id,
        changed_by_id=author_id,
        field_name="created",
        old_value=None,
        new_value=f"Defect created with status {defect.status.value}",
    )

    db.commit()
    db.refresh(db_defect)

    return {"success": True, "data": DefectRead.model_validate(db_defect)}


@router.get("/", response_model=dict)
async def get_defects(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    project_id: Optional[UUID] = Query(None, description="Фильтр по ID проекта"),
    status: Optional[DefectStatus] = Query(None, description="Фильтр по статусу"),
    priority: Optional[DefectPriority] = Query(None, description="Фильтр по приоритету"),
    assignee_id: Optional[UUID] = Query(None, description="Фильтр по ID исполнителя"),
    author_id: Optional[UUID] = Query(None, description="Фильтр по ID автора"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Получение списка дефектов с фильтрацией и пагинацией.

    Права доступа:
    - ENGINEER: видит дефекты, где author_id == user_id ИЛИ assignee_id == user_id
    - MANAGER и ADMIN: видят все дефекты
    - SUPERVISOR и CUSTOMER: видят дефекты своих проектов (требуется дополнительная логика)

    Returns:
        {"success": True, "data": [DefectRead, ...]}
    """
    query = db.query(Defects)

    # Фильтрация по ролям
    user_role = current_user["role"]
    user_id = current_user["user_id"]

    if user_role == "ENGINEER":
        # ENGINEER видит только свои дефекты (как автор или исполнитель)
        query = query.filter(
            (Defects.author_id == user_id) | (Defects.assignee_id == user_id)
        )
    elif user_role in ["SUPERVISOR", "CUSTOMER"]:
        # SUPERVISOR и CUSTOMER видят дефекты своих проектов
        # (Примечание: для полной реализации нужно джойнить с Projects
        # и проверять manager_id, но для упрощения оставим фильтр по author_id)
        query = query.filter(Defects.author_id == user_id)

    # Применение фильтров
    if project_id:
        query = query.filter(Defects.project_id == project_id)

    if status:
        query = query.filter(Defects.status == status)

    if priority:
        query = query.filter(Defects.priority == priority)

    if assignee_id:
        query = query.filter(Defects.assignee_id == assignee_id)

    if author_id:
        query = query.filter(Defects.author_id == author_id)

    # Сортировка по дате создания (новые первыми)
    query = query.order_by(Defects.created_at.desc())

    # Пагинация
    defects = query.offset(skip).limit(limit).all()

    return {"success": True, "data": [DefectRead.model_validate(d) for d in defects]}


@router.get("/{defect_id}", response_model=dict)
async def get_defect(
    defect_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Получение деталей конкретного дефекта по ID.

    Returns:
        {"success": True, "data": DefectRead}

    Raises:
        HTTPException 404: Если дефект не найден
        HTTPException 403: Если у пользователя нет прав на просмотр
    """
    defect = db.query(Defects).filter(Defects.id == defect_id).first()

    if not defect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Defect with ID {defect_id} not found",
        )

    # Проверка прав доступа
    user_role = current_user["role"]
    user_id = current_user["user_id"]

    if user_role == "ENGINEER":
        # ENGINEER может видеть только свои дефекты
        if defect.author_id != user_id and defect.assignee_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view your own defects.",
            )

    return {"success": True, "data": DefectRead.model_validate(defect)}


@router.patch("/{defect_id}", response_model=dict)
async def update_defect(
    defect_id: UUID,
    defect_update: DefectUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Обновление дефекта.

    Права доступа:
    - ENGINEER: может обновлять только свои дефекты (как автор или assignee)
    - MANAGER и ADMIN: могут обновлять любые дефекты

    Поддерживает частичное обновление (PATCH).
    При изменении критических полей (status, priority, assignee_id, due_date)
    автоматически создаётся запись в DefectHistory.

    Returns:
        {"success": True, "data": DefectRead}

    Raises:
        HTTPException 404: Если дефект не найден
        HTTPException 403: Если у пользователя нет прав на обновление
        HTTPException 400: Если переход статуса невалиден
    """
    token = credentials.credentials

    # Поиск дефекта
    defect = db.query(Defects).filter(Defects.id == defect_id).first()

    if not defect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Defect with ID {defect_id} not found",
        )

    # Проверка прав доступа
    user_role = current_user["role"]
    user_id = current_user["user_id"]

    if user_role == "ENGINEER":
        # ENGINEER может редактировать только свои дефекты
        if defect.author_id != user_id and defect.assignee_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only update your own defects.",
            )

    # Получение данных для обновления (только переданные поля)
    update_data = defect_update.model_dump(exclude_unset=True)

    # Валидация assignee_id если он меняется
    if "assignee_id" in update_data and update_data["assignee_id"]:
        await validate_user_exists(update_data["assignee_id"], token)

    # Валидация перехода статуса если он меняется
    if "status" in update_data:
        check_valid_status_transition(defect.status, update_data["status"])

    # Создание записей в истории для критических полей
    tracked_fields = ["status", "priority", "assignee_id", "due_date", "title", "location"]

    for field in tracked_fields:
        if field in update_data:
            old_value = getattr(defect, field)
            new_value = update_data[field]

            # Записываем историю только если значение изменилось
            if old_value != new_value:
                _create_history_entry(
                    db=db,
                    defect_id=defect.id,
                    changed_by_id=user_id,
                    field_name=field,
                    old_value=old_value,
                    new_value=new_value,
                )

    # Обновление полей
    for field, value in update_data.items():
        setattr(defect, field, value)

    # Обновление timestamp
    defect.updated_at = datetime.now(UTC)

    db.commit()
    db.refresh(defect)

    return {"success": True, "data": DefectRead.model_validate(defect)}


@router.delete("/{defect_id}", response_model=dict)
async def delete_defect(
    defect_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Удаление дефекта (каскадное удаление комментариев и истории).

    Права доступа:
    - ENGINEER: может удалять только свои дефекты (как автор)
    - MANAGER и ADMIN: могут удалять любые дефекты

    Returns:
        {"success": True, "data": {"message": "Defect deleted successfully"}}

    Raises:
        HTTPException 404: Если дефект не найден
        HTTPException 403: Если у пользователя нет прав на удаление
    """
    # Поиск дефекта
    defect = db.query(Defects).filter(Defects.id == defect_id).first()

    if not defect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Defect with ID {defect_id} not found",
        )

    # Проверка прав доступа
    user_role = current_user["role"]
    user_id = current_user["user_id"]

    if user_role == "ENGINEER":
        # ENGINEER может удалять только свои дефекты (как автор)
        if defect.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only delete defects you created.",
            )
    elif user_role in ["SUPERVISOR", "CUSTOMER"]:
        # SUPERVISOR и CUSTOMER не могут удалять дефекты
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You cannot delete defects.",
        )

    # Удаление дефекта (каскадное удаление комментариев и истории через ondelete="CASCADE")
    db.delete(defect)
    db.commit()

    return {"success": True, "data": {"message": "Defect deleted successfully"}}


@router.get("/{defect_id}/history", response_model=dict)
async def get_defect_history(
    defect_id: UUID,
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Получение истории изменений дефекта.

    Returns:
        {"success": True, "data": [DefectHistoryEntryRead, ...]}

    Raises:
        HTTPException 404: Если дефект не найден
    """
    # Проверяем существование дефекта
    defect = db.query(Defects).filter(Defects.id == defect_id).first()

    if not defect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Defect with ID {defect_id} not found",
        )

    # Получаем историю изменений
    history = (
        db.query(DefectHistory)
        .filter(DefectHistory.defect_id == defect_id)
        .order_by(DefectHistory.changed_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    from schemas.defects import DefectHistoryEntryRead

    return {
        "success": True,
        "data": [DefectHistoryEntryRead.model_validate(h) for h in history],
    }
