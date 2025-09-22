from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class UserCountryPreference(Base):
    __tablename__ = "user_country_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    country_code = Column(String(5), nullable=False)  # ISO 2-letter or 3-letter code
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "country_code", name="uq_user_country"),)

    user = relationship("User", back_populates="country_preferences")

    def __repr__(self):
        return f"<UserCountryPreference user_id={self.user_id} country={self.country_code}>"
