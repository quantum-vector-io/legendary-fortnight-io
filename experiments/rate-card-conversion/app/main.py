from fastapi import FastAPI, File, HTTPException, UploadFile

from app.config import settings
from app.extractors import UnsupportedFormatError, load_rate_card
from app.pipeline import convert_dataframe
from app.schemas import ConversionResponse

app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(f"{settings.api_prefix}/convert-rate-card", response_model=ConversionResponse)
async def convert_rate_card(file: UploadFile = File(...)) -> ConversionResponse:
    content = await file.read()
    try:
        raw_df = load_rate_card(file.filename, content)
    except UnsupportedFormatError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if raw_df.empty:
        raise HTTPException(status_code=400, detail="No records found in input")

    return convert_dataframe(raw_df)
