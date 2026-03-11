from flask import Flask, request, jsonify, redirect
import sqlite3
from datetime import date, datetime, timedelta

app = Flask(__name__)
DB = 'planner.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, completed INTEGER DEFAULT 0,
        task_date TEXT NOT NULL, category TEXT DEFAULT 'todo',
        urgency TEXT DEFAULT 'today', complexity TEXT DEFAULT 'quick',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, meeting_date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT, note_date TEXT NOT NULL UNIQUE,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit(); conn.close()

init_db()

def purge():
    cutoff = (datetime.now()-timedelta(hours=24)).strftime('%Y-%m-%d')
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE task_date < ?", (cutoff,))
    conn.execute("DELETE FROM meetings WHERE meeting_date < ?", (cutoff,))
    conn.execute("DELETE FROM notes WHERE note_date < ?", (cutoff,))
    conn.commit(); conn.close()

@app.before_request
def before(): purge()

@app.route('/')
def index(): return redirect('/daily')

@app.route('/daily')
def daily():
    today = request.args.get('date', date.today().isoformat())
    today_real = date.today().isoformat()
    return DAILY_HTML.replace('__TODAY__', today).replace('__TODAY_REAL__', today_real)

@app.route('/matrix')
def matrix():
    today = request.args.get('date', date.today().isoformat())
    today_real = date.today().isoformat()
    return MATRIX_HTML.replace('__TODAY__', today).replace('__TODAY_REAL__', today_real)

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    d = request.args.get('date', date.today().isoformat())
    conn = get_db()
    tasks = conn.execute('SELECT * FROM tasks WHERE task_date=? ORDER BY created_at',(d,)).fetchall()
    conn.close()
    return jsonify([dict(t) for t in tasks])

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.json
    conn = get_db()
    conn.execute('INSERT INTO tasks (title,task_date,category,urgency,complexity) VALUES(?,?,?,?,?)',
        (data['title'], data.get('task_date', date.today().isoformat()),
         data.get('category','todo'), data.get('urgency','today'), data.get('complexity','quick')))
    conn.commit()
    task_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    task = conn.execute('SELECT * FROM tasks WHERE id=?',(task_id,)).fetchone()
    conn.close()
    return jsonify(dict(task))

@app.route('/api/tasks/<int:tid>', methods=['PUT'])
def update_task(tid):
    data = request.json
    conn = get_db()
    fields,vals=[],[]
    for k in ['title','completed','category','urgency','complexity']:
        if k in data: fields.append(f'{k}=?'); vals.append(data[k])
    vals.append(tid)
    conn.execute(f'UPDATE tasks SET {",".join(fields)} WHERE id=?', vals)
    conn.commit()
    task = conn.execute('SELECT * FROM tasks WHERE id=?',(tid,)).fetchone()
    conn.close()
    return jsonify(dict(task))

@app.route('/api/tasks/<int:tid>', methods=['DELETE'])
def delete_task(tid):
    conn = get_db()
    conn.execute('DELETE FROM tasks WHERE id=?',(tid,))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/meetings', methods=['GET'])
def get_meetings():
    d = request.args.get('date', date.today().isoformat())
    conn = get_db()
    m = conn.execute('SELECT * FROM meetings WHERE meeting_date=? ORDER BY created_at',(d,)).fetchall()
    conn.close()
    return jsonify([dict(x) for x in m])

@app.route('/api/meetings', methods=['POST'])
def add_meeting():
    data = request.json
    conn = get_db()
    conn.execute('INSERT INTO meetings (title,meeting_date) VALUES(?,?)',
        (data['title'], data.get('meeting_date', date.today().isoformat())))
    conn.commit()
    mid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    m = conn.execute('SELECT * FROM meetings WHERE id=?',(mid,)).fetchone()
    conn.close()
    return jsonify(dict(m))

@app.route('/api/meetings/<int:mid>', methods=['DELETE'])
def delete_meeting(mid):
    conn = get_db()
    conn.execute('DELETE FROM meetings WHERE id=?',(mid,))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

@app.route('/api/notes', methods=['GET'])
def get_notes():
    d = request.args.get('date', date.today().isoformat())
    conn = get_db()
    note = conn.execute('SELECT * FROM notes WHERE note_date=?',(d,)).fetchone()
    conn.close()
    return jsonify(dict(note) if note else {'content':'','note_date':d})

@app.route('/api/notes', methods=['POST'])
def save_notes():
    data = request.json
    d = data.get('note_date', date.today().isoformat())
    conn = get_db()
    conn.execute('INSERT INTO notes (content,note_date) VALUES(?,?) ON CONFLICT(note_date) DO UPDATE SET content=?,updated_at=CURRENT_TIMESTAMP',
        (data['content'],d,data['content']))
    conn.commit(); conn.close()
    return jsonify({'ok':True})

DAILY_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Planner</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--ink:#1a1a1a;--ink-light:#888;--ink-faint:#d0d0d0;--paper:#faf9f7;--warm:#f2efe9;--accent:#c9a96e;--red:#c94040}
html,body{height:100%;background:var(--paper);color:var(--ink);font-family:'DM Sans',sans-serif;font-size:14px}
nav{display:flex;align-items:center;justify-content:space-between;padding:16px 40px;border-bottom:1px solid var(--ink-faint);background:var(--paper);position:sticky;top:0;z-index:100}
.brand{font-family:'DM Serif Display',serif;font-size:20px;letter-spacing:-0.5px;color:var(--ink);text-decoration:none}
.nav-links{display:flex;gap:6px}
.nav-link{padding:7px 16px;border-radius:100px;text-decoration:none;font-size:13px;font-weight:500;color:var(--ink-light);transition:all .2s}
.nav-link:hover{color:var(--ink);background:var(--warm)}
.nav-link.active{background:var(--ink);color:var(--paper)}
.date-nav{display:flex;align-items:center;gap:10px}
.date-nav button{background:none;border:1px solid var(--ink-faint);border-radius:6px;padding:4px 10px;cursor:pointer;font-family:inherit;font-size:13px;color:var(--ink)}
.date-nav button:hover{background:var(--warm)}
.date-nav input[type=date]{border:1px solid var(--ink-faint);border-radius:6px;padding:4px 10px;font-family:inherit;font-size:13px;background:var(--paper);color:var(--ink)}
main{padding:36px 40px;max-width:1100px;margin:0 auto}
.day-header{display:flex;align-items:baseline;gap:14px;margin-bottom:24px}
.day-header h1{font-family:'DM Serif Display',serif;font-size:34px;font-weight:400;letter-spacing:-1px}
.day-header .dow{color:var(--ink-light);font-size:15px}
/* CIRCLES */
.week-days{display:flex;gap:8px;margin-bottom:36px}
.week-day{width:40px;height:40px;border-radius:50%;border:1.5px solid var(--ink-faint);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;color:var(--ink-light);cursor:pointer;transition:all .2s;text-decoration:none}
.week-day:hover{border-color:var(--ink);color:var(--ink)}
.week-day.active{background:var(--ink);border-color:var(--ink);color:var(--paper)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:32px}
.section-title{font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-light);margin-bottom:12px}
.task-list{display:flex;flex-direction:column;gap:1px}
.task-item{display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:8px;transition:background .15s}
.task-item:hover{background:var(--warm)}
.chk{width:18px;height:18px;border:1.5px solid var(--ink-faint);border-radius:4px;cursor:pointer;flex-shrink:0;display:flex;align-items:center;justify-content:center;transition:all .2s}
.chk:hover{border-color:var(--accent)}
.chk.checked{background:var(--ink);border-color:var(--ink)}
.chk.checked::after{content:'';width:5px;height:9px;border-right:2px solid white;border-bottom:2px solid white;transform:rotate(45deg) translate(-1px,-1px);display:block}
.task-title{flex:1;font-size:14px}
.task-title.done{color:var(--ink-faint);text-decoration:line-through}
.del-btn{opacity:0;background:none;border:none;cursor:pointer;color:var(--ink-light);font-size:17px;padding:0 4px;border-radius:4px;transition:all .15s}
.task-item:hover .del-btn{opacity:1}
.del-btn:hover{color:var(--red)}
.add-row{display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:8px;border:1.5px dashed var(--ink-faint);margin-top:6px;transition:border-color .2s}
.add-row:focus-within{border-color:var(--accent);border-style:solid}
.add-row .plus{color:var(--ink-faint);font-size:17px;flex-shrink:0}
input[type=text],textarea{font-family:'DM Sans',sans-serif;font-size:14px;background:transparent;border:none;outline:none;color:var(--ink);width:100%}
textarea{resize:none}
.power-block{background:#ede8e3;border-radius:12px;padding:24px 20px 24px 48px;margin-top:22px;position:relative;min-height:120px}
.power-label{position:absolute;left:-2px;top:50%;transform:translateY(-50%) rotate(-90deg);transform-origin:center;font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-light);white-space:nowrap}
.box{border:1.5px solid var(--ink-faint);border-radius:12px;padding:16px}
.meeting-item{display:flex;align-items:center;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--ink-faint);font-size:14px}
.meeting-item:last-child{border-bottom:none}
.meet-del{opacity:0;background:none;border:none;cursor:pointer;color:var(--ink-light);font-size:15px;transition:all .15s}
.meeting-item:hover .meet-del{opacity:1;color:var(--red)}
.notes-box{border:1.5px solid var(--ink-faint);border-radius:12px;padding:16px;margin-top:24px}
.notes-box textarea{min-height:180px;line-height:1.7}
.print-btn{background:none;border:1px solid var(--ink-faint);border-radius:6px;padding:6px 14px;cursor:pointer;font-family:inherit;font-size:13px;color:var(--ink-light);transition:all .2s;display:flex;align-items:center;gap:6px}
.print-btn:hover{border-color:var(--ink);color:var(--ink)}
@media print{
  nav,.print-btn,.del-btn,.meet-del,.add-row{display:none!important}
  body{background:white}
  main{padding:20px}
  .chk{border:1.5px solid #999!important;print-color-adjust:exact}
  .chk.checked{background:#000!important;print-color-adjust:exact}
  .power-block{background:#ede8e3!important;print-color-adjust:exact}
  .box,.notes-box{border:1px solid #ccc!important}
}
</style>
</head>
<body>
<nav>
  <a class="brand" href="/">Planner</a>
  <div class="nav-links">
    <a class="nav-link active" href="/daily?date=__TODAY__">Daily</a>
    <a class="nav-link" href="/matrix?date=__TODAY__">Matrix</a>
  </div>
  <div class="date-nav">
    <button onclick="changeDate(-1)">&#8592;</button>
    <input type="date" value="__TODAY__" onchange="goDate(this.value)">
    <button onclick="goDate(\'__TODAY_REAL__\')">Today</button>
    <button class="print-btn" onclick="window.print()">&#128424; Print</button>
  </div>
</nav>
<main>
  <div class="day-header">
    <h1 id="dateDisplay"></h1>
    <span class="dow" id="dowDisplay"></span>
  </div>

  <div class="week-days" id="weekDays"></div>

  <div class="grid">
    <div>
      <div class="section-title">Today\'s Schedule</div>
      <div class="section-title" style="font-size:10px;margin-bottom:8px;margin-top:-4px;">To Do</div>
      <div class="task-list" id="todoList"></div>
      <div class="add-row">
        <span class="plus">+</span>
        <input type="text" placeholder="Add a task&#8230;" onkeydown="addTask(event,\'todo\')">
      </div>

      <div class="power-block" style="margin-top:22px;">
        <span class="power-label">Power Hour</span>
        <div class="task-list" id="powerList"></div>
        <div class="add-row" style="border-color:#c8bdb6;">
          <span class="plus" style="color:#c8bdb6;">+</span>
          <input type="text" placeholder="Add a power hour task&#8230;" onkeydown="addTask(event,\'power_hour\')">
        </div>
      </div>
    </div>

    <div>
      <div class="section-title">Meetings</div>
      <div class="box">
        <div id="meetingList"></div>
        <div class="add-row" style="margin-top:8px;border-color:#ddd;">
          <span class="plus">+</span>
          <input type="text" placeholder="Add meeting&#8230;" onkeydown="addMeeting(event)">
        </div>
      </div>

      <div class="section-title" style="margin-top:24px;">Notes / Don\'t Forget</div>
      <div class="notes-box">
        <textarea id="notesArea" placeholder="Your notes&#8230;" oninput="scheduleNoteSave()"></textarea>
      </div>
    </div>
  </div>
</main>
<script>
const CURRENT_DATE = '__TODAY__';
const TODAY_REAL = '__TODAY_REAL__';
const DAYS = ['S','M','T','W','T','F','S'];
let notesTimer;

function goDate(d){const u=new URL(location);u.searchParams.set('date',d);location=u}
function changeDate(n){const d=new Date(CURRENT_DATE+'T12:00:00');d.setDate(d.getDate()+n);goDate(d.toISOString().slice(0,10))}

function formatDate(d){return new Date(d+'T12:00:00').toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric'})}
function getDow(d){return new Date(d+'T12:00:00').toLocaleDateString('en-US',{weekday:'long'})}

function buildWeekDays(){
  const dt=new Date(CURRENT_DATE+'T12:00:00');
  const start=new Date(dt);
  start.setDate(dt.getDate()-dt.getDay());
  const el=document.getElementById('weekDays');
  el.innerHTML='';
  for(let i=0;i<7;i++){
    const d=new Date(start);d.setDate(start.getDate()+i);
    const iso=d.toISOString().slice(0,10);
    const a=document.createElement('a');
    a.className='week-day'+(iso===CURRENT_DATE?' active':'');
    a.textContent=DAYS[i];a.href='?date='+iso;
    el.appendChild(a);
  }
}

function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function taskHTML(t){
  return '<div class="task-item" id="task-'+t.id+'">'
    +'<div class="chk '+(t.completed?'checked':'')+'" onclick="toggleTask('+t.id+','+(t.completed?0:1)+')"></div>'
    +'<span class="task-title '+(t.completed?'done':'')+'">'+esc(t.title)+'</span>'
    +'<button class="del-btn" onclick="deleteTask('+t.id+')">&#215;</button>'
    +'</div>';
}
function meetingHTML(m){
  return '<div class="meeting-item" id="meeting-'+m.id+'">'
    +'<span>'+esc(m.title)+'</span>'
    +'<button class="meet-del" onclick="deleteMeeting('+m.id+')">&#215;</button>'
    +'</div>';
}

async function api(method,path,body){
  const r=await fetch(path,{method,headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});
  return r.json();
}

async function loadAll(){
  const [tasks,meetings,note]=await Promise.all([
    api('GET','/api/tasks?date='+CURRENT_DATE),
    api('GET','/api/meetings?date='+CURRENT_DATE),
    api('GET','/api/notes?date='+CURRENT_DATE)
  ]);
  document.getElementById('todoList').innerHTML=tasks.filter(t=>t.category==='todo').map(taskHTML).join('');
  document.getElementById('powerList').innerHTML=tasks.filter(t=>t.category==='power_hour').map(taskHTML).join('');
  document.getElementById('meetingList').innerHTML=meetings.map(meetingHTML).join('');
  document.getElementById('notesArea').value=note.content||'';
}

async function addTask(e,cat){
  if(e.key!=='Enter')return;
  const inp=e.target,title=inp.value.trim();if(!title)return;
  const t=await api('POST','/api/tasks',{title,task_date:CURRENT_DATE,category:cat});
  document.getElementById(cat==='todo'?'todoList':'powerList').insertAdjacentHTML('beforeend',taskHTML(t));
  inp.value='';
}
async function toggleTask(id,val){
  const t=await api('PUT','/api/tasks/'+id,{completed:val});
  document.getElementById('task-'+id).outerHTML=taskHTML(t);
}
async function deleteTask(id){await api('DELETE','/api/tasks/'+id);document.getElementById('task-'+id).remove()}
async function addMeeting(e){
  if(e.key!=='Enter')return;
  const inp=e.target,title=inp.value.trim();if(!title)return;
  const m=await api('POST','/api/meetings',{title,meeting_date:CURRENT_DATE});
  document.getElementById('meetingList').insertAdjacentHTML('beforeend',meetingHTML(m));
  inp.value='';
}
async function deleteMeeting(id){await api('DELETE','/api/meetings/'+id);document.getElementById('meeting-'+id).remove()}
function scheduleNoteSave(){
  clearTimeout(notesTimer);
  notesTimer=setTimeout(async()=>{
    await api('POST','/api/notes',{content:document.getElementById('notesArea').value,note_date:CURRENT_DATE});
  },800);
}

document.getElementById('dateDisplay').textContent=formatDate(CURRENT_DATE);
document.getElementById('dowDisplay').textContent=getDow(CURRENT_DATE);
buildWeekDays();
loadAll();
</script>
</body>
</html>'''

MATRIX_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Matrix — Planner</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--ink:#1a1a1a;--ink-light:#888;--ink-faint:#d0d0d0;--paper:#faf9f7;--warm:#f2efe9;--accent:#c9a96e;--red:#c94040}
html,body{height:100%;background:var(--paper);color:var(--ink);font-family:'DM Sans',sans-serif;font-size:14px}
nav{display:flex;align-items:center;justify-content:space-between;padding:16px 40px;border-bottom:1px solid var(--ink-faint);background:var(--paper);position:sticky;top:0;z-index:100}
.brand{font-family:'DM Serif Display',serif;font-size:20px;letter-spacing:-0.5px;color:var(--ink);text-decoration:none}
.nav-links{display:flex;gap:6px}
.nav-link{padding:7px 16px;border-radius:100px;text-decoration:none;font-size:13px;font-weight:500;color:var(--ink-light);transition:all .2s}
.nav-link:hover{color:var(--ink);background:var(--warm)}
.nav-link.active{background:var(--ink);color:var(--paper)}
.date-nav{display:flex;align-items:center;gap:10px}
.date-nav button{background:none;border:1px solid var(--ink-faint);border-radius:6px;padding:4px 10px;cursor:pointer;font-family:inherit;font-size:13px;color:var(--ink)}
.date-nav button:hover{background:var(--warm)}
.date-nav input[type=date]{border:1px solid var(--ink-faint);border-radius:6px;padding:4px 10px;font-family:inherit;font-size:13px;background:var(--paper);color:var(--ink)}
main{padding:36px 80px;max-width:1100px;margin:0 auto}
.matrix-header{display:flex;align-items:baseline;gap:14px;margin-bottom:32px}
.matrix-header h1{font-family:'DM Serif Display',serif;font-size:32px;font-weight:400;letter-spacing:-1px}
.matrix-header p{color:var(--ink-light)}
input[type=text]{font-family:'DM Sans',sans-serif;font-size:14px;background:transparent;border:none;outline:none;color:var(--ink);width:100%}
.matrix-wrap{position:relative;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr 1fr;border:1.5px solid var(--ink);min-height:560px}
.axis-label{position:absolute;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--ink)}
.axis-top{top:-26px;left:50%;transform:translateX(-50%)}
.axis-bottom{bottom:-26px;left:50%;transform:translateX(-50%)}
.axis-left{left:-68px;top:50%;transform:translateY(-50%) rotate(-90deg);white-space:nowrap}
.axis-right{right:-68px;top:50%;transform:translateY(-50%) rotate(90deg);white-space:nowrap}
.quadrant{padding:24px 20px;border:0.75px solid var(--ink-faint);display:flex;flex-direction:column;min-height:280px}
.q-label{font-family:'DM Serif Display',serif;font-size:20px;color:var(--ink-faint);font-style:italic;margin-bottom:3px;line-height:1.2}
.q-sub{font-size:11px;color:#ccc;margin-bottom:16px}
.q-tasks{flex:1;display:flex;flex-direction:column;gap:1px}
.q-task{display:flex;align-items:center;gap:8px;padding:7px 8px;border-radius:6px;transition:background .15s}
.q-task:hover{background:var(--warm)}
.qchk{width:14px;height:14px;border:1.5px solid var(--ink-faint);border-radius:3px;flex-shrink:0;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all .2s}
.qchk:hover{border-color:var(--accent)}
.qchk.checked{background:var(--ink);border-color:var(--ink)}
.qchk.checked::after{content:'';width:4px;height:7px;border-right:1.5px solid white;border-bottom:1.5px solid white;transform:rotate(45deg) translate(-1px,-1px);display:block}
.q-title{font-size:13px;flex:1}
.q-title.done{color:var(--ink-faint);text-decoration:line-through}
.qdel{opacity:0;background:none;border:none;cursor:pointer;color:var(--ink-light);font-size:15px;padding:0 3px;transition:all .15s}
.q-task:hover .qdel{opacity:1}
.qdel:hover{color:var(--red)}
.q-add{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:6px;border:1.5px dashed var(--ink-faint);margin-top:8px;transition:border-color .2s}
.q-add:focus-within{border-style:solid;border-color:var(--accent)}
.q-add .plus{color:var(--ink-faint);font-size:14px;flex-shrink:0}
.print-btn{background:none;border:1px solid var(--ink-faint);border-radius:6px;padding:6px 14px;cursor:pointer;font-family:inherit;font-size:13px;color:var(--ink-light);transition:all .2s;display:flex;align-items:center;gap:6px}
.print-btn:hover{border-color:var(--ink);color:var(--ink)}
@media print{
  nav,.print-btn,.qdel,.q-add{display:none!important}
  body{background:white}
  main{padding:20px}
  .matrix-wrap{border:1.5px solid #000!important}
  .quadrant{border:0.75px solid #ccc!important}
  .qchk{border:1.5px solid #999!important;print-color-adjust:exact}
  .qchk.checked{background:#000!important;print-color-adjust:exact}
}
</style>
</head>
<body>
<nav>
  <a class="brand" href="/">Planner</a>
  <div class="nav-links">
    <a class="nav-link" href="/daily?date=__TODAY__">Daily</a>
    <a class="nav-link active" href="/matrix?date=__TODAY__">Matrix</a>
  </div>
  <div class="date-nav">
    <button onclick="changeDate(-1)">&#8592;</button>
    <input type="date" value="__TODAY__" onchange="goDate(this.value)">
    <button onclick="goDate(\'__TODAY_REAL__\')">Today</button>
    <button class="print-btn" onclick="window.print()">&#128424; Print</button>
  </div>
</nav>
<main>
  <div class="matrix-header">
    <h1>Priority Matrix</h1>
    <p id="mDate"></p>
  </div>
  <div class="matrix-wrap">
    <span class="axis-label axis-top">Quick Wins</span>
    <span class="axis-label axis-bottom">Big Tasks</span>
    <span class="axis-label axis-left">Due Today</span>
    <span class="axis-label axis-right">Due Later</span>
    <div class="quadrant">
      <div class="q-label">start here</div><div class="q-sub"></div>
      <div class="q-tasks" id="q-today-quick"></div>
      <div class="q-add"><span class="plus">+</span><input type="text" placeholder="Add task&#8230;" onkeydown="addQ(event,\'today\',\'quick\')"></div>
    </div>
    <div class="quadrant">
      <div class="q-label">on hold</div><div class="q-sub">don\'t get distracted</div>
      <div class="q-tasks" id="q-later-quick"></div>
      <div class="q-add"><span class="plus">+</span><input type="text" placeholder="Add task&#8230;" onkeydown="addQ(event,\'later\',\'quick\')"></div>
    </div>
    <div class="quadrant">
      <div class="q-label">power hour</div><div class="q-sub"></div>
      <div class="q-tasks" id="q-today-complex"></div>
      <div class="q-add"><span class="plus">+</span><input type="text" placeholder="Add task&#8230;" onkeydown="addQ(event,\'today\',\'complex\')"></div>
    </div>
    <div class="quadrant">
      <div class="q-label">break into<br>smaller tasks<br>& reassign</div><div class="q-sub"></div>
      <div class="q-tasks" id="q-later-complex"></div>
      <div class="q-add"><span class="plus">+</span><input type="text" placeholder="Add task&#8230;" onkeydown="addQ(event,\'later\',\'complex\')"></div>
    </div>
  </div>
</main>
<script>
const CURRENT_DATE='__TODAY__';
const TODAY_REAL='__TODAY_REAL__';

function goDate(d){const u=new URL(location);u.searchParams.set('date',d);location=u}
function changeDate(n){const d=new Date(CURRENT_DATE+'T12:00:00');d.setDate(d.getDate()+n);goDate(d.toISOString().slice(0,10))}
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}

document.getElementById('mDate').textContent=new Date(CURRENT_DATE+'T12:00:00').toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});

function qHTML(t){
  return '<div class="q-task" id="qt-'+t.id+'">'
    +'<div class="qchk '+(t.completed?'checked':'')+'" onclick="toggleQ('+t.id+','+(t.completed?0:1)+')"></div>'
    +'<span class="q-title '+(t.completed?'done':'')+'">'+esc(t.title)+'</span>'
    +'<button class="qdel" onclick="deleteQ('+t.id+')">&#215;</button></div>';
}

async function api(method,path,body){
  const r=await fetch(path,{method,headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});
  return r.json();
}

async function loadMatrix(){
  const tasks=await api('GET','/api/tasks?date='+CURRENT_DATE);
  ['today-quick','today-complex','later-quick','later-complex'].forEach(k=>document.getElementById('q-'+k).innerHTML='');
  tasks.forEach(t=>{
    const el=document.getElementById('q-'+t.urgency+'-'+t.complexity);
    if(el)el.insertAdjacentHTML('beforeend',qHTML(t));
  });
}

async function addQ(e,urgency,complexity){
  if(e.key!=='Enter')return;
  const inp=e.target,title=inp.value.trim();if(!title)return;
  const t=await api('POST','/api/tasks',{title,task_date:CURRENT_DATE,category:complexity==='complex'?'power_hour':'todo',urgency,complexity});
  document.getElementById('q-'+urgency+'-'+complexity).insertAdjacentHTML('beforeend',qHTML(t));
  inp.value='';
}
async function toggleQ(id,val){const t=await api('PUT','/api/tasks/'+id,{completed:val});document.getElementById('qt-'+id).outerHTML=qHTML(t)}
async function deleteQ(id){await api('DELETE','/api/tasks/'+id);document.getElementById('qt-'+id).remove()}

loadMatrix();
</script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(debug=True, port=5000)
