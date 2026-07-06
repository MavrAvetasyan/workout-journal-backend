from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Measurement, User
from ..schemas import MeasurementCreate, MeasurementRead, MeasurementUpdate


router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.get("", response_model=list[MeasurementRead])
def list_measurements(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = select(Measurement).where(Measurement.user_id == current_user.id).order_by(Measurement.date.desc())
    return list(db.scalars(query))


@router.post("", response_model=MeasurementRead, status_code=status.HTTP_201_CREATED)
def create_measurement(
    payload: MeasurementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    measurement = Measurement(
        user_id=current_user.id,
        title=payload.title.strip(),
        date=payload.date,
        weight=payload.weight,
        body_fat=payload.body_fat,
        chest=payload.chest,
        waist=payload.waist,
        belly=payload.belly,
        hips=payload.hips,
        arm=payload.arm,
        leg=payload.leg,
        note=payload.note.strip(),
    )
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.put("/{measurement_id}", response_model=MeasurementRead)
def update_measurement(
    measurement_id: str,
    payload: MeasurementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    measurement = db.scalar(select(Measurement).where(Measurement.id == measurement_id, Measurement.user_id == current_user.id))
    if not measurement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Measurement not found")

    measurement.title = payload.title.strip()
    measurement.date = payload.date
    measurement.weight = payload.weight
    measurement.body_fat = payload.body_fat
    measurement.chest = payload.chest
    measurement.waist = payload.waist
    measurement.belly = payload.belly
    measurement.hips = payload.hips
    measurement.arm = payload.arm
    measurement.leg = payload.leg
    measurement.note = payload.note.strip()
    db.commit()
    db.refresh(measurement)
    return measurement


@router.delete("/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_measurement(
    measurement_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    measurement = db.scalar(select(Measurement).where(Measurement.id == measurement_id, Measurement.user_id == current_user.id))
    if not measurement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Measurement not found")

    db.delete(measurement)
    db.commit()
