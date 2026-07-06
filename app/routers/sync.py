from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import get_current_user
from ..models import Exercise, Measurement, User, Workout, WorkoutExercise
from ..schemas import SyncPayload


router = APIRouter(prefix="/sync", tags=["sync"])


def serialize_workout_item(item: Workout) -> dict:
    return {
        "id": item.id,
        "title": item.title,
        "type": item.type,
        "status": item.status,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "exercises": [
            {
                "id": exercise.id,
                "exercise_id": exercise.exercise_id,
                "status": exercise.status,
                "position": exercise.position,
                "plan": {
                    "sets": exercise.plan_sets,
                    "weight": exercise.plan_weight,
                    "reps": exercise.plan_reps,
                    "note": exercise.plan_note,
                }
                if any(value is not None for value in [exercise.plan_sets, exercise.plan_weight, exercise.plan_reps]) or exercise.plan_note
                else None,
                "fact": {
                    "sets": exercise.fact_sets,
                    "weight": exercise.fact_weight,
                    "reps": exercise.fact_reps,
                    "note": exercise.fact_note,
                }
                if any(value is not None for value in [exercise.fact_sets, exercise.fact_weight, exercise.fact_reps]) or exercise.fact_note
                else None,
            }
            for exercise in item.exercises
        ],
    }


@router.get("", response_model=SyncPayload)
def get_sync_payload(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    workouts = list(
        db.scalars(
            select(Workout)
            .where(Workout.user_id == current_user.id)
            .options(selectinload(Workout.exercises))
            .order_by(Workout.created_at.desc())
        )
    )
    exercises = list(db.scalars(select(Exercise).where(Exercise.user_id == current_user.id).order_by(Exercise.name)))
    measurements = list(db.scalars(select(Measurement).where(Measurement.user_id == current_user.id).order_by(Measurement.date.desc())))

    return SyncPayload(
        workouts=[serialize_workout_item(item) for item in workouts],
        exercises=[
            {
                "id": item.id,
                "name": item.name,
                "type": item.type,
                "description": item.description,
                "archived": item.archived,
            }
            for item in exercises
        ],
        measurements=[
            {
                "id": item.id,
                "title": item.title,
                "date": item.date,
                "weight": item.weight,
                "body_fat": item.body_fat,
                "chest": item.chest,
                "waist": item.waist,
                "belly": item.belly,
                "hips": item.hips,
                "arm": item.arm,
                "leg": item.leg,
                "note": item.note,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }
            for item in measurements
        ],
    )


@router.put("", response_model=SyncPayload)
def replace_sync_payload(payload: SyncPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    exercise_map = {item.id: item for item in payload.exercises}

    for workout in payload.workouts:
        for entry in workout.exercises:
            if entry.exercise_id not in exercise_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Workout contains exercise that is missing in exercise directory",
                )

    active_count = sum(1 for item in payload.workouts if item.status == "active")
    if active_count > 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only one active workout is allowed")

    db.execute(delete(WorkoutExercise).where(WorkoutExercise.workout_id.in_(select(Workout.id).where(Workout.user_id == current_user.id))))
    db.execute(delete(Workout).where(Workout.user_id == current_user.id))
    db.execute(delete(Measurement).where(Measurement.user_id == current_user.id))
    db.execute(delete(Exercise).where(Exercise.user_id == current_user.id))
    db.flush()

    for item in payload.exercises:
        db.add(
            Exercise(
                id=item.id,
                user_id=current_user.id,
                name=item.name.strip(),
                type=item.type,
                description=item.description.strip(),
                archived=item.archived,
            )
        )

    for item in payload.measurements:
        db.add(
            Measurement(
                id=item.id,
                user_id=current_user.id,
                title=item.title.strip(),
                date=item.date,
                weight=item.weight,
                body_fat=item.body_fat,
                chest=item.chest,
                waist=item.waist,
                belly=item.belly,
                hips=item.hips,
                arm=item.arm,
                leg=item.leg,
                note=item.note.strip(),
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )

    for item in payload.workouts:
        workout = Workout(
            id=item.id,
            user_id=current_user.id,
            title=item.title.strip(),
            type=item.type,
            status=item.status,
            start_time=item.start_time,
            end_time=item.end_time,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        workout.exercises = [
            WorkoutExercise(
                id=entry.id,
                exercise_id=entry.exercise_id,
                position=index,
                status=entry.status,
                plan_sets=entry.plan.sets if entry.plan else None,
                plan_weight=entry.plan.weight if entry.plan else None,
                plan_reps=entry.plan.reps if entry.plan else None,
                plan_note=entry.plan.note if entry.plan else "",
                fact_sets=entry.fact.sets if entry.fact else None,
                fact_weight=entry.fact.weight if entry.fact else None,
                fact_reps=entry.fact.reps if entry.fact else None,
                fact_note=entry.fact.note if entry.fact else "",
            )
            for index, entry in enumerate(item.exercises)
        ]
        db.add(workout)

    db.commit()
    return get_sync_payload(current_user=current_user, db=db)
