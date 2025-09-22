from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

# Import the shared enum
from app.models.enums import CategoryEnum


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    category = Column(Enum(CategoryEnum), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "category", name = "uq_user_category"),)

    user =  relationship("User", back_populates="preferences", passive_deletes=True)


    def __repr__(self):
        return f"<UserPreference user_id={self.user_id} category={self.category}>"