from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.user_service import UserService
from app.schemas.user_schemas import (
    UserListResponse,
    UserCreate,
    UserUpdate,
    UserCreateResponse,
    UserUpdateResponse,
    UserDeleteResponse,
    UserLogin,
    UserResponse,
    UserLoginResponse
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/",
    response_model=UserListResponse,
    summary="Get all users",
    description="Retrieve all users with total count"
)
def get_all_users(db: Session = Depends(get_db)):
    """
    Get all users.
    
    **Returns**: List of all users with total count
    
    Example response:
    ```
    {
        "total": 2,
        "users": [
            {
                "id": 1,
                "email": "admin@company.tn",
                "full_name": "Admin Système",
                "role": "ADMIN",
                "is_active": 1,
                "created_at": "2024-01-01T00:00:00"
            }
        ]
    }
    ```
    """
    try:
        return UserService.get_all_users(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/",
    response_model=UserCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
    description="Create a new user account"
)
def create_user(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user with all required fields.
    
    All parameters are required and must be provided:
    - **email**: User email address (must be unique and valid format)
    - **password**: User password (minimum 6 characters)
    - **full_name**: User full name
    - **role**: User role (ADMIN | MANAGER | ANALYST | VIEWER)
    - **is_active**: Active status (1 = active, 0 = inactive)
    
    Example response on success:
    ```
    {
        "message": "User admin@company.tn created successfully",
        "user": {
            "id": 1,
            "email": "admin@company.tn",
            "full_name": "Admin Système",
            "role": "ADMIN",
            "is_active": 1,
            "created_at": "2024-01-01T00:00:00"
        }
    }
    ```
    """
    try:
        return UserService.create_user(db, user_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put(
    "/{user_id}",
    response_model=UserUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a user",
    description="Update a user by id"
)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a user by id. All fields are optional.
    
    Only provided fields will be updated:
    - **password**: New password (minimum 6 characters, will be hashed)
    - **full_name**: Updated full name
    - **role**: Updated role (ADMIN | MANAGER | ANALYST | VIEWER)
    - **is_active**: Updated active status (1 = active, 0 = inactive)
    
    Example response on success:
    ```
    {
        "message": "User Admin Système updated successfully",
        "user": {
            "id": 1,
            "email": "admin@company.tn",
            "full_name": "Admin Système Updated",
            "role": "MANAGER",
            "is_active": 1,
            "created_at": "2024-01-01T00:00:00"
        }
    }
    ```
    """
    try:
        return UserService.update_user(db, user_id, user_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/{user_id}",
    response_model=UserDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a user",
    description="Delete a user by id"
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a user by id.
    
    Example response on success:
    ```
    {
        "message": "User Admin Système deleted successfully"
    }
    ```
    """
    try:
        return UserService.delete_user(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/login",
    response_model=UserLoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate user with email and password"
)
def login_user(
    user_login: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate a user with email and password.
    
    **Parameters**:
    - **email**: User email address (unique identifier)
    - **password**: User password (minimum 6 characters)
    
    **Returns**: Success message and authenticated user data
    
    Example response on success:
    ```
    {
        "message": "Login successful",
        "user": {
            "id": 1,
            "email": "admin@company.tn",
            "full_name": "Admin Système",
            "role": "ADMIN",
            "is_active": 1,
            "created_at": "2024-01-01T00:00:00"
        }
    }
    ```
    """
    try:
        return UserService.login_user(db, user_login.email, user_login.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
