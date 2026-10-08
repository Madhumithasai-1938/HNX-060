import React, {useEffect, useState} from "react";
import {createRoot} from "react-dom/client";
import {ShieldCheck, LayoutDashboard, Users, MapPin, HeartHandshake, UserRoundPlus, Search, Bell, LogOut, Plus, CheckCircle2, XCircle, Navigation, Activity, Menu, X, AlertTriangle} from "lucide-react";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";
const api = async (path, options={}) => {
  const token = localStorage.getItem("safelink_token");
  const r = await fetch(API + path, {headers: {"Content-Type":"application/json", ...(token ? {Authorization:`Bearer ${token}`} : {}), ...(options.headers||{})}, ...options});
  if(!r.ok) { const e = await r.json().catch(()=>({detail:"Request failed"})); throw new Error(e.detail || "Request failed"); }
  return r.json();
};

function Logo({compact=false}) {
  return <div className="logo"><div className="logo-mark"><ShieldCheck size={compact?21:27}/></div>{!compact && <div><b>Safe<span>Link</span></b><small>Reunite • Rescue • Respond</small></div>}</div>
}

function Card({children, className=""}) { return <div className={"card "+className}>{children}</div> }
function Stat({icon, value, label}) { return <Card className="stat"><div className="stat-icon">{icon}</div><div><strong>{value}</strong><span>{label}</span></div></Card> }

const emptyFamily={family_name:"",home_address:"",emergency_contact:"",members:[{full_name:"",relationship:"",age:"",gender:"",phone:"",email:""}]};
const emptyRescue={full_name:"",age:"",gender:"",phone:"",email:"",family_name:"",rescue_location:"",current_location:"",status:"SAFE_AT_SHELTER"};
const emptyVolunteer={full_name:"",phone:"",skills:"",location:"",availability:"AVAILABLE"};

function Dashboard({stats}) {
  return <><div className="page-head"><div><h1>Community Rescue Dashboard</h1><p>Monitor rescued people, family matching and volunteer response in one place.</p></div><div className="live"><i/> System Operational</div></div>
    <div className="stats-grid">
      <Stat icon={<Users/>} value={stats.families} label="Registered Families"/>
      <Stat icon={<MapPin/>} value={stats.rescued} label="Rescued People"/>
      <Stat icon={<HeartHandshake/>} value={stats.volunteers} label="Active Volunteers"/>
      <Stat icon={<Activity/>} value={stats.pending_matches} label="Pending Matches"/>
    </div>
    <Card className="hero-card"><div><span className="eyebrow">DISASTER RESPONSE NETWORK</span><h2>Bring families back together.</h2><p>Family ID connects people before a disaster. Community ID follows rescued people across shelters. AI-assisted matching helps response teams find possible relatives safely.</p></div><div className="hero-orbit"><ShieldCheck size={72}/><span>FAMILY<br/>REUNIFICATION</span></div></Card>
    <div className="grid2"><Card><h3>How SafeLink works</h3><div className="steps"><div><b>01</b><span><strong>Family ID</strong> — register members and relationships.</span></div><div><b>02</b><span><strong>Community ID</strong> — register each rescued person.</span></div><div><b>03</b><span><strong>AI matching</strong> — compare registered family profiles.</span></div><div><b>04</b><span><strong>Verification</strong> — authorized staff confirm a match.</span></div></div></Card>
    <Card><h3>Response principle</h3><div className="principle"><div>Family ID <span>→</span> Who belongs together</div><div>Community ID <span>→</span> Where they are</div><div>Volunteer ID <span>→</span> Who can help</div><div>Verification <span>→</span> Safe reunification</div></div></Card></div>
  </>
}

function Form({children,onSubmit,title,subtitle}) {return <Card><h3>{title}</h3><p className="muted">{subtitle}</p><form onSubmit={onSubmit}>{children}</form></Card>}
function Input({label,...p}) {return <label className="field"><span>{label}</span><input {...p}/></label>}
function Select({label,children,...p}) {return <label className="field"><span>{label}</span><select {...p}>{children}</select></label>}

function Families() {
  const [families,setFamilies]=useState([]), [form,setForm]=useState(emptyFamily), [show,setShow]=useState(false), [msg,setMsg]=useState("");
  const load=()=>api("/families").then(setFamilies); useEffect(load,[]);
  const submit=async e=>{e.preventDefault(); try{await api("/families",{method:"POST",body:JSON.stringify({...form,members:form.members.map(m=>({...m,age:m.age?Number(m.age):null}))})});setMsg("Family ID created successfully.");setForm(emptyFamily);setShow(false);load()}catch(x){setMsg(x.message)}};
  const updateMember=(i,k,v)=>setForm(f=>({...f,members:f.members.map((m,n)=>n===i?{...m,[k]:v}:m)}));
  return <><div className="page-head"><div><h1>Family Registry</h1><p>Create a Family ID and connect every member before a disaster.</p></div><button className="primary" onClick={()=>setShow(true)}><Plus size={18}/> New Family ID</button></div>
    {msg&&<div className="notice">{msg}</div>}
    {show&&<Form title="Create Family ID" subtitle="Add household details and the people who belong together." onSubmit={submit}>
      <div className="formgrid"><Input label="Family name" required value={form.family_name} onChange={e=>setForm({...form,family_name:e.target.value})}/><Input label="Emergency contact" value={form.emergency_contact} onChange={e=>setForm({...form,emergency_contact:e.target.value})}/><Input label="Home address" value={form.home_address} onChange={e=>setForm({...form,home_address:e.target.value})}/></div>
      <h4>Family members</h4>{form.members.map((m,i)=><div className="member-row" key={i}><Input label="Full name" required value={m.full_name} onChange={e=>updateMember(i,"full_name",e.target.value)}/><Input label="Relationship" required placeholder="Father / Mother / Child" value={m.relationship} onChange={e=>updateMember(i,"relationship",e.target.value)}/><Input label="Age" type="number" value={m.age} onChange={e=>updateMember(i,"age",e.target.value)}/><Input label="Phone" value={m.phone} onChange={e=>updateMember(i,"phone",e.target.value)}/></div>)}
      <div className="actions"><button type="button" className="ghost" onClick={()=>setShow(false)}>Cancel</button><button className="primary">Create Family ID</button></div>
    </Form>}
    <Card><div className="table-head"><h3>Registered families</h3><span>{families.length} families</span></div><div className="table-wrap"><table><thead><tr><th>Family ID</th><th>Family</th><th>Members</th><th>Emergency Contact</th></tr></thead><tbody>{families.map(f=><tr key={f.id}><td><code>{f.family_id}</code></td><td><b>{f.family_name}</b></td><td>{f.members.map(x=><span className="tag" key={x.id}>{x.full_name} · {x.relationship}</span>)}</td><td>{f.emergency_contact||"—"}</td></tr>)}</tbody></table></div></Card>
  </>
}

function Rescue() {
  const [people,setPeople]=useState([]), [form,setForm]=useState(emptyRescue), [show,setShow]=useState(false), [selected,setSelected]=useState(null), [movement,setMovement]=useState({location:"",note:""});
  const load=()=>api("/rescue").then(setPeople); useEffect(load,[]);
  const submit=async e=>{e.preventDefault();await api("/rescue",{method:"POST",body:JSON.stringify({...form,age:form.age?Number(form.age):null})});setForm(emptyRescue);setShow(false);load()};
  const move=async e=>{e.preventDefault();await api(`/rescue/${selected.community_id}/movement`,{method:"POST",body:JSON.stringify({...movement,verified:true})});setMovement({location:"",note:""});load();api(`/rescue/${selected.community_id}`).then(setSelected)};
  return <><div className="page-head"><div><h1>Community ID Registry</h1><p>Track rescued people, current shelter location and verified movement history.</p></div><button className="primary" onClick={()=>setShow(true)}><Plus size={18}/> Register Rescued Person</button></div>
    {show&&<Form title="Create Community ID" subtitle="Register a rescued person at a shelter, hospital or relief centre." onSubmit={submit}>
      <div className="formgrid"><Input label="Full name" required value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}/><Input label="Age" type="number" value={form.age} onChange={e=>setForm({...form,age:e.target.value})}/><Input label="Family name" value={form.family_name} onChange={e=>setForm({...form,family_name:e.target.value})}/><Input label="Phone" value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})}/><Input label="Rescue location" required value={form.rescue_location} onChange={e=>setForm({...form,rescue_location:e.target.value})}/><Input label="Current shelter / centre" required value={form.current_location} onChange={e=>setForm({...form,current_location:e.target.value})}/><Select label="Status" value={form.status} onChange={e=>setForm({...form,status:e.target.value})}><option>SAFE_AT_SHELTER</option><option>HOSPITAL</option><option>TRANSFERRED</option><option>REUNITED</option></Select></div>
      <div className="actions"><button type="button" className="ghost" onClick={()=>setShow(false)}>Cancel</button><button className="primary">Create Community ID & Match</button></div>
    </Form>}
    <div className="search"><Search size={18}/><input placeholder="Search name, Community ID or family name..." onChange={async e=>setPeople(await api("/rescue?search="+encodeURIComponent(e.target.value)))}/></div>
    <div className="people-grid">{people.map(p=><Card className="person-card" key={p.community_id}><div className="person-top"><div className="avatar">{p.full_name?.[0]}</div><div><h3>{p.full_name}</h3><code>{p.community_id}</code></div><span className={"status "+(p.status==="REUNITED"?"good":"")}>{p.status.replaceAll("_"," ")}</span></div><div className="details"><span><MapPin size={15}/>{p.current_location}</span><span><Navigation size={15}/>{p.rescue_location}</span><span><Users size={15}/>Family: {p.family_name||"Unknown"}</span></div><button className="secondary full" onClick={()=>api(`/rescue/${p.community_id}`).then(setSelected)}>View history & matches</button></Card>)}</div>
    {selected&&<div className="modal"><div className="modal-box"><button className="close" onClick={()=>setSelected(null)}><X/></button><span className="eyebrow">COMMUNITY ID</span><h2>{selected.full_name}</h2><code>{selected.community_id}</code><h4>Movement history</h4>{selected.movements.map((m,i)=><div className="timeline" key={i}><i/><div><b>{m.location}</b><small>{new Date(m.moved_at).toLocaleString()} · {m.verified?"Verified":"Unverified"}</small><p>{m.note}</p></div></div>)}<h4>AI-assisted possible family matches</h4>{selected.matches?.length?<div className="match-list">{selected.matches.map(m=><div className="match" key={m.id}><div><b>{m.member_name}</b><span>{m.family_id} · {m.family_name} · {m.relationship}</span><small>{m.reasons}</small></div><strong>{m.score}%</strong></div>)}</div>:<p className="muted">No possible match above the matching threshold.</p>}<form onSubmit={move} className="move-form"><Input label="Move to shelter / centre" required value={movement.location} onChange={e=>setMovement({...movement,location:e.target.value})}/><Input label="Note" value={movement.note} onChange={e=>setMovement({...movement,note:e.target.value})}/><button className="primary"><Navigation size={16}/> Record verified movement</button></form></div></div>}
  </>
}

function Matches() {
  const [matches,setMatches]=useState([]); const load=()=>api("/matches?status=PENDING").then(setMatches); useEffect(load,[]);
  const act=async(id,action)=>{await api(`/matches/${id}`,{method:"PATCH",body:JSON.stringify({action,verified_by:"admin"})});load()};
  return <><div className="page-head"><div><h1>AI Match Verification</h1><p>Review possible family relationships before any reunification action.</p></div></div><Card><div className="alert"><AlertTriangle size={19}/><span>AI suggestions are not proof of identity. Authorized personnel must verify the relationship before reunification.</span></div>{matches.length===0?<div className="empty"><CheckCircle2 size={35}/><h3>No pending matches</h3><p>New possible matches will appear here.</p></div>:<div className="match-list big">{matches.map(m=><div className="match" key={m.id}><div><span className="eyebrow">COMMUNITY {m.community_id}</span><b>{m.member_name} ↔ rescued person</b><span>Family {m.family_id} · {m.family_name} · {m.relationship}</span><small>{m.reasons}</small></div><div className="match-actions"><strong>{m.score}%</strong><button className="approve" onClick={()=>act(m.id,"VERIFY")}><CheckCircle2 size={16}/> Verify</button><button className="reject" onClick={()=>act(m.id,"REJECT")}><XCircle size={16}/> Reject</button></div></div>)}</div>}</Card></>
}

function Volunteers() {
  const [list,setList]=useState([]),[form,setForm]=useState(emptyVolunteer),[show,setShow]=useState(false); const load=()=>api("/volunteers").then(setList);useEffect(load,[]);
  const submit=async e=>{e.preventDefault();await api("/volunteers",{method:"POST",body:JSON.stringify(form)});setForm(emptyVolunteer);setShow(false);load()};
  return <><div className="page-head"><div><h1>Volunteer Network</h1><p>Use skill-based Volunteer IDs to coordinate rescue, medical and logistics support.</p></div><button className="primary" onClick={()=>setShow(true)}><UserRoundPlus size={18}/> Register Volunteer</button></div>{show&&<Form title="Create Volunteer ID" subtitle="Register skills so response coordinators can allocate the right people." onSubmit={submit}><div className="formgrid"><Input label="Full name" required value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})}/><Input label="Phone" value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})}/><Input label="Skills" required placeholder="Medical, First Aid, Logistics" value={form.skills} onChange={e=>setForm({...form,skills:e.target.value})}/><Input label="Location" value={form.location} onChange={e=>setForm({...form,location:e.target.value})}/><Select label="Availability" value={form.availability} onChange={e=>setForm({...form,availability:e.target.value})}><option>AVAILABLE</option><option>BUSY</option><option>OFFLINE</option></Select></div><div className="actions"><button type="button" className="ghost" onClick={()=>setShow(false)}>Cancel</button><button className="primary">Create Volunteer ID</button></div></Form>}<div className="vol-grid">{list.map(v=><Card className="vol-card" key={v.volunteer_id}><div className="vol-avatar"><UserRoundPlus/></div><div><code>{v.volunteer_id}</code><h3>{v.full_name}</h3><p>{v.location||"Location not specified"}</p><div>{v.skills.split(",").map(s=><span className="tag" key={s}>{s.trim()}</span>)}</div></div><span className={"status "+(v.availability==="AVAILABLE"?"good":"")}>{v.availability}</span></Card>)}</div></>
}

function AuthPage({onAuth}) {
  const [mode,setMode]=useState("signin"), [name,setName]=useState(""), [email,setEmail]=useState(""), [password,setPassword]=useState(""), [error,setError]=useState(""), [loading,setLoading]=useState(false);
  const submit=async e=>{e.preventDefault();setError("");setLoading(true);try{
    const data=await api(mode==="signin"?"/auth/signin":"/auth/signup",{method:"POST",body:JSON.stringify(mode==="signin"?{email,password}:{full_name:name,email,password})});
    localStorage.setItem("safelink_token",data.token); localStorage.setItem("safelink_user",JSON.stringify(data.user)); onAuth(data.user);
  }catch(x){setError(x.message)}finally{setLoading(false)}};
  return <div className="auth-page"><div className="auth-visual"><div className="auth-brand"><Logo/><span className="auth-pill"><i/> Disaster response network</span></div><div className="auth-copy"><span className="eyebrow">SAFE RESPONSE • FAMILY REUNIFICATION</span><h1>Bring families back together.</h1><p>SafeLink connects Family IDs, Community IDs, volunteers and verified AI-assisted matches in one secure response network.</p><div className="auth-points"><span><ShieldCheck size={17}/> Secure local access</span><span><HeartHandshake size={17}/> Verified reunification</span><span><MapPin size={17}/> Rescue location tracking</span></div></div></div><div className="auth-panel"><div className="auth-box"><div className="auth-mobile-logo"><Logo/></div><span className="auth-kicker">SAFELINK PORTAL</span><h2>{mode==="signin"?"Welcome back":"Create your account"}</h2><p className="muted">{mode==="signin"?"Sign in to access the disaster response dashboard.":"Register an authorized response account to continue."}</p>{error&&<div className="auth-error"><AlertTriangle size={16}/>{error}</div>}<form onSubmit={submit} className="auth-form">{mode==="signup"&&<Input label="Full name" required value={name} onChange={e=>setName(e.target.value)} placeholder="Your name"/>}<Input label="Email address" type="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com"/><Input label="Password" type="password" minLength={6} required value={password} onChange={e=>setPassword(e.target.value)} placeholder="Minimum 6 characters"/><button className="primary full auth-submit" disabled={loading}>{loading?"Please wait...":mode==="signin"?"Sign In":"Create Account"}</button></form><div className="auth-switch">{mode==="signin"?<>New to SafeLink? <button onClick={()=>{setMode("signup");setError("")}}>Create an account</button></>:<>Already have an account? <button onClick={()=>{setMode("signin");setError("")}}>Sign in</button></>}</div><div className="auth-note"><ShieldCheck size={15}/> Your account is stored in the local SafeLink PostgreSQL database.</div></div></div></div>
}

function App(){
  const [page,setPage]=useState("dashboard"),[stats,setStats]=useState({families:0,rescued:0,volunteers:0,pending_matches:0,reunited:0}),[mobile,setMobile]=useState(false),[user,setUser]=useState(null),[checking,setChecking]=useState(true);
  const refresh=()=>api("/dashboard").then(setStats).catch(()=>{});
  useEffect(()=>{const token=localStorage.getItem("safelink_token"); if(!token){setChecking(false);return;} api("/auth/me").then(u=>setUser(u)).catch(()=>{localStorage.removeItem("safelink_token");localStorage.removeItem("safelink_user")}).finally(()=>setChecking(false));},[]);
  useEffect(()=>{if(user){refresh();api("/demo/seed").then(refresh).catch(()=>{})}},[user]);
  const signout=async()=>{try{await api("/auth/signout",{method:"POST"})}catch{} localStorage.removeItem("safelink_token");localStorage.removeItem("safelink_user");setUser(null)};
  if(checking)return <div className="loading-screen"><Logo/><p>Loading SafeLink...</p></div>;
  if(!user)return <AuthPage onAuth={setUser}/>;
  const nav=[["dashboard","Dashboard",<LayoutDashboard/>],["families","Family IDs",<Users/>],["rescue","Community IDs",<MapPin/>],["matches","Match Verification",<HeartHandshake/>],["volunteers","Volunteer IDs",<UserRoundPlus/>]];
  const content=page==="dashboard"?<Dashboard stats={stats}/>:page==="families"?<Families/>:page==="rescue"?<Rescue/>:page==="matches"?<Matches/>:<Volunteers/>;
  return <div className="app"><aside className={mobile?"open":""}><div className="brand"><Logo/><button onClick={()=>setMobile(false)}><X/></button></div><nav>{nav.map(([id,label,icon])=><button className={page===id?"active":""} onClick={()=>{setPage(id);setMobile(false)}} key={id}>{icon}<span>{label}</span></button>)}</nav><div className="side-bottom"><div className="admin"><div className="admin-avatar">{user.full_name?.[0]?.toUpperCase()||"U"}</div><div><b>{user.full_name}</b><small>{user.role}</small></div></div><button className="signout" onClick={signout}><LogOut size={14}/> Sign Out</button></div></aside><main><header><button className="mobile-menu" onClick={()=>setMobile(true)}><Menu/></button><Logo compact/><div className="header-right"><span className="disaster"><i/> Disaster mode ready</span><Bell size={20}/><div className="header-user">{user.full_name?.[0]?.toUpperCase()||"U"}</div><button className="header-signout" onClick={signout}><LogOut size={16}/> Sign Out</button></div></header><div className="content">{content}</div><footer>SafeLink • Disaster Family Reunification & Community Rescue Network • Prototype</footer></main></div>
}
createRoot(document.getElementById("root")).render(<App/>);
