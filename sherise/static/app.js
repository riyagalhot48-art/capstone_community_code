const { useState, useEffect } = React;
const h = htm.bind(React.createElement);

async function api(path, o = {}) {
  const t = localStorage.getItem('token');
  const r = await fetch('/api' + path, { method: o.method || 'GET', headers: { 'Content-Type': 'application/json', ...(t ? { Authorization: 'Bearer ' + t } : {}) }, body: o.body ? JSON.stringify(o.body) : undefined });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || 'Something went wrong. Try again.');
  return j;
}
function useData(fn, deps) {
  const [d, setD] = useState(null), [e, setE] = useState('');
  useEffect(() => { setD(null); setE(''); fn().then(setD).catch(x => setE(x.message)); }, deps);
  return [d, e, setD];
}
const Chips = ({ list, cls }) => h`<div className="chips">${list.map(s => h`<span key=${s} className=${'chip ' + (cls || '')}>${s}</span>`)}</div>`;
const Load = ({ d, e }) => e ? h`<p className="err">${e}</p>` : (!d ? h`<p className="mute">Loading…</p>` : null);

function Home({ user }) {
  const [s] = useData(() => api('/stats'), []);
  const steps = [['Assess', 'Short skill tests with scoring'], ['Find the gap', 'Compare your skills with what jobs need'], ['Recommend', 'Ranked jobs, internships and courses'], ['Learn & connect', 'Free courses and mentor matching'], ['Track', 'A dashboard shows your progress']];
  return h`<div>
    <div className="hero"><div className="wrap">
      <h1>Learn the skill. Find the job. Find your mentor.</h1>
      <p>Many women cannot see which skills they are missing, so opportunities stay out of reach. SheRise turns one skill test into a personal learning and career path.</p>
      <a className="btn light" href=${user ? '#assess' : '#auth'}>${user ? 'Take a skill test' : 'Create your free profile'}</a>
    </div></div>
    <div className="wrap main">
      <h2>How SheRise works</h2>
      <ol className="steps">${steps.map(([a, b]) => h`<li key=${a}><b>${a}</b><span>${b}</span></li>`)}</ol>
      ${s && h`<div className="grid">${[['profiles', 'Profiles created'], ['assessments', 'Assessments completed'], ['courses_finished', 'Courses finished'], ['applications', 'Opportunities applied for'], ['mentor_sessions', 'Mentor sessions held']].map(([k, l]) => h`<div className="card" key=${k}><div className="num">${s[k]}</div>${l}</div>`)}</div>`}
      <div className="sdg"><b>Our goal: SDG 5, Gender Equality.</b> We also support SDG 4 (Quality Education) and SDG 8 (Decent Work). Built by Team Code Divas, KRMU.</div>
    </div></div>`;
}

function Auth({ onAuth }) {
  const [mode, setMode] = useState('login'), [err, setErr] = useState(''), [busy, setBusy] = useState(false);
  const [f, setF] = useState({ name: '', email: '', password: '', role: 'learner', skills: [] });
  const [all] = useData(() => api('/skills'), []);
  const set = (k, v) => setF({ ...f, [k]: v });
  const toggle = s => set('skills', f.skills.includes(s) ? f.skills.filter(x => x !== s) : [...f.skills, s]);
  const submit = async e => {
    e.preventDefault(); setBusy(true); setErr('');
    try { onAuth(await api(mode === 'login' ? '/login' : '/register', { method: 'POST', body: f })); } catch (x) { setErr(x.message); }
    setBusy(false);
  };
  return h`<div className="wrap main narrow">
    <h2>${mode === 'login' ? 'Sign in' : 'Create your profile'}</h2>
    <form onSubmit=${submit}>
      ${mode === 'register' && h`<label>Full name<input required value=${f.name} onInput=${e => set('name', e.target.value)} autoComplete="name"/></label>`}
      <label>Email<input type="email" required value=${f.email} onInput=${e => set('email', e.target.value)} autoComplete="email"/></label>
      <label>Password${mode === 'register' ? ' (8+ characters)' : ''}<input type="password" required minLength=${mode === 'register' ? 8 : 1} value=${f.password} onInput=${e => set('password', e.target.value)} autoComplete=${mode === 'login' ? 'current-password' : 'new-password'}/></label>
      ${mode === 'register' && h`<label>I want to join as<select value=${f.role} onChange=${e => set('role', e.target.value)}><option value="learner">Learner / job seeker</option><option value="mentor">Mentor / volunteer</option></select></label>
        <div><b>${f.role === 'mentor' ? 'Skills you can mentor in' : 'Skills you already have'}</b>
        <div className="checks">${(all || []).map(s => h`<label key=${s}><input type="checkbox" checked=${f.skills.includes(s)} onChange=${() => toggle(s)}/>${s}</label>`)}</div></div>`}
      <div className="err" role="alert">${err}</div>
      <button className="btn" disabled=${busy}>${busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create profile'}</button>
    </form>
    <p>${mode === 'login' ? 'New here? ' : 'Already have an account? '}<a href="#auth" onClick=${e => { e.preventDefault(); setMode(mode === 'login' ? 'register' : 'login'); setErr(''); }}>${mode === 'login' ? 'Create a profile' : 'Sign in'}</a></p></div>`;
}

function Dashboard({ user }) {
  const [p, e] = useData(() => api('/progress/' + user.id), []);
  const [recs] = useData(() => api('/recommend/' + user.id), []);
  const learn = recs ? [...new Set(recs.filter(r => r.type !== 'course').slice(0, 3).flatMap(r => r.skill_gap))] : [];
  return h`<div className="wrap main"><h2>Welcome, ${user.name.split(' ')[0]}</h2>
    <${Load} d=${p} e=${e}/>
    ${p && h`<div className="card"><b>Your progress: ${p.progress}%</b><div className="bar" role="progressbar" aria-valuenow=${p.progress} aria-valuemin="0" aria-valuemax="100"><i style=${{ width: p.progress + '%' }}></i></div></div>
      <div className="grid" style=${{ marginTop: 16 }}>${[['skills_verified', 'Skills verified'], ['assessments_taken', 'Assessments taken'], ['courses_finished', 'Courses finished'], ['applications', 'Applications'], ['mentor_sessions', 'Mentor sessions']].map(([k, l]) => h`<div className="card" key=${k}><div className="num">${p[k]}</div>${l}</div>`)}</div>`}
    <h3 style=${{ marginTop: 28 }}>Your skills</h3>
    ${user.skills.length ? h`<${Chips} list=${user.skills} cls="ok"/>` : h`<p className="mute">No skills yet. Take a skill test to add verified skills.</p>`}
    <h3>Skills to learn next</h3>
    ${learn.length ? h`<${Chips} list=${learn} cls="gap"/>` : h`<p className="mute">${recs ? 'Nothing missing for your top matches. Great work!' : 'Loading…'}</p>`}
    <div className="row"><a className="btn" href="#assess">Take a skill test</a><a className="btn alt" href="#opportunities">See opportunities</a><a className="btn alt" href="#mentors">Find a mentor</a></div></div>`;
}

function Assess({ user, setUser, say }) {
  const [skills] = useData(() => api('/skills'), []);
  const [scores, , setScores] = useData(() => api('/assessments'), []);
  const [skill, setSkill] = useState(null), [qs, setQs] = useState([]), [ans, setAns] = useState({}), [res, setRes] = useState(null);
  const start = async s => { setSkill(s); setRes(null); setAns({}); try { setQs(await api('/questions/' + encodeURIComponent(s))); } catch (x) { say(x.message); } };
  const submit = async e => {
    e.preventDefault();
    try { const r = await api('/assess', { method: 'POST', body: { skill, answers: ans } }); setRes(r); setUser(r.user); setScores({ ...scores, [skill]: Math.max(scores?.[skill] || 0, r.score) }); } catch (x) { say(x.message); }
  };
  if (skill) return h`<div className="wrap main narrow"><h2>${skill} test</h2>
    ${res ? h`<div className="card"><div className="num">${res.score}%</div><p>${res.passed ? `You passed. ${skill} is now verified on your profile.` : `You got ${res.correct} of ${res.total}. You need ${67}% to verify this skill. Study and try again.`}</p>
      <div className="row"><button className="btn" onClick=${() => start(skill)}>Try again</button><button className="btn alt" onClick=${() => setSkill(null)}>All skills</button><a className="btn alt" href="#opportunities">See matches</a></div></div>`
      : h`<form onSubmit=${submit}>${qs.map(q => h`<fieldset className="q" key=${q.i}><legend>${q.q}</legend>${q.options.map(o => h`<label key=${o}><input type="radio" name=${'q' + q.i} required checked=${ans[q.i] === o} onChange=${() => setAns({ ...ans, [q.i]: o })}/>${o}</label>`)}</fieldset>`)}
      <div className="row"><button className="btn">Submit answers</button><button type="button" className="btn alt" onClick=${() => setSkill(null)}>Back</button></div></form>`}</div>`;
  return h`<div className="wrap main"><h2>Skill assessments</h2><p className="mute">Each test has 3 questions. Score ${67}% or more to verify a skill.</p>
    <div className="grid">${(skills || []).map(s => h`<div className="card" key=${s}><h3>${s}</h3>
      ${user.skills.includes(s) ? h`<span className="chip ok">On your profile</span>` : ''} ${scores && scores[s] !== undefined ? h`<span className="chip">Best score ${scores[s]}%</span>` : ''}
      <p><button className="btn sm" onClick=${() => start(s)}>${scores && scores[s] !== undefined ? 'Retake' : 'Start test'}</button></p></div>`)}</div></div>`;
}

function Opps({ user, say }) {
  const [type, setType] = useState('');
  const [d, e, setD] = useData(() => api(`/recommend/${user.id}` + (type ? '?type=' + type : '')), [type]);
  const track = async (o, kind) => {
    try { await api('/track', { method: 'POST', body: { opportunity_id: o.id, kind } }); say(kind === 'applied' ? 'Marked as applied.' : 'Course marked complete.'); setD(d.map(x => x.id === o.id ? { ...x, [kind === 'applied' ? 'applied' : 'course_done']: true } : x)); } catch (x) { say(x.message); }
  };
  const tabs = [['', 'All'], ['job', 'Jobs'], ['internship', 'Internships'], ['course', 'Courses']];
  return h`<div className="wrap main"><h2>Opportunities for you</h2><p className="mute">Ranked by how well your skills match. Add skills with tests to raise your match.</p>
    <div className="tabs">${tabs.map(([v, l]) => h`<button key=${v} className=${type === v ? 'on' : ''} onClick=${() => setType(v)}>${l}</button>`)}</div>
    <${Load} d=${d} e=${e}/>
    <div className="grid">${(d || []).map(o => h`<div className="card" key=${o.id}>
      <span className="chip">${o.type}</span><h3 style=${{ marginTop: 8 }}>${o.title}</h3><div className="mute">${o.org}</div>
      <p>${o.description}</p><b>Match ${o.match}%</b><div className="bar"><i style=${{ width: o.match + '%' }}></i></div>
      ${o.skill_gap.length ? h`<div className="mute" style=${{ marginTop: 8 }}>Learn:</div><${Chips} list=${o.skill_gap} cls="gap"/>` : h`<p className="chip ok">Nothing missing</p>`}
      <div className="row">${o.link && h`<a className="btn sm" href=${o.link} target="_blank" rel="noopener noreferrer">${o.type === 'course' ? 'Open course' : 'Open listing'}</a>`}
      ${o.type === 'course' ? (o.course_done ? h`<span className="chip ok">Completed</span>` : h`<button className="btn sm alt" onClick=${() => track(o, 'course_done')}>Mark complete</button>`)
        : (o.applied ? h`<span className="chip ok">Applied</span>` : h`<button className="btn sm alt" onClick=${() => track(o, 'applied')}>Mark as applied</button>`)}</div></div>`)}</div></div>`;
}

function Mentors({ user, say }) {
  const [list, e] = useData(() => api('/mentors'), []);
  const [reqs, , setReqs] = useData(() => api('/mentor-requests'), []);
  const [open, setOpen] = useState(null), [msg, setMsg] = useState('');
  const reload = () => api('/mentor-requests').then(setReqs);
  const send = async id => { try { await api('/mentor-requests', { method: 'POST', body: { mentor_id: id, message: msg } }); say('Request sent.'); setOpen(null); setMsg(''); reload(); } catch (x) { say(x.message); } };
  const answer = async (id, status) => { try { await api('/mentor-requests/' + id, { method: 'PATCH', body: { status } }); reload(); } catch (x) { say(x.message); } };
  const incoming = (reqs || []).filter(r => r.mentor_id === user.id), mine = (reqs || []).filter(r => r.learner_id === user.id);
  return h`<div className="wrap main">
    ${user.role === 'mentor' && h`<h2>Requests from learners</h2>${incoming.length ? incoming.map(r => h`<div className="card" key=${r.id} style=${{ marginBottom: 12 }}><b>${r.learner_name}</b> <span className="chip">${r.status}</span> <span className="mute">${r.created_at}</span><p>${r.message || 'No message.'}</p>
      ${r.status === 'pending' && h`<div className="row"><button className="btn sm" onClick=${() => answer(r.id, 'accepted')}>Accept</button><button className="btn sm alt" onClick=${() => answer(r.id, 'declined')}>Decline</button></div>`}</div>`) : h`<p className="mute">No requests yet.</p>`}`}
    <h2 style=${{ marginTop: 20 }}>Find a mentor</h2><${Load} d=${list} e=${e}/>
    <div className="grid">${(list || []).map(m => h`<div className="card" key=${m.id}><h3>${m.name}</h3><p className="mute">${m.bio}</p>
      <${Chips} list=${m.skills}/>${m.helps_with.length ? h`<div className="mute">Can help you with:</div><${Chips} list=${m.helps_with} cls="gap"/>` : ''}
      ${open === m.id ? h`<form onSubmit=${ev => { ev.preventDefault(); send(m.id); }}><label>Message (optional)<textarea rows="3" maxLength="500" value=${msg} onInput=${ev => setMsg(ev.target.value)}></textarea></label><div className="row"><button className="btn sm">Send request</button><button type="button" className="btn sm alt" onClick=${() => setOpen(null)}>Cancel</button></div></form>`
        : h`<button className="btn sm" onClick=${() => setOpen(m.id)}>Request mentoring</button>`}</div>`)}</div>
    <h3 style=${{ marginTop: 28 }}>My requests</h3>
    ${mine.length ? mine.map(r => h`<p key=${r.id}>${r.mentor_name}: <span className="chip ${r.status === 'accepted' ? 'ok' : ''}">${r.status}</span> <span className="mute">${r.created_at}</span></p>`) : h`<p className="mute">You have not requested a mentor yet.</p>`}</div>`;
}

function Admin({ say }) {
  const [s] = useData(() => api('/stats'), []);
  const [users] = useData(() => api('/admin/users'), []);
  const [opps, , setOpps] = useData(() => api('/opportunities'), []);
  const [f, setF] = useState({ title: '', type: 'job', org: '', skills_needed: '', link: '', description: '' });
  const reload = () => api('/opportunities').then(setOpps);
  const add = async e => { e.preventDefault(); try { await api('/admin/opportunities', { method: 'POST', body: f }); say('Opportunity added.'); setF({ ...f, title: '', skills_needed: '', link: '', description: '' }); reload(); } catch (x) { say(x.message); } };
  const del = async id => { if (confirm('Delete this opportunity?')) { await api('/admin/opportunities/' + id, { method: 'DELETE' }); reload(); } };
  const inp = (k, l, extra) => h`<label>${l}<input value=${f[k]} onInput=${e => setF({ ...f, [k]: e.target.value })} ...${extra}/></label>`;
  return h`<div className="wrap main"><h2>Admin: usage report</h2>
    ${s && h`<div className="grid">${Object.entries(s).map(([k, v]) => h`<div className="card" key=${k}><div className="num">${v}</div>${k.replace('_', ' ')}</div>`)}</div>`}
    <h2 style=${{ marginTop: 30 }}>Add opportunity</h2>
    <form className="narrow" onSubmit=${add}>${inp('title', 'Title', { required: true })}
      <label>Type<select value=${f.type} onChange=${e => setF({ ...f, type: e.target.value })}><option value="job">Job</option><option value="internship">Internship</option><option value="course">Course</option></select></label>
      ${inp('org', 'Organisation')}${inp('skills_needed', 'Skills needed (comma separated, e.g. Python,SQL)', { required: true })}${inp('link', 'Link (https://…)')}${inp('description', 'Short description')}
      <button className="btn">Add opportunity</button></form>
    <h3 style=${{ marginTop: 30 }}>All opportunities</h3><div className="scroll"><table><thead><tr><th>Title</th><th>Type</th><th>Skills</th><th></th></tr></thead><tbody>
      ${(opps || []).map(o => h`<tr key=${o.id}><td>${o.title}</td><td>${o.type}</td><td>${o.skills_needed}</td><td><button className="btn sm alt" onClick=${() => del(o.id)}>Delete</button></td></tr>`)}</tbody></table></div>
    <h3 style=${{ marginTop: 30 }}>Recent users</h3><div className="scroll"><table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Joined</th></tr></thead><tbody>
      ${(users || []).map(u => h`<tr key=${u.id}><td>${u.name}</td><td>${u.email}</td><td>${u.role}</td><td>${u.joined}</td></tr>`)}</tbody></table></div></div>`;
}

function App() {
  const [route, setRoute] = useState(location.hash.slice(1) || 'home'), [user, setUser] = useState(null), [ready, setReady] = useState(false), [toast, setToast] = useState('');
  useEffect(() => {
    const f = () => { setRoute(location.hash.slice(1) || 'home'); scrollTo(0, 0); };
    addEventListener('hashchange', f);
    if (localStorage.getItem('token')) api('/me').then(setUser).catch(() => localStorage.removeItem('token')).finally(() => setReady(true)); else setReady(true);
  }, []);
  const say = m => { setToast(m); setTimeout(() => setToast(''), 3000); };
  const onAuth = r => { localStorage.setItem('token', r.token); setUser(r.user); location.hash = 'dashboard'; };
  const logout = () => { localStorage.removeItem('token'); setUser(null); location.hash = 'home'; };
  if (!ready) return h`<p className="wrap main mute">Loading…</p>`;
  const pages = { dashboard: Dashboard, assess: Assess, opportunities: Opps, mentors: Mentors, admin: Admin };
  let Page = Home;
  if (route === 'auth') Page = user ? Dashboard : Auth;
  else if (pages[route]) Page = !user ? Auth : (route === 'admin' && user.role !== 'admin') ? Home : pages[route];
  const links = user ? [['dashboard', 'Dashboard'], ['assess', 'Skill tests'], ['opportunities', 'Opportunities'], ['mentors', 'Mentors'], ...(user.role === 'admin' ? [['admin', 'Admin']] : [])] : [];
  return h`<div><nav className="top"><div className="wrap"><b>SheRise</b>
      ${links.map(([r, l]) => h`<a key=${r} href=${'#' + r} className=${route === r ? 'on' : ''}>${l}</a>`)}
      ${user ? h`<button onClick=${logout}>Sign out</button>` : h`<a href="#auth">Sign in</a>`}</div></nav>
    <${Page} user=${user} setUser=${setUser} say=${say} onAuth=${onAuth}/>
    <div className="wrap mute" style=${{ padding: '0 20px 30px' }}>© ${new Date().getFullYear()} SheRise · Team Code Divas, KRMU · Supports SDG 5</div>
    ${toast && h`<div className="toast" role="status">${toast}</div>`}</div>`;
}
ReactDOM.createRoot(document.getElementById('root')).render(h`<${App}/>`);
