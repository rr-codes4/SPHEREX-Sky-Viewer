from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from astroquery.ipac.irsa import Irsa
import astropy.units as u
from astropy.coordinates import SkyCoord

app = FastAPI(title="SPHEREx Sky Viewer Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "online", "project": "SPHEREx Sky Viewer API", "message": "Backend is running!"}

@app.get("/api/query")
def query_sky_data(
    ra: float = Query(269.452, description="Right Ascension in degrees (default: Barnard's Star)"),
    dec: float = Query(4.693, description="Declination in degrees"),
    radius: float = Query(0.01, description="Search radius in degrees")
):
    try:
        # Format coordinates using Astropy
        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame='icrs')
        
        # Query NASA IRSA using SIA2 / image cutout service capabilities
        images = Irsa.query_sia(pos=coord, size=radius * u.deg)
        
        results = []
        if images is not None and len(images) > 0:
            for row in images[:5]: # Limit to top 5 results for speed
                access_url = row['access_url'] if 'access_url' in images.colnames else None
                results.append({
                    "access_url": access_url,
                    "target_ra": ra,
                    "target_dec": dec
                })
                
        return {
            "status": "success", 
            "count": len(results), 
            "data": results
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
        }