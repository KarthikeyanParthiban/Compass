from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from monte_carlo import get_management_data, get_available_profiles
import uvicorn

app = FastAPI(title="Portfolio Compass API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/profiles")
async def list_profiles():
    return {"status": "success", "data": get_available_profiles()}

@app.get("/simulate")
async def simulate(
    profile_id:  str = Query("sample"),
    iterations:  int = Query(1000, ge=100,  le=10000),
    days:        int = Query(252,  ge=30,   le=1825),
    confidence:  int = Query(95,   ge=50,   le=99),
):
    try:
        result = get_management_data(
            profile_id=profile_id,
            num_sims=iterations,
            days=days,
            confidence_level=confidence,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
