from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from api.deps import get_current_user_from_token
from db.database import get_db
from models.attachments import Attachment
from models.defects import Defects
from schemas.defects import AttachmentRead

router = APIRouter(prefix="/attachments", tags=["Attachments"])

# Максимальный размер файла: 10 МБ
MAX_FILE_SIZE = 10 * 1024 * 1024

# Разрешённые MIME типы
ALLOWED_CONTENT_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
]


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    defect_id: UUID = Form(..., description="ID дефекта"),
    file: UploadFile = File(..., description="Файл для загрузки"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Загрузка файла (фото) к дефекту.

    Файл сохраняется напрямую в БД в виде бинарных данных.

    Права доступа:
    - ENGINEER, MANAGER, ADMIN могут загружать файлы
    - SUPERVISOR, CUSTOMER не могут

    Ограничения:
    - Максимальный размер файла: 10 МБ
    - Разрешённые типы: JPEG, PNG, GIF, WebP, PDF

    Args:
        defect_id: ID дефекта (через Form data)
        file: Загружаемый файл (multipart/form-data)

    Returns:
        {"success": True, "data": AttachmentRead}

    Raises:
        HTTPException 403: Если у пользователя нет прав
        HTTPException 404: Если дефект не найден
        HTTPException 413: Если файл слишком большой
        HTTPException 415: Если тип файла не поддерживается
    """
    # Проверка прав доступа
    user_role = current_user["role"]
    if user_role in ["SUPERVISOR", "CUSTOMER"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only ENGINEER, MANAGER, or ADMIN can upload attachments.",
        )

    # Проверка существования дефекта
    defect = db.query(Defects).filter(Defects.id == defect_id).first()

    if not defect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Defect with ID {defect_id} not found",
        )

    # Чтение файла
    file_data = await file.read()
    file_size = len(file_data)

    # Проверка размера файла
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {file_size} bytes exceeds maximum allowed size {MAX_FILE_SIZE} bytes (10 MB)",
        )

    # Проверка типа файла
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{content_type}' is not supported. Allowed types: {ALLOWED_CONTENT_TYPES}",
        )

    # uploaded_by_id берём из токена
    uploaded_by_id = current_user["user_id"]

    # Создание вложения
    db_attachment = Attachment(
        defect_id=defect_id,
        file_name=file.filename or "unnamed",
        file_data=file_data,
        file_size=file_size,
        content_type=content_type,
        uploaded_by_id=uploaded_by_id,
    )

    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)

    return {"success": True, "data": AttachmentRead.model_validate(db_attachment)}


@router.get("/defects/{defect_id}/attachments", response_model=dict)
async def get_defect_attachments(
    defect_id: UUID,
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Получение списка вложений (метаданных) к дефекту.

    Доступно всем авторизованным пользователям.
    Возвращает метаданные файлов без самих бинарных данных.
    Вложения отсортированы по дате загрузки (новые первыми).

    Для получения самого файла используйте GET /attachments/{id}/download

    Args:
        defect_id: ID дефекта
        skip: Количество записей для пропуска (пагинация)
        limit: Максимальное количество записей

    Returns:
        {"success": True, "data": [AttachmentRead, ...]}

    Raises:
        HTTPException 404: Если дефект не найден
    """
    # Проверка существования дефекта
    defect = db.query(Defects).filter(Defects.id == defect_id).first()

    if not defect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Defect with ID {defect_id} not found",
        )

    # Получение вложений
    attachments = (
        db.query(Attachment)
        .filter(Attachment.defect_id == defect_id)
        .order_by(Attachment.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "success": True,
        "data": [AttachmentRead.model_validate(a) for a in attachments],
    }


@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Скачивание файла (фото) вложения.

    Возвращает бинарные данные файла с правильным Content-Type заголовком.
    Файл отображается в браузере (inline) или скачивается, в зависимости от типа.

    Args:
        attachment_id: ID вложения

    Returns:
        Response с бинарными данными файла

    Raises:
        HTTPException 404: Если вложение не найдено
    """
    # Поиск вложения
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment with ID {attachment_id} not found",
        )

    # Возвращаем файл
    return Response(
        content=attachment.file_data,
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f'inline; filename="{attachment.file_name}"',
            "Content-Length": str(attachment.file_size),
        },
    )


@router.delete("/{attachment_id}", response_model=dict)
async def delete_attachment(
    attachment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Удаление вложения (файла).

    Права доступа:
    - Автор вложения может удалить своё вложение
    - MANAGER и ADMIN могут удалять любые вложения
    - Остальные не могут удалять

    Удаляется вся запись из БД включая бинарные данные файла.

    Args:
        attachment_id: ID вложения для удаления

    Returns:
        {"success": True, "data": {"message": "Attachment deleted successfully"}}

    Raises:
        HTTPException 404: Если вложение не найдено
        HTTPException 403: Если у пользователя нет прав на удаление
    """
    # Поиск вложения
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attachment with ID {attachment_id} not found",
        )

    # Проверка прав доступа
    user_role = current_user["role"]
    user_id = current_user["user_id"]

    # Автор вложения или MANAGER/ADMIN могут удалять
    if attachment.uploaded_by_id != user_id and user_role not in ["MANAGER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only delete your own attachments.",
        )

    # Удаление вложения
    db.delete(attachment)
    db.commit()

    return {
        "success": True,
        "data": {"message": "Attachment deleted successfully"},
    }
