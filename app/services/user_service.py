from sqlalchemy.orm import Session
import hashlib
from app.models.models import Users
from app.schemas.user_schemas import (
    UserListResponse,
    UserResponse,
    UserCreate,
    UserAnalystCreate,
    UserUpdate,
    UserProfileUpdate,
)


class UserService:
    ALLOWED_ROLES = {"ADMIN", "ANALYST"}

    @staticmethod
    def get_user_or_raise(db: Session, user_id: int) -> Users:
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        return user

    @staticmethod
    def require_admin(db: Session, user_id: int) -> Users:
        user = UserService.get_user_or_raise(db, user_id)
        if user.role != "ADMIN":
            raise PermissionError("Admin privileges required")
        return user
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> dict:
        """Create an admin user in the database"""

        # Check if email already exists
        existing_user = db.query(Users).filter(Users.email == user_create.email).first()
        if existing_user:
            raise ValueError(f"User with email {user_create.email} already exists")

        if user_create.role != "ADMIN":
            raise ValueError("create_user is reserved for admin signup")
        
        # Hash password
        hashed_password = UserService.hash_password(user_create.password)
        
        # Create new user
        new_user = Users(
            email=user_create.email,
            password=hashed_password,
            full_name=user_create.full_name,
            role="ADMIN",
            is_active=user_create.is_active
        )
        
        # Save to database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "message": f"Admin {user_create.email} created successfully",
            "user": UserResponse.from_orm(new_user)
        }

    @staticmethod
    def create_analyst(db: Session, current_user_id: int, analyst_create: UserAnalystCreate) -> dict:
        """Create an analyst user in the database"""
        UserService.require_admin(db, current_user_id)

        existing_user = db.query(Users).filter(Users.email == analyst_create.email).first()
        if existing_user:
            raise ValueError(f"User with email {analyst_create.email} already exists")

        hashed_password = UserService.hash_password(analyst_create.password)

        new_user = Users(
            email=analyst_create.email,
            password=hashed_password,
            full_name=analyst_create.full_name,
            role="ANALYST",
            is_active=analyst_create.is_active,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "message": f"Analyst {analyst_create.email} created successfully",
            "user": UserResponse.from_orm(new_user),
        }
    
    @staticmethod
    def get_all_users(db: Session, current_user_id: int) -> UserListResponse:
        """Get all users with total count"""
        UserService.require_admin(db, current_user_id)

        users = db.query(Users).all()
        return UserListResponse(
            total=len(users),
            users=[UserResponse.from_orm(u) for u in users]
        )
    
    @staticmethod
    def update_user_status(db: Session, current_user_id: int, user_id: int, user_update: UserUpdate) -> dict:
        """Update user status by id"""
        UserService.require_admin(db, current_user_id)

        user = UserService.get_user_or_raise(db, user_id)
        if user.role != "ANALYST":
            raise ValueError("Only analyst users can be updated or deleted by this action")

        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        # Save to database
        db.commit()
        db.refresh(user)
        
        return {
            "message": f"User {user.full_name} updated successfully",
            "user": UserResponse.from_orm(user)
        }

    @staticmethod
    def update_own_profile(db: Session, current_user_id: int, user_update: UserProfileUpdate) -> dict:
        """Update the connected user's profile"""
        user = UserService.get_user_or_raise(db, current_user_id)

        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)

        return {
            "message": f"User {user.full_name} updated successfully",
            "user": UserResponse.from_orm(user)
        }
    
    @staticmethod
    def delete_user(db: Session, current_user_id: int, user_id: int) -> dict:
        """Delete user by id"""
        UserService.require_admin(db, current_user_id)

        user = UserService.get_user_or_raise(db, user_id)
        if user.role != "ANALYST":
            raise ValueError("Only analyst users can be deleted")
        
        # Store full_name for response message
        full_name = user.full_name
        
        # Delete from database
        db.delete(user)
        db.commit()
        
        return {"message": f"User {full_name} deleted successfully"}
    
    @staticmethod
    def login_user(db: Session, email: str, password: str) -> dict:
        """Authenticate user by email and password"""
        # Check if user exists by email
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise ValueError("User not found")
        
        # Hash the input password
        hashed_password = UserService.hash_password(password)
        
        # Compare hashed password with stored password
        if hashed_password != user.password:
            raise ValueError("Invalid password")

       
    
        # Return success response with user data
        return {
            "message": "Login successful",
            "user": UserResponse.from_orm(user)
        }
