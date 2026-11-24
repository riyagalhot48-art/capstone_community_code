"""SheRise - Women Skills & Career Empowerment Platform (Flask REST API + React frontend)."""
import os, re, random
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('DATA_DIR', os.path.join(BASE, 'data'))
os.makedirs(DATA_DIR, exist_ok=True)
app = Flask(__name__, static_folder='static', static_url_path='')
# DATABASE_URL e.g. mysql+pymysql://user:pass@host/women_empower  (defaults to SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(DATA_DIR, 'sherise.db')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024
db = SQLAlchemy(app)
ser = URLSafeTimedSerializer(os.environ.get('SECRET_KEY', 'dev-only-change-me'))
if 'SECRET_KEY' not in os.environ:
    print('WARNING: set SECRET_KEY in production.')

SKILLS = ['Python', 'SQL', 'Communication', 'Git', 'Excel', 'Statistics', 'HTML', 'CSS', 'JavaScript', 'React']
QB = {  # (question, options, index of correct option)
 'Python': [('Which creates a list?', ['(1,2)', '[1,2]', '{1,2}'], 1), ('What is len("abc")?', ['2', '3', '4'], 1), ('Keyword to define a function?', ['func', 'def', 'fn'], 1)],
 'SQL': [('Which clause filters rows?', ['WHERE', 'ORDER BY', 'GROUP BY'], 0), ('Which statement adds a row?', ['INSERT', 'SELECT', 'DROP'], 0), ('COUNT(*) returns?', ['A sum', 'The number of rows', 'An average'], 1)],
 'Communication': [('You disagree in a meeting. Best first step?', ['Interrupt', 'Listen, then share your view politely', 'Stay silent'], 1), ('A clear email has?', ['A clear subject and one main ask', 'Only long background', 'No greeting'], 0), ('Active listening means?', ['Planning your reply', 'Full attention and checking you understood', 'Waiting to talk'], 1)],
 'Git': [('Which saves changes to local history?', ['git commit', 'git clone', 'git pull'], 0), ('Which copies a remote repo?', ['git clone', 'git init', 'git add'], 0), ('Which stages files?', ['git add', 'git push', 'git log'], 0)],
 'Excel': [('A formula starts with?', ['=', '#', '@'], 0), ('SUM(A1:A3) does?', ['Adds three cells', 'Counts text', 'Multiplies'], 0), ('Which looks up a value in a table?', ['VLOOKUP', 'LEN', 'TODAY'], 0)],
 'Statistics': [('Middle value of sorted data?', ['Mean', 'Median', 'Mode'], 1), ('Most frequent value?', ['Mode', 'Median', 'Range'], 0), ('Max minus min is the?', ['Range', 'Mean', 'Mode'], 0)],
 'HTML': [('Tag for the largest heading?', ['h1', 'head', 'title'], 0), ('Tag for a link?', ['a', 'link', 'href'], 0), ('Tag for an image?', ['img', 'image', 'pic'], 0)],
 'CSS': [('Property for text colour?', ['color', 'font-style', 'text-size'], 0), ('Selector for class "x"?', ['.x', '#x', 'x'], 0), ('display value for flexbox?', ['flex', 'block-flex', 'inline'], 0)],
 'JavaScript': [('Block-scoped variable keyword?', ['let', 'int', 'dim'], 0), ('"3" + 2 gives?', ['5', '"32"', 'an error'], 1), ('Add to end of an array?', ['push', 'add', 'append'], 0)],
 'React': [('Hook for state?', ['useState', 'useData', 'getState'], 0), ('A component returns?', ['JSX (UI)', 'SQL', 'A file'], 0), ('Hook for side effects?', ['useEffect', 'useStyle', 'useSort'], 0)],
}
PASS = 67  # percent needed to verify a skill


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), default='learner')  # learner | mentor | admin
    skills = db.Column(db.Text, default='')
    bio = db.Column(db.String(300), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def skill_list(self): return [s for s in (self.skills or '').split(',') if s]
    def public(self): return dict(id=self.id, name=self.name, email=self.email, role=self.role, skills=self.skill_list(), bio=self.bio)


class Opportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(12), nullable=False)  # job | internship | course
    org = db.Column(db.String(100), default='')
    skills_needed = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(300), default='')
    description = db.Column(db.String(400), default='')


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kind = db.Column(db.String(20), nullable=False)  # assessment | applied | course_done
    ref = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MentorRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    learner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), default='')
    status = db.Column(db.String(10), default='pending')  # pending | accepted | declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def seed():
    if Opportunity.query.count() == 0:
        rows = [
         ('Data Entry & Reporting Associate', 'job', 'Sample listing', 'Python,SQL,Communication', '', 'Sample role: clean data and prepare weekly reports.'),
         ('Junior Python Developer', 'job', 'Sample listing', 'Python,SQL,Git', '', 'Sample role: build and fix small backend features.'),
         ('Data Analyst Intern', 'internship', 'Sample listing', 'Python,SQL,Excel,Statistics', '', 'Sample internship: analyse survey data.'),
         ('Web Developer Intern', 'internship', 'Sample listing', 'HTML,CSS,JavaScript,React', '', 'Sample internship: build pages for a local NGO.'),
         ('Customer Support Associate', 'job', 'Sample listing', 'Communication,Excel', '', 'Sample role: help customers by phone and email.'),
         ('Python for Everybody / CS50', 'course', 'Free: CS50 (Harvard)', 'Python', 'https://cs50.harvard.edu/x', 'Free, self-paced programming course.'),
         ('Learn SQL', 'course', 'Free: Khan Academy', 'SQL', 'https://www.khanacademy.org/computing/computer-programming/sql', 'Free interactive SQL lessons.'),
         ('Pro Git book', 'course', 'Free: git-scm.com', 'Git', 'https://git-scm.com/book', 'Free book on Git from basics.'),
         ('Excel training', 'course', 'Free: Microsoft Support', 'Excel', 'https://support.microsoft.com/en-us/excel', 'Free Excel video training.'),
         ('Statistics and probability', 'course', 'Free: Khan Academy', 'Statistics', 'https://www.khanacademy.org/math/statistics-probability', 'Free statistics lessons.'),
         ('Web basics: HTML, CSS, JavaScript', 'course', 'Free: freeCodeCamp', 'HTML,CSS,JavaScript', 'https://www.freecodecamp.org/learn', 'Free hands-on web development path.'),
         ('Learn React', 'course', 'Free: react.dev', 'React,JavaScript', 'https://react.dev/learn', 'Official React tutorial.'),
         ('Communication at work', 'course', 'Free: Coursera audit / local library', 'Communication', 'https://www.coursera.org/browse/personal-development', 'Find free-to-audit communication courses.'),
        ]
        for t, ty, o, s, l, d in rows:
            db.session.add(Opportunity(title=t, type=ty, org=o, skills_needed=s, link=l, description=d))
    if User.query.filter_by(role='mentor').count() == 0:
        for n, s, b in [('Sample Mentor: Ananya', 'Python,SQL,Git', 'Sample profile. Replaced when real mentors join.'),
                        ('Sample Mentor: Meera', 'Communication,Excel,Statistics', 'Sample profile. Replaced when real mentors join.'),
                        ('Sample Mentor: Kavya', 'HTML,CSS,JavaScript,React', 'Sample profile. Replaced when real mentors join.')]:
            db.session.add(User(name=n, email=n.split(': ')[1].lower() + '@sample.invalid', password_hash=generate_password_hash(os.urandom(8).hex()), role='mentor', skills=s, bio=b))
    ae, ap = os.environ.get('ADMIN_EMAIL', '').lower(), os.environ.get('ADMIN_PASSWORD', '')
    if ae and ap and not User.query.filter_by(email=ae).first():
        db.session.add(User(name='Admin', email=ae, password_hash=generate_password_hash(ap), role='admin'))
    db.session.commit()


with app.app_context():
    db.create_all()
    seed()


def auth(roles=None):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            try: uid = ser.loads(request.headers.get('Authorization', '')[7:], max_age=7 * 86400)
            except Exception: return jsonify(error='Please sign in.'), 401
            u = db.session.get(User, uid)
            if not u: return jsonify(error='Please sign in.'), 401
            if roles and u.role not in roles: return jsonify(error='You do not have access to this.'), 403
            g.user = u
            return f(*a, **k)
        return w
    return deco


def body(): return request.get_json(silent=True) or {}
def clean(v, n): return v.strip()[:n] if isinstance(v, str) else ''
def split_skills(v):
    items = v.split(',') if isinstance(v, str) else (v if isinstance(v, list) else [])
    return [clean(x, 40) for x in items if clean(x, 40)]


def match(user_skills, needed):
    need = [s for s in needed.split(',') if s]
    have = {s.lower() for s in user_skills}
    gap = [s for s in need if s.lower() not in have]
    return (round(100 * (len(need) - len(gap)) / len(need)) if need else 0), gap


def progress(u):
    acts = Activity.query.filter_by(user_id=u.id).all()
    passed = sum(1 for a in acts if a.kind == 'assessment' and a.score >= PASS)
    taken = sum(1 for a in acts if a.kind == 'assessment')
    courses = sum(1 for a in acts if a.kind == 'course_done')
    applied = sum(1 for a in acts if a.kind == 'applied')
    sessions = MentorRequest.query.filter_by(learner_id=u.id, status='accepted').count()
    pct = min(100, passed * 15 + courses * 20 + applied * 10 + sessions * 15)
    return dict(progress=pct, assessments_taken=taken, skills_verified=passed, courses_finished=courses, applications=applied, mentor_sessions=sessions)


@app.get('/')
def index(): return send_from_directory(app.static_folder, 'index.html')
@app.get('/api/health')
def health(): return jsonify(ok=True)


@app.post('/api/register')
def register():
    d = body()
    name, email, pw = clean(d.get('name'), 100), clean(d.get('email'), 150).lower(), d.get('password') or ''
    role = d.get('role') if d.get('role') in ('learner', 'mentor') else 'learner'
    skills = [s for s in split_skills(d.get('skills')) if s in SKILLS]
    if not name or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email): return jsonify(error='Enter your name and a valid email.'), 400
    if not isinstance(pw, str) or len(pw) < 8: return jsonify(error='Password must be at least 8 characters.'), 400
    if User.query.filter_by(email=email).first(): return jsonify(error='This email already has an account. Sign in instead.'), 409
    u = User(name=name, email=email, password_hash=generate_password_hash(pw), role=role, skills=','.join(skills), bio=clean(d.get('bio'), 300))
    db.session.add(u); db.session.commit()
    return jsonify(token=ser.dumps(u.id), user=u.public()), 201


@app.post('/api/login')
def login():
    d = body()
    u = User.query.filter_by(email=clean(d.get('email'), 150).lower()).first()
    if not u or not check_password_hash(u.password_hash, d.get('password') or ''): return jsonify(error='Email or password is wrong.'), 401
    return jsonify(token=ser.dumps(u.id), user=u.public())


@app.get('/api/me')
@auth()
def me(): return jsonify(g.user.public())


@app.get('/api/skills')
def skills(): return jsonify(SKILLS)


@app.get('/api/questions/<skill>')
def questions(skill):
    if skill not in QB: return jsonify(error='Unknown skill.'), 404
    return jsonify([dict(i=i, q=q, options=random.sample(o, len(o))) for i, (q, o, _) in enumerate(QB[skill])])


@app.post('/api/assess')
@auth()
def assess():
    d = body(); skill = d.get('skill'); ans = d.get('answers') or {}
    if skill not in QB: return jsonify(error='Unknown skill.'), 404
    right = sum(1 for i, (_, o, c) in enumerate(QB[skill]) if ans.get(str(i)) == o[c])
    pct = round(100 * right / len(QB[skill])); passed = pct >= PASS
    a = Activity.query.filter_by(user_id=g.user.id, kind='assessment', ref=skill).first()
    if a: a.score = max(a.score, pct)
    else: db.session.add(Activity(user_id=g.user.id, kind='assessment', ref=skill, score=pct))
    if passed and skill not in g.user.skill_list():
        g.user.skills = ','.join(g.user.skill_list() + [skill])
    db.session.commit()
    return jsonify(score=pct, correct=right, total=len(QB[skill]), passed=passed, user=g.user.public())


@app.get('/api/assessments')
@auth()
def my_assessments():
    return jsonify({a.ref: a.score for a in Activity.query.filter_by(user_id=g.user.id, kind='assessment')})


@app.get('/api/recommend/<int:uid>')
@auth()
def recommend(uid):
    if g.user.id != uid and g.user.role != 'admin': return jsonify(error='You do not have access to this.'), 403
    u = db.session.get(User, uid)
    q = Opportunity.query
    if request.args.get('type') in ('job', 'internship', 'course'): q = q.filter_by(type=request.args['type'])
    done = {(a.kind, a.ref) for a in Activity.query.filter_by(user_id=uid) if a.kind in ('applied', 'course_done')}
    out = []
    for o in q.all():
        pct, gap = match(u.skill_list(), o.skills_needed)
        out.append(dict(id=o.id, title=o.title, type=o.type, org=o.org, link=o.link, description=o.description, match=pct, skill_gap=gap,
                        applied=('applied', str(o.id)) in done, course_done=('course_done', str(o.id)) in done))
    return jsonify(sorted(out, key=lambda x: -x['match']))


@app.post('/api/track')
@auth()
def track():
    d = body(); o = db.session.get(Opportunity, d.get('opportunity_id') or 0); kind = d.get('kind')
    if not o or kind not in ('applied', 'course_done'): return jsonify(error='Invalid request.'), 400
    if (kind == 'course_done') != (o.type == 'course'): return jsonify(error='That action does not fit this opportunity.'), 400
    if not Activity.query.filter_by(user_id=g.user.id, kind=kind, ref=str(o.id)).first():
        db.session.add(Activity(user_id=g.user.id, kind=kind, ref=str(o.id))); db.session.commit()
    return jsonify(ok=True)


@app.get('/api/progress/<int:uid>')
@auth()
def progress_route(uid):
    if g.user.id != uid and g.user.role != 'admin': return jsonify(error='You do not have access to this.'), 403
    return jsonify(progress(db.session.get(User, uid)))


@app.get('/api/mentors')
@auth()
def mentors():
    mine = set(g.user.skill_list())
    return jsonify([dict(m.public(), email=None, helps_with=[s for s in m.skill_list() if s not in mine])
                    for m in User.query.filter_by(role='mentor').all() if m.id != g.user.id])


def req_json(r):
    l, m = db.session.get(User, r.learner_id), db.session.get(User, r.mentor_id)
    return dict(id=r.id, status=r.status, message=r.message, learner_id=l.id, learner_name=l.name, mentor_id=m.id, mentor_name=m.name,
                created_at=r.created_at.strftime('%d %b %Y'))


@app.post('/api/mentor-requests')
@auth()
def mentor_request():
    d = body(); m = db.session.get(User, d.get('mentor_id') or 0)
    if not m or m.role != 'mentor' or m.id == g.user.id: return jsonify(error='Choose a mentor from the list.'), 400
    if MentorRequest.query.filter_by(learner_id=g.user.id, mentor_id=m.id, status='pending').first():
        return jsonify(error='You already have a pending request with this mentor.'), 409
    db.session.add(MentorRequest(learner_id=g.user.id, mentor_id=m.id, message=clean(d.get('message'), 500))); db.session.commit()
    return jsonify(ok=True), 201


@app.get('/api/mentor-requests')
@auth()
def my_requests():
    rs = MentorRequest.query.filter((MentorRequest.learner_id == g.user.id) | (MentorRequest.mentor_id == g.user.id)).order_by(MentorRequest.id.desc()).all()
    return jsonify([req_json(r) for r in rs])


@app.patch('/api/mentor-requests/<int:rid>')
@auth(['mentor', 'admin'])
def answer_request(rid):
    r = db.session.get(MentorRequest, rid); st = body().get('status')
    if not r or r.mentor_id != g.user.id or st not in ('accepted', 'declined'): return jsonify(error='Invalid request.'), 400
    r.status = st; db.session.commit()
    return jsonify(ok=True)


@app.get('/api/stats')
def stats():
    return jsonify(profiles=User.query.filter_by(role='learner').count(), mentors=User.query.filter_by(role='mentor').count(),
                   assessments=Activity.query.filter_by(kind='assessment').count(), courses_finished=Activity.query.filter_by(kind='course_done').count(),
                   applications=Activity.query.filter_by(kind='applied').count(), mentor_sessions=MentorRequest.query.filter_by(status='accepted').count())


@app.get('/api/admin/users')
@auth(['admin'])
def admin_users():
    return jsonify([dict(u.public(), joined=u.created_at.strftime('%d %b %Y')) for u in User.query.order_by(User.id.desc()).limit(100)])


@app.get('/api/opportunities')
@auth(['admin'])
def all_opps():
    return jsonify([dict(id=o.id, title=o.title, type=o.type, org=o.org, skills_needed=o.skills_needed) for o in Opportunity.query.order_by(Opportunity.id.desc())])


@app.post('/api/admin/opportunities')
@auth(['admin'])
def add_opp():
    d = body(); title = clean(d.get('title'), 150); ty = d.get('type'); need = split_skills(d.get('skills_needed')); link = clean(d.get('link'), 300)
    if not title or ty not in ('job', 'internship', 'course') or not need: return jsonify(error='Title, type and at least one skill are required.'), 400
    if link and not re.match(r'^https?://', link): return jsonify(error='Link must start with http:// or https://'), 400
    db.session.add(Opportunity(title=title, type=ty, org=clean(d.get('org'), 100), skills_needed=','.join(need), link=link, description=clean(d.get('description'), 400)))
    db.session.commit()
    return jsonify(ok=True), 201


@app.delete('/api/admin/opportunities/<int:oid>')
@auth(['admin'])
def del_opp(oid):
    o = db.session.get(Opportunity, oid)
    if o: db.session.delete(o); db.session.commit()
    return jsonify(ok=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), debug=False)
