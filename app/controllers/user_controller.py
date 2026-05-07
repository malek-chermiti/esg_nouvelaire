from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.user_service import UserService
from app.schemas.user_schemas import (
    UserListResponse,
    UserCreate,
    UserAnalystCreate,
    UserUpdate,
    UserProfileUpdate,
    UserCreateResponse,
    UserUpdateResponse,
    UserDeleteResponse,
    UserLogin,
    UserResponse,
    UserLoginResponse,
    UserLogoutResponse
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
def get_all_users(current_user_id: int = Header(default=None), db: Session = Depends(get_db)):
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
        if current_user_id is None:
            raise HTTPException(status_code=401, detail="Missing X-User-Id header. User authentication required.")
        return UserService.get_all_users(db, current_user_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/",
    response_model=UserCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up admin",
    description="Create a new admin account"
)
def create_user(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Sign up an admin user.
    
    All parameters are required and must be provided:
    - **email**: User email address (must be unique and valid format)
    - **password**: User password (minimum 6 characters)
    - **full_name**: User full name
    - **role**: Must be ADMIN
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
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/analysts",
    response_model=UserCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create analyst",
    description="Create an analyst account by admin only"
)
def create_analyst(
    user_create: UserAnalystCreate,
    current_user_id: int = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    Create an analyst account.

    Only an admin can call this endpoint.
    The role is forced to ANALYST.
    """
    try:
        if current_user_id is None:
            raise HTTPException(status_code=401, detail="Missing X-User-Id header. User authentication required.")
        return UserService.create_analyst(db, current_user_id, user_create)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put(
    "/status/{user_id}",
    response_model=UserUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a user",
    description="Update a user by id"
)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user_id: int = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    Update a user's status by id.
    
    Only the status can be updated:
    - **is_active**: Updated active status (1 = active, 0 = inactive)
    
    Example response on success:
    ```
    {
        "message": "User Admin Système updated successfully",
        "user": {
            "id": 1,
            "email": "admin@company.tn",
            "full_name": "Admin Système Updated",
            "role": "ANALYST",
            "is_active": 1,
            "created_at": "2024-01-01T00:00:00"
        }
    }
    ```
    """
    try:
        if current_user_id is None:
            raise HTTPException(status_code=401, detail="Missing X-User-Id header. User authentication required.")
        return UserService.update_user_status(db, current_user_id, user_id, user_update)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put(
    "/me",
    response_model=UserUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update my profile",
    description="Update only the connected user's full name"
)
def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user_id: int = Header(default=None),
    db: Session = Depends(get_db)
):
    """
    Update the connected user's profile.

    Only the user's full name can be changed.
    """
    try:
        if current_user_id is None:
            raise HTTPException(status_code=401, detail="Missing X-User-Id header. User authentication required.")
        return UserService.update_own_profile(db, current_user_id, profile_update)
    except HTTPException:
        raise
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
    current_user_id: int = Header(default=None),
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
        if current_user_id is None:
            raise HTTPException(status_code=401, detail="Missing X-User-Id header. User authentication required.")
        return UserService.delete_user(db, current_user_id, user_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
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


@router.post(
    "/logout",
    response_model=UserLogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Logout user and invalidate session"
)
def logout_user(x_user_id: int = Header(default=None)):
    """
    Logout a user and invalidate their session.
    
    **Parameters**:
    - **X-User-Id**: User ID header (required)
    
    **Returns**: Success logout message
    
    Example response on success:
    ```
    {
        "message": "Logout successfully!"
    }
    ```
    """
    if x_user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Missing X-User-Id header. User authentication required."
        )
    
    # Session invalidation is simulated here
    # In a real application, you would:
    # - Invalidate JWT token
    # - Delete session from database
    # - Clear cache
    
    return {
        "message": "Logout successfully!"
    }
