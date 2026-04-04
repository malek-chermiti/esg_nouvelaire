from sqlalchemy.orm import Session
import hashlib
from app.models.models import Users
from app.schemas.user_schemas import UserListResponse, UserResponse, UserCreate, UserUpdate


class UserService:
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> dict:
        """Create a new user in the database"""
        # Check if email already exists
        existing_user = db.query(Users).filter(Users.email == user_create.email).first()
        if existing_user:
            raise ValueError(f"User with email {user_create.email} already exists")
        
        # Hash password
        hashed_password = UserService.hash_password(user_create.password)
        
        # Create new user
        new_user = Users(
            email=user_create.email,
            password=hashed_password,
            full_name=user_create.full_name,
            role=user_create.role,
            is_active=user_create.is_active
        )
        
        # Save to database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "message": f"User {user_create.email} created successfully",
            "user": UserResponse.from_orm(new_user)
        }
    
    @staticmethod
    def get_all_users(db: Session) -> UserListResponse:
        """Get all users with total count"""
        users = db.query(Users).all()
        return UserListResponse(
            total=len(users),
            users=[UserResponse.from_orm(u) for u in users]
        )
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> dict:
        """Update user by id"""
        # Find user by id
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        # Update only provided fields
        if user_update.password is not None:
            user.password = UserService.hash_password(user_update.password)
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.role is not None:
            user.role = user_update.role
        if user_update.is_active is not None:
            user.is_active = user_update.is_active
        
        # Save to database
        db.commit()
        db.refresh(user)
        
        return {
            "message": f"User {user.full_name} updated successfully",
            "user": UserResponse.from_orm(user)
        }
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> dict:
        """Delete user by id"""
        # Find user by id
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        # Store full_name for response message
        full_name = user.full_name
        
        # Delete from database
        db.delete(user)
        db.commit()
        
        return {"message": f"User {full_name} deleted successfully"}
