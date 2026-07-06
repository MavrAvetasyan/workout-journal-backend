from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    id: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ExerciseBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: str = Field(pattern="^(cardio|strength)$")
    description: str = ""
    archived: bool = False


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseUpdate(ExerciseBase):
    pass


class ExerciseRead(ExerciseBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExerciseSync(ExerciseBase):
    id: str


class WorkoutPhase(BaseModel):
    sets: int | None = None
    weight: float | None = None
    reps: int | None = None
    note: str = ""


class WorkoutExerciseBase(BaseModel):
    exercise_id: str
    status: str = Field(default="pending", max_length=20)
    plan: WorkoutPhase | None = None
    fact: WorkoutPhase | None = None


class WorkoutExerciseCreate(WorkoutExerciseBase):
    pass


class WorkoutExerciseRead(WorkoutExerciseBase):
    id: str
    position: int


class WorkoutExerciseSync(WorkoutExerciseBase):
    id: str


class WorkoutBase(BaseModel):
    title: str = Field(default="", max_length=255)
    type: str = Field(pattern="^(cardio|strength)$")
    status: str = Field(pattern="^(planned|active|completed|cancelled)$")
    start_time: datetime | None = None
    end_time: datetime | None = None
    exercises: list[WorkoutExerciseCreate] = Field(default_factory=list)


class WorkoutCreate(WorkoutBase):
    pass


class WorkoutUpdate(WorkoutBase):
    pass


class WorkoutRead(WorkoutBase):
    id: str
    created_at: datetime
    updated_at: datetime
    exercises: list[WorkoutExerciseRead]

    model_config = ConfigDict(from_attributes=True)


class WorkoutSync(WorkoutBase):
    id: str
    created_at: datetime
    updated_at: datetime
    exercises: list[WorkoutExerciseSync]


class MeasurementBase(BaseModel):
    title: str = Field(default="", max_length=255)
    date: date
    weight: float | None = None
    body_fat: float | None = None
    chest: float | None = None
    waist: float | None = None
    belly: float | None = None
    hips: float | None = None
    arm: float | None = None
    leg: float | None = None
    note: str = ""


class MeasurementCreate(MeasurementBase):
    pass


class MeasurementUpdate(MeasurementBase):
    pass


class MeasurementRead(MeasurementBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeasurementSync(MeasurementBase):
    id: str
    created_at: datetime
    updated_at: datetime


class SyncPayload(BaseModel):
    workouts: list[WorkoutSync] = Field(default_factory=list)
    exercises: list[ExerciseSync] = Field(default_factory=list)
    measurements: list[MeasurementSync] = Field(default_factory=list)
