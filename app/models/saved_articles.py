from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base
from sqlalchemy.sql import func


class SavedArticle(Base):
    __tablename__ = "saved_articles"


    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True)

    saved_at = Column(DateTime(timezone=True), server_default=func.now())


    # Constraints
    __table_args__ = (UniqueConstraint("user_id", "article_id", name = "uq_user_article"),)


    # Relationships
    user = relationship("User", back_populates="saved_articles", passive_deletes=True)
    article = relationship("Article", back_populates="saved_by", passive_deletes=True)

    def __repr__(self):
        return f"<SavedArticle user_id={self.user_id} article_id={self.article_id}>"