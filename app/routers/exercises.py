from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Exercise, User
from ..schemas import ExerciseCreate, ExerciseRead, ExerciseUpdate


router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[ExerciseRead])
def list_exercises(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = select(Exercise).where(Exercise.user_id == current_user.id).order_by(Exercise.archived, Exercise.name)
    return list(db.scalars(query))


@router.post("", response_model=ExerciseRead, status_code=status.HTTP_201_CREATED)
def create_exercise(payload: ExerciseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.scalar(
        select(Exercise).where(
            Exercise.user_id == current_user.id,
            Exercise.name == payload.name.strip(),
        )
    )
    if existing and not existing.archived:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Exercise already exists")

    exercise = Exercise(
        user_id=current_user.id,
        name=payload.name.strip(),
        type=payload.type,
        description=payload.description.strip(),
        archived=payload.archived,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


@router.put("/{exercise_id}", response_model=ExerciseRead)
def update_exercise(
    exercise_id: str,
    payload: ExerciseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exercise = db.scalar(select(Exercise).where(Exercise.id == exercise_id, Exercise.user_id == current_user.id))
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    exercise.name = payload.name.strip()
    exercise.type = payload.type
    exercise.description = payload.description.strip()
    exercise.archived = payload.archived
    db.commit()
    db.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(exercise_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exercise = db.scalar(select(Exercise).where(Exercise.id == exercise_id, Exercise.user_id == current_user.id))
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")

    db.delete(exercise)
    db.commit()
