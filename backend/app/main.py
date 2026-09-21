"""SafePath AI demo API. Deterministic demo routes keep presentations functional offline."""
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated
import hashlib, os, secrets
import jwt
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash

app = FastAPI(title="SafePath AI", version="1.0.0", openapi_url="/api/v1/openapi.json", docs_url="/docs")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
password_hash = PasswordHash.recommended(); SECRET=os.getenv("JWT_SECRET", "demo-secret")
users: dict[str, dict] = {}; tokens: set[str] = set(); guardians: list[dict] = []; trips: dict[str, dict] = {}; sockets: dict[str, list[WebSocket]] = {}
class Role(str, Enum): traveller="traveller"; guardian="guardian"; admin="admin"
class Credentials(BaseModel): email: EmailStr; password: str = Field(min_length=8, max_length=128); name: str="SafePath User"; role: Role=Role.traveller
class Login(BaseModel): email: EmailStr; password: str
class RouteRequest(BaseModel): origin: str; destination: str
class TripStart(BaseModel): route_id: str; origin: str; destination: str; share_with: list[str]=[]
class Position(BaseModel): lat: float; lng: float
class Invite(BaseModel): email: EmailStr

def issue(email: str, minutes: int): return jwt.encode({"sub":email,"exp":datetime.now(timezone.utc)+timedelta(minutes=minutes)}, SECRET, algorithm="HS256")
def current(authorization: Annotated[str|None, __import__('fastapi').Header()] = None):
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401, "Authentication required")
    try: return jwt.decode(authorization[7:], SECRET, algorithms=["HS256"])["sub"]
    except jwt.PyJWTError: raise HTTPException(401, "Authentication required")
def auth(email):
    return {"access_token":issue(email,15),"refresh_token":issue(email,60*24*7),"token_type":"bearer","user":public(users[email])}
def public(user): return {k:v for k,v in user.items() if k not in {"password"}}
@app.get("/health")
def health(): return {"status":"ok","service":"safepath-api"}
@app.post("/api/v1/auth/register")
def register(body: Credentials):
    if body.email in users: raise HTTPException(400,"Unable to create account")
    users[body.email]={"id":secrets.token_hex(8),"email":body.email,"name":body.name,"role":body.role,"password":password_hash.hash(body.password)}; return auth(body.email)
@app.post("/api/v1/auth/login")
def login(body: Login):
    user=users.get(body.email)
    if not user or not password_hash.verify(body.password,user["password"]): raise HTTPException(401,"Invalid email or password")
    return auth(body.email)
@app.post("/api/v1/auth/refresh")
def refresh(refresh_token: str):
    try: email=jwt.decode(refresh_token,SECRET,algorithms=["HS256"])["sub"]; return auth(email)
    except jwt.PyJWTError: raise HTTPException(401,"Invalid refresh token")
@app.post("/api/v1/auth/logout")
def logout(): return {"ok":True}
@app.get("/api/v1/users/me")
def me(email=Depends(current)): return public(users[email])
@app.get("/api/v1/places/search")
def places_search(q:str): return [{"label":f"{q}, Demo Campus","lat":12.9716,"lng":77.5946}]
DEMO_GEOM=[[77.5946,12.9716],[77.5960,12.9730],[77.5983,12.9740]]
@app.post("/api/v1/routes/compare")
def compare(_:RouteRequest, email=Depends(current)):
    return {"data_source":"Demo data / Prototype","disclaimer":"Safety Scores are estimates from available data.","routes":[
      {"id":"fastest","label":"Fastest route","geometry":DEMO_GEOM,"eta_min":12,"distance_m":1100,"safety_score":41,"recommended":False,"confidence":"low_data","factors":{"lighting":20,"crime":55,"crowd":40,"emergency":58,"traffic":45},"why_safer":["Shorter route, but includes an unlit stretch","Limited open amenities nearby","Incident data is reports-only"]},
      {"id":"safest","label":"Safest route","geometry":[[77.5946,12.9716],[77.5936,12.9736],[77.5965,12.9752],[77.5983,12.9740]],"eta_min":16,"distance_m":1500,"safety_score":88,"recommended":True,"confidence":"high","factors":{"lighting":95,"crime":90,"crowd":86,"emergency":82,"traffic":78},"why_safer":["Well-lit roads with 8 street lamps","6 open shops and active amenities","Police booth approximately 150 m away"]}]}
@app.post("/api/v1/guardians/invite")
def invite(body:Invite,email=Depends(current)):
    guardians.append({"id":secrets.token_hex(6),"traveller":email,"guardian":str(body.email),"status":"pending"}); return guardians[-1]
@app.get("/api/v1/guardians")
def guardian_list(email=Depends(current)): return [x for x in guardians if email in (x["traveller"],x["guardian"])]
@app.post("/api/v1/guardians/accept")
def accept(id:str,email=Depends(current)):
    link=next((x for x in guardians if x["id"]==id and x["guardian"]==email),None)
    if not link: raise HTTPException(404,"Invitation not found")
    link["status"]="active"; return link
@app.delete("/api/v1/guardians/{id}")
def revoke(id:str,email=Depends(current)):
    link=next((x for x in guardians if x["id"]==id and x["traveller"]==email),None)
    if not link: raise HTTPException(404,"Guardian link not found")
    link["status"]="revoked"; return {"ok":True}
@app.post("/api/v1/trips")
def start_trip(body:TripStart,email=Depends(current)):
    tid=secrets.token_hex(8); trips[tid]={"id":tid,"traveller":email,"status":"active","route_id":body.route_id,"origin":body.origin,"destination":body.destination,"events":[{"type":"start","at":datetime.now(timezone.utc).isoformat()}],"position":None}; return trips[tid]
@app.get("/api/v1/trips/active")
def active(email=Depends(current)): return [t for t in trips.values() if t["traveller"]==email and t["status"]=="active"]
@app.get("/api/v1/trips/{id}")
def trip(id:str,email=Depends(current)):
    if id not in trips: raise HTTPException(404,"Trip not found")
    return trips[id]
@app.post("/api/v1/trips/{id}/checkin")
def checkin(id:str,email=Depends(current)): trips[id]["events"].append({"type":"checkin"}); return {"status":"on_route"}
@app.post("/api/v1/trips/{id}/end")
def end(id:str,email=Depends(current)): trips[id]["status"]="completed"; return trips[id]
@app.post("/api/v1/trips/{id}/sos")
async def sos(id:str,email=Depends(current)):
    trips[id]["status"]="sos"; trips[id]["events"].append({"type":"sos"})
    for ws in sockets.get(id,[]): await ws.send_json({"type":"sos","message":"SOS alert sent to connected guardians"})
    return {"status":"sos","message":"SOS alert created. Contact local emergency services if needed."}
@app.post("/api/v1/trips/{id}/safe")
def safe(id:str,email=Depends(current)): trips[id]["events"].append({"type":"safe"}); return {"status":"on_route"}
@app.post("/api/v1/reports")
def report(body:dict,email=Depends(current)): return {"id":secrets.token_hex(6),"status":"pending","message":"Report received for review"}
@app.get("/api/v1/reports/nearby")
def reports(): return []
@app.get("/api/v1/admin/hotspots")
def hotspots(email=Depends(current)): return [{"lat":12.973,"lng":77.596,"count":3,"anonymised":True}]
@app.websocket("/api/v1/ws/trips/{id}")
async def ws(websocket:WebSocket,id:str):
    await websocket.accept(); sockets.setdefault(id,[]).append(websocket)
    try:
      while True:
        data=await websocket.receive_json(); trips.get(id,{}).update(position=data)
        for client in sockets[id]:
          if client != websocket: await client.send_json({"type":"position","position":data})
    except WebSocketDisconnect: sockets[id].remove(websocket)
