from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_health(): assert client.get('/health').json()['status']=='ok'
def test_route_demo():
 r=client.post('/api/v1/auth/register',json={'email':'test@example.com','password':'password123'}).json()
 routes=client.post('/api/v1/routes/compare',headers={'Authorization':'Bearer '+r['access_token']},json={'origin':'A','destination':'B'}).json()['routes']
 assert [x['safety_score'] for x in routes]==[41,88]
