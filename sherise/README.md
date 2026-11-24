# SheRise - Women Skills & Career Empowerment Platform
Team Code Divas, B.Tech CSE Section E, KRMU. Flask REST API + React frontend + MySQL (SQLite for quick start). Supports SDG 5.

## Run locally
    pip install -r requirements.txt
    SECRET_KEY=abc ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=ChangeMe123 python app.py
Open http://localhost:8000. Windows PowerShell: set each variable with `$env:NAME="value"` first.

## Use MySQL (as in the project plan)
Create the database in MySQL Workbench: `CREATE DATABASE women_empower;`
Then set `DATABASE_URL=mysql+pymysql://root:PASSWORD@localhost:3306/women_empower`. Tables are created automatically.

## REST API
POST /api/register, POST /api/login, POST /api/assess, GET /api/recommend/<id>, GET /api/progress/<id>,
GET /api/mentors, POST/GET/PATCH /api/mentor-requests, POST /api/track, GET /api/stats, admin: POST/DELETE /api/admin/opportunities.

## Deploy (Render)
1. Push to GitHub. 2. Render > New > Web Service > Docker.
3. Env vars: SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD (and DATABASE_URL for MySQL).
4. With SQLite, attach a Persistent Disk at /data. With a hosted MySQL (e.g. Aiven, Railway) no disk is needed.
Health check: /api/health

## Before going live
- The jobs/internships and the three mentors are SAMPLE data. Sign in as admin to replace jobs with real listings; mentors appear when real mentors register.
- Course links go to free third-party platforms.
