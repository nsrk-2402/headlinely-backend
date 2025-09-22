import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.sql import func
from app.models.enums import CategoryEnum


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Metadata
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(1000), nullable=False, unique=True)
    image_url = Column(String(500), nullable=True)

    # Category / tags
    category = Column(Enum(CategoryEnum), nullable=True, index=True)
    country = Column(String(5), nullable=True, index=True)  # ISO 3166-1 alpha-2 code

    # Dates
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships (for saved articles later)
    saved_by = relationship("SavedArticle", back_populates="article", cascade="all, delete-orphan")

    def __repr__(self):
        title_preview = (self.title[:30] + "...") if self.title else "No Title"
        return f"<Article id={self.id} title={title_preview} country={self.country}>"