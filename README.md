# Planner

A minimalist daily planner web app built with Flask and SQLite.

## Features
- **Daily View**: To Do list, Power Hour block, Meetings, and Notes
- **Priority Matrix**: 2x2 grid to prioritize tasks by urgency and complexity
- **Week navigation**: click any day to jump to it
- **Auto-clears**: all data is wiped after 24 hours
- **Print**: clean print view on both pages

## Explaining the Matrix Quadrants
- **Start Here** = due today + quick win
- **On Hold** = due later + quick win (don't get distracted)
- **Power Hour** = due today + big task
- **Break into smaller tasks & reassign** = due later + big task

## Setup

**Requirements:** Python 3.x

**Install Flask:**
```bash
pip install flask
```

**Run:**
```bash
python planner_final.py
```

**Open** `http://127.0.0.1:5000` in your browser.

## Usage
- Type a task and press **Enter** to add it
- Click the checkbox to complete a task
- Hover a task to reveal the delete button
- Use **← →** arrows or the date picker to navigate days
- Click **Print** for a clean printable version

## Notes
- Database is created automatically on first run as `planner.db`
- All entries older than 24 hours are automatically deleted
- Not intended for production deployment

## More
It's a two-page daily productivity system.
- Page 1 | Daily Planner has a day-of-week selector at the top to navigate your week. Below that, the left column splits your tasks into a regular To Do list and a Power Hour block, which is a dedicated section for your most challenging, focused work. The right column has Meetings and a Notes / Don't Forget area.
- Page 2 | Priority Matrix is a 2x2 grid that helps you decide what to work on first. Tasks are sorted by two axes:

Horizontal: Due Today ↔ Due Later
Vertical: Quick Wins ↔ Big Tasks

The idea is that the Matrix helps you plan and prioritize, while the Daily page helps you execute. Tasks added in the Matrix sync to the Daily view, and everything clears automatically after 24 hours so you start fresh each day.

I made sure to add a Print button at the top if you prefer to see it on paper to cross over or checkmark the tasks.

## Tech Stack

**Frontend**
- HTML | CSS | JavaScript

**Backend**
- Python & Flask to handle all API requests (saving, loading, deleting tasks)
- SQLite for the database that stores tasks, meetings, and notes locally

**How they connect**
When you add a task, JavaScript sends a request to Flask (`POST /api/tasks`). Flask writes it to SQLite and returns the saved task. JavaScript then adds it to the page, no page refresh needed.
