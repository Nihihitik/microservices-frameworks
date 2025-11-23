from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.deps import get_current_user_from_token
from db.database import get_db
from models.comments import Comment
from models.defects import Defects
from schemas.defects import CommentCreate, CommentRead

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Создание комментария к дефекту.

    Все авторизованные пользователи могут добавлять комментарии.
    author_id автоматически берётся из JWT токена.

    Returns:
        {"success": True, "data": CommentRead}

    Raises:
        HTTPException 404: Если дефект не найден
    """
    # Проверка существования дефекта
    defect = db.query(Defects).filter(Defects.id == comment_data.defect_id).first()

    if not defect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Defect with ID {comment_data.defect_id} not found",
        )

    # author_id берём из токена
    author_id = current_user["user_id"]

    # Создание комментария
    db_comment = Comment(
        defect_id=comment_data.defect_id,
        author_id=author_id,
        text=comment_data.text,
    )

    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    return {"success": True, "data": CommentRead.model_validate(db_comment)}


@router.get("/defects/{defect_id}/comments", response_model=dict)
async def get_defect_comments(
    defect_id: UUID,
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Получение списка комментариев к дефекту.

    Комментарии отсортированы по дате создания (новые первыми).

    Returns:
        {"success": True, "data": [CommentRead, ...]}

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

    # Получение комментариев
    comments = (
        db.query(Comment)
        .filter(Comment.defect_id == defect_id)
        .order_by(Comment.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {"success": True, "data": [CommentRead.model_validate(c) for c in comments]}


@router.patch("/{comment_id}", response_model=dict)
async def update_comment(
    comment_id: UUID,
    text: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Обновление комментария.

    Только автор комментария может его редактировать.

    Returns:
        {"success": True, "data": CommentRead}

    Raises:
        HTTPException 404: Если комментарий не найден
        HTTPException 403: Если пользователь не автор комментария
    """
    # Поиск комментария
    comment = db.query(Comment).filter(Comment.id == comment_id).first()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with ID {comment_id} not found",
        )

    # Проверка прав доступа (только автор может редактировать)
    user_id = current_user["user_id"]

    if comment.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only edit your own comments.",
        )

    # Обновление текста комментария
    comment.text = text

    db.commit()
    db.refresh(comment)

    return {"success": True, "data": CommentRead.model_validate(comment)}


@router.delete("/{comment_id}", response_model=dict)
async def delete_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Удаление комментария.

    Права доступа:
    - Автор комментария может удалять свой комментарий
    - MANAGER и ADMIN могут удалять любые комментарии

    Returns:
        {"success": True, "data": {"message": "Comment deleted successfully"}}

    Raises:
        HTTPException 404: Если комментарий не найден
        HTTPException 403: Если у пользователя нет прав на удаление
    """
    # Поиск комментария
    comment = db.query(Comment).filter(Comment.id == comment_id).first()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with ID {comment_id} not found",
        )

    # Проверка прав доступа
    user_role = current_user["role"]
    user_id = current_user["user_id"]

    # Автор или ADMIN/MANAGER могут удалять
    if comment.author_id != user_id and user_role not in ["MANAGER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only delete your own comments.",
        )

    # Удаление комментария
    db.delete(comment)
    db.commit()

    return {"success": True, "data": {"message": "Comment deleted successfully"}}
