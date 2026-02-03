from datetime import datetime
from sqlalchemy import String, BigInteger, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List


class Base(DeclarativeBase):
    pass


class Video(Base):
    __tablename__ = "videos"

    # Primary key - строковый UUID
    id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Основные поля
    creator_id: Mapped[str] = mapped_column(String, nullable=False)
    video_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Счетчики (финальные значения)
    views_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    likes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reports_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Служебные поля
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Связь с снапшотами
    snapshots: Mapped[List["VideoSnapshot"]] = relationship(
        "VideoSnapshot", 
        back_populates="video",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Video(id={self.id}, creator_id={self.creator_id})>"


class VideoSnapshot(Base):
    __tablename__ = "video_snapshots"

    # Primary key - строковый UUID
    id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Foreign key к видео
    video_id: Mapped[str] = mapped_column(
        String, 
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Текущие значения на момент замера
    views_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    likes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reports_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Приращения (дельты)
    delta_views_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    delta_likes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delta_comments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delta_reports_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Время замера (это поле из JSON created_at) - КРИТИЧНО для запросов по датам
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False,
        index=True  # Индекс для быстрой фильтрации по датам
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Связь с видео
    video: Mapped["Video"] = relationship("Video", back_populates="snapshots")

    def __repr__(self):
        return f"<VideoSnapshot(id={self.id}, video_id={self.video_id}, created_at={self.created_at})>"


# Дополнительные индексы для оптимизации запросов
Index('idx_snapshots_created_at_date', VideoSnapshot.created_at)
Index('idx_videos_created_at_date', Video.video_created_at)
