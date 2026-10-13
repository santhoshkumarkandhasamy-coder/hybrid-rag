from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    # None / empty = search every document the user owns
    document_ids: list[str] | None = None
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"
    quota_mb: int | None = Field(default=None, ge=1)


class UpdateUserRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    quota_mb: int | None = Field(default=None, ge=1)
    new_password: str | None = None


class SettingsUpdate(BaseModel):
    allow_signup: bool
