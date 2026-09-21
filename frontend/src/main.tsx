import { FormEvent, useState } from "react";
import { createRoot } from "react-dom/client";
import { AlertTriangle, MapPin, Navigation, Shield } from "lucide-react";
import "./style.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

type Route = { id: string; label: string; safety_score: number; eta_min: number; distance_m: number; recommended: boolean; factors: Record<string, number>; why_safer: string[]; confidence: string };
type Trip = { id: string; status: string };
type AuthResponse = { access_token: string };
type RequestOptions = Omit<RequestInit, "headers"> & { headers?: Record<string, string> };

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Request failed";
}

function App() {
  const [token, setToken] = useState(localStorage.token || "");
  const [routes, setRoutes] = useState<Route[]>([]);
  const [trip, setTrip] = useState<Trip>();
  const [notice, setNotice] = useState("");

  const request = async <T,>(path: string, options: RequestOptions = {}): Promise<T> => {
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
    });
    if (!response.ok) {
      const body: unknown = await response.json().catch(() => ({}));
      const detail = typeof body === "object" && body !== null && "detail" in body && typeof body.detail === "string" ? body.detail : "Request failed";
      throw new Error(detail);
    }
    return response.json() as Promise<T>;
  };

  const register = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const response = await request<AuthResponse>("/auth/register", { method: "POST", body: JSON.stringify({ email: form.get("email"), password: form.get("password"), name: form.get("name") }) });
      localStorage.token = response.access_token;
      setToken(response.access_token);
    } catch (error: unknown) { setNotice(errorMessage(error)); }
  };

  if (!token) return <main className="auth"><Shield size={42}/><h1>SafePath <b>AI</b></h1><p>Not just the fastest route — the safest explainable route.</p><form onSubmit={register}><input name="name" placeholder="Your name" required/><input name="email" type="email" placeholder="Email" required/><input name="password" type="password" minLength={8} placeholder="Password (8+ characters)" required/><button>Create secure account</button></form><small>{notice || "Demo data / Prototype · Safety Scores are estimates from available data."}</small></main>;

  const compare = async () => {
    try { const response = await request<{ routes: Route[] }>("/routes/compare", { method: "POST", body: JSON.stringify({ origin: "Demo Campus Gate", destination: "Metro Station" }) }); setRoutes(response.routes); }
    catch (error: unknown) { setNotice(errorMessage(error)); }
  };
  const start = async (route: Route) => {
    try { setTrip(await request<Trip>("/trips", { method: "POST", body: JSON.stringify({ route_id: route.id, origin: "Demo Campus Gate", destination: "Metro Station" }) })); }
    catch (error: unknown) { setNotice(errorMessage(error)); }
  };
  const sos = async () => {
    try { await request(`/trips/${trip?.id}/sos`, { method: "POST" }); setNotice("SOS alert created. Contact local emergency services if needed."); }
    catch (error: unknown) { setNotice(errorMessage(error)); }
  };
  const checkIn = async () => {
    try { await request(`/trips/${trip?.id}/checkin`, { method: "POST" }); setNotice("Check-in recorded — glad you are safe."); }
    catch (error: unknown) { setNotice(errorMessage(error)); }
  };

  return <main><header><span><Shield/> SafePath <b>AI</b></span><em>Demo data / Prototype</em><button className="link" onClick={() => { localStorage.clear(); setToken(""); }}>Log out</button></header><section className="hero"><div><p className="eyebrow">SAFETY-FIRST NAVIGATION</p><h1>Your route. <i>Explained.</i> Protected.</h1><p>Compare safety signals before you leave, then share live protection with trusted guardians.</p><div className="search"><input value="Demo Campus Gate" readOnly/><input value="Metro Station" readOnly/><button onClick={compare}><Navigation/> Compare safe routes</button></div></div><div className="map"><MapPin/><strong>Live safety map</strong><span>Map tiles connect with MapTiler when configured.</span></div></section>{routes.length > 0 && !trip && <section><h2>Choose your route</h2><p className="disclaimer">Safety Scores are estimates from available data. Incident signal uses available reports only.</p><div className="cards">{routes.map((route) => <article className={route.recommended ? "card recommended" : "card"} key={route.id}>{route.recommended && <label>RECOMMENDED</label>}<div className="score">{route.safety_score}<small>/100 safety</small></div><h3>{route.label}</h3><p>{route.eta_min} min · {(route.distance_m / 1000).toFixed(1)} km</p><div className="bars">{Object.entries(route.factors).map(([name, value]) => <div key={name}><span>{name}</span><b style={{ width: `${value}%` }}/></div>)}</div><ul>{route.why_safer.map((reason) => <li key={reason}>✓ {reason}</li>)}</ul><small>{route.confidence === "low_data" ? "Low data: neutral values used where lighting data is missing." : "High confidence from demo POI coverage."}</small><button onClick={() => start(route)}>Start Safety Trip</button></article>)}</div></section>}{trip && <section className="trip"><p className="eyebrow">LIVE SAFETY TRIP · GUARDIAN SHARING OPT-IN</p><h2>Protection is active</h2><div className="status"><span>● Route monitoring on</span><span>◷ Check in every 5 minutes</span><span>⌁ Keep screen on for reliable background tracking</span></div><p>Your location is shared only for this trip. Browsers may throttle background tracking.</p><button onClick={checkIn}>I&apos;m safe · Check in</button><button className="sos" onClick={sos}><AlertTriangle/> SOS</button><p role="status">{notice}</p></section>}<footer>Implemented: route comparison & trip demo · Prototype: map/live notifications · Proposed: ML safety model</footer></main>;
}

createRoot(document.getElementById("root")!).render(<App/>);
