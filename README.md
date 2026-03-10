# Planner
A minimalist daily planner web app built with Python (Flask) and SQLite. 
Features a daily schedule view with To Do and Power Hour sections, a priority matrix to categorize tasks by urgency and complexity, plus meetings and notes. 
Data auto-clears every 24 hours.

It's a two-page daily productivity system.
Page 1 | Daily Planner has a day-of-week selector at the top to navigate your week. Below that, the left column splits your tasks into a regular To Do list and a Power Hour block, which is a dedicated section for your most challenging, focused work. The right column has Meetings and a Notes / Don't Forget area.
Page 2 | Priority Matrix is a 2x2 grid that helps you decide what to work on first. Tasks are sorted by two axes:

Horizontal: Due Today ↔ Due Later
Vertical: Quick Wins ↔ Big Tasks

This creates four quadrants with clear guidance:

Start Here = due today + quick win
On Hold = due later + quick win (don't get distracted)
Power Hour = due today + big task (your scary, focused work)
Break into smaller tasks & reassign = due later + big task

The idea is that the Matrix helps you plan and prioritize, while the Daily page helps you execute. Tasks added in the Matrix sync to the Daily view, and everything clears automatically after 24 hours so you start fresh each day.

Features a Print button at the top if you prefer to see it on paper to cross over or checkmark the tasks.

