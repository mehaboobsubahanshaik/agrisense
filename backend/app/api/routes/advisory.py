from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db.models import SoilReport, User, YieldPrediction
from app.db.session import get_db
from app.schemas import CropRecommendIn, SoilIn, YieldIn
from app.services import agronomy

router = APIRouter(tags=["advisory"])


@router.post("/soil/analyze")
async def soil_analyze(body: SoilIn, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = agronomy.analyse_soil(
        body.crop, body.n, body.p, body.k, body.ph, body.oc, body.moisture, body.area_acres
    )
    db.add(
        SoilReport(
            user_id=user.id, crop=body.crop, n=body.n, p=body.p, k=body.k, ph=body.ph,
            oc=body.oc, moisture=body.moisture, score=result["score"], recommendation=result,
        )
    )
    await db.commit()
    return result


@router.post("/crop/recommend")
async def crop_recommend(body: CropRecommendIn, user: User = Depends(current_user)):
    return {
        "season": body.season,
        "recommendations": agronomy.recommend_crops(
            body.n, body.p, body.k, body.ph, body.rainfall_mm, body.season, body.irrigation, body.soil_type
        ),
    }


@router.post("/yield/predict")
async def yield_predict(body: YieldIn, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = agronomy.predict_yield(
        body.crop, body.area_acres, body.soil_score, body.rainfall_mm,
        body.irrigation, body.disease_pressure, body.fertilizer_applied,
    )
    db.add(
        YieldPrediction(
            user_id=user.id, crop=body.crop, area_acres=body.area_acres,
            predicted_quintals=result["total_quintals"], confidence=result["confidence"],
            factors=result["factors"],
        )
    )
    await db.commit()
    return result
