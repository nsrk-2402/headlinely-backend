from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)    # only for manual signup
    full_name = Column(String(255), nullable=True)
    
    oauth_provider = Column(String(50), nullable=True)      # "google", "github", etc.
    oauth_id = Column(String(255), nullable=True)        # provider user ID
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(hashed_password IS NOT NULL) OR (oauth_provider IS NOT NULL AND oauth_id IS NOT NULL)",
            name="ck_user_auth_method"
        ),
    )

    saved_articles = relationship("SavedArticle", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    country_preferences = relationship("UserCountryPreference", back_populates="user", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<User id={self.id} email={self.email} provider={self.oauth_provider}>"