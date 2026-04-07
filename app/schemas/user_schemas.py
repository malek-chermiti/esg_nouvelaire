from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import List, Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for creating a user - all fields required"""
    email: EmailStr = Field(
        ...,
        example="t@company.tn",
        description="Adresse email de l'utilisateur (unique)"
    )
    password: str = Field(
        ...,
        example="admin1234",
        description="Mot de passe (minimum 6 caractères)"
    )
    full_name: str = Field(
        ...,
        example="Admin Système",
        description="Nom complet de l'utilisateur"
    )
    role: str = Field(
        ...,
        example="ADMIN",
        description="Rôle : ADMIN | ANALYST"
    )
    is_active: int = Field(
        ...,
        example=1,
        description="Statut : 1 = actif, 0 = inactif"
    )

    @field_validator('password')
    @classmethod
    def password_length(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        valid_roles = ['ADMIN', 'ANALYST']
        if v not in valid_roles:
            raise ValueError(f'Role must be one of {valid_roles}')
        return v

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Schema for updating a user - all fields optional"""
    password: Optional[str] = Field(
        None,
        example="newpassword123",
        description="Nouveau mot de passe (minimum 6 caractères)"
    )
    full_name: Optional[str] = Field(
        None,
        example="Admin System Updated",
        description="Nom complet mise à jour"
    )
    role: Optional[str] = Field(
        None,
        example="ADMIN",
        description="Rôle mise à jour : ADMIN | ANALYST"
    )
    is_active: Optional[int] = Field(
        None,
        example=1,
        description="Statut mise à jour : 1 = actif, 0 = inactif"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v is not None:
            valid_roles = ['ADMIN', 'ANALYST']
            if v not in valid_roles:
                raise ValueError(f'Role must be one of {valid_roles}')
        return v

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    email: str
    full_name: str
    role: str
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for user list response"""
    total: int
    users: List[UserResponse]


class UserCreateResponse(BaseModel):
    """Schema for successful user creation response"""
    message: str
    user: UserResponse


class UserUpdateResponse(BaseModel):
    """Schema for successful user update response"""
    message: str
    user: UserResponse


class UserDeleteResponse(BaseModel):
    """Schema for successful user delete response"""
    message: str


class UserLogin(BaseModel):
    """Schema for user login - email and password required"""
    email: EmailStr = Field(
        ...,
        example="admin@company.tn",
        description="Adresse email de l'utilisateur (identifiant unique)"
    )
    password: str = Field(
        ...,
        example="admin1234",
        description="Mot de passe de l'utilisateur (minimum 6 caractères)"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

    class Config:
        from_attributes = True


class UserLoginResponse(BaseModel):
    """Schema for successful user login response"""
    message: str
    user: UserResponse
