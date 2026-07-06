from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import get_current_user
from ..models import Exercise, User, Workout, WorkoutExercise
from ..schemas import WorkoutCreate, WorkoutRead, WorkoutUpdate


router = APIRouter(prefix="/workouts", tags=["workouts"])


def build_workout_exercise(entry, position: int) -> WorkoutExercise:
    plan = entry.plan
    fact = entry.fact
    return WorkoutExercise(
        exercise_id=entry.exercise_id,
        position=position,
        status=entry.status,
        plan_sets=plan.sets if plan else None,
        plan_weight=plan.weight if plan else None,
        plan_reps=plan.reps if plan else None,
        plan_note=plan.note if plan else "",
        fact_sets=fact.sets if fact else None,
        fact_weight=fact.weight if fact else None,
        fact_reps=fact.reps if fact else None,
        fact_note=fact.note if fact else "",
    )


def serialize_workout(workout: Workout) -> WorkoutRead:
    return WorkoutRead(
        id=workout.id,
        title=workout.title,
        type=workout.type,
        status=workout.status,
        start_time=workout.start_time,
        end_time=workout.end_time,
        created_at=workout.created_at,
        updated_at=workout.updated_at,
        exercises=[
            {
                "id": item.id,
                "exercise_id": item.exercise_id,
                "position": item.position,
                "status": item.status,
                "plan": {
                    "sets": item.plan_sets,
                    "weight": item.plan_weight,
                    "reps": item.plan_reps,
                    "note": item.plan_note,
                } if any(value is not None for value in [item.plan_sets, item.plan_weight, item.plan_reps]) or item.plan_note else None,
                "fact": {
                    "sets": item.fact_sets,
                    "weight": item.fact_weight,
                    "reps": item.fact_reps,
                    "note": item.fact_note,
                } if any(value is not None for value in [item.fact_sets, item.fact_weight, item.fact_reps]) or item.fact_note else None,
            }
            for item in workout.exercises
        ],
    )


def get_workout_or_404(db: Session, current_user: User, workout_id: str) -> Workout:
    query = (
        select(Workout)
        .where(Workout.id == workout_id, Workout.user_id == current_user.id)
        .options(selectinload(Workout.exercises))
    )
    workout = db.scalar(query)
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return workout


def validate_workout_exercises(db: Session, current_user: User, payload: WorkoutCreate | WorkoutUpdate):
    exercise_ids = [item.exercise_id for item in payload.exercises]
    if not exercise_ids:
        return
    query = select(Exercise).where(
        Exercise.user_id == current_user.id,
        Exercise.id.in_(exercise_ids),
        Exercise.archived.is_(False),
    )
    existing = list(db.scalars(query))
    existing_ids = {item.id for item in existing}
    missing = [exercise_id for exercise_id in exercise_ids if exercise_id not in existing_ids]
    if missing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workout contains unknown or archived exercises")

    by_id = {item.id: item for item in existing}
    wrong_type = [exercise_id for exercise_id in exercise_ids if by_id[exercise_id].type != payload.type]
    if wrong_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workout contains exercises of another type")


def validate_workout_status(db: Session, current_user: User, payload: WorkoutCreate | WorkoutUpdate, workout_id: str | None = None):
    if payload.status != "active":
        return

    query = select(Workout).where(Workout.user_id == current_user.id, Workout.status == "active")
    if workout_id:
        query = query.where(Workout.id != workout_id)

    another_active = db.scalar(query)
    if another_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only one active workout is allowed")


@router.get("", response_model=list[WorkoutRead])
def list_workouts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = (
        select(Workout)
        .where(Workout.user_id == current_user.id)
        .options(selectinload(Workout.exercises))
        .order_by(Workout.start_time.desc().nullslast(), Workout.created_at.desc())
    )
    return [serialize_workout(item) for item in db.scalars(query)]


@router.post("", response_model=WorkoutRead, status_code=status.HTTP_201_CREATED)
def create_workout(payload: WorkoutCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    validate_workout_exercises(db, current_user, payload)
    validate_workout_status(db, current_user, payload)
    workout = Workout(
        user_id=current_user.id,
        title=payload.title.strip(),
        type=payload.type,
        status=payload.status,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    workout.exercises = [build_workout_exercise(entry, index) for index, entry in enumerate(payload.exercises)]
    db.add(workout)
    db.commit()
    db.refresh(workout)
    workout = get_workout_or_404(db, current_user, workout.id)
    return serialize_workout(workout)


@router.put("/{workout_id}", response_model=WorkoutRead)
def update_workout(
    workout_id: str,
    payload: WorkoutUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_workout_exercises(db, current_user, payload)
    validate_workout_status(db, current_user, payload, workout_id=workout_id)
    workout = get_workout_or_404(db, current_user, workout_id)
    workout.title = payload.title.strip()
    workout.type = payload.type
    workout.status = payload.status
    workout.start_time = payload.start_time
    workout.end_time = payload.end_time
    workout.exercises.clear()
    workout.exercises.extend(build_workout_exercise(entry, index) for index, entry in enumerate(payload.exercises))
    db.commit()
    db.refresh(workout)
    workout = get_workout_or_404(db, current_user, workout.id)
    return serialize_workout(workout)


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    workout = get_workout_or_404(db, current_user, workout_id)
    db.delete(workout)
    db.commit()
