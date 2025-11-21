"""Schemas для сервиса дефектов."""

from .defects import (
    AttachmentBase,
    AttachmentCreate,
    AttachmentRead,
    CommentBase,
    CommentCreate,
    CommentRead,
    DefectBase,
    DefectCreate,
    DefectHistoryEntryBase,
    DefectHistoryEntryCreate,
    DefectHistoryEntryRead,
    DefectRead,
    DefectUpdate,
)

__all__ = [
    "DefectBase",
    "DefectCreate",
    "DefectRead",
    "DefectUpdate",
    "CommentBase",
    "CommentCreate",
    "CommentRead",
    "AttachmentBase",
    "AttachmentCreate",
    "AttachmentRead",
    "DefectHistoryEntryBase",
    "DefectHistoryEntryCreate",
    "DefectHistoryEntryRead",
]
