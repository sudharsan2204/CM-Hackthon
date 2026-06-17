from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import folium, uuid, datetime

app = Flask(__name__)
app.secret_key = "smart_tn_tvk_hackathon_2026"

# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────

complaints = []

officials = {
    "TN-ADMIN-1001": {"password": "admin@123",  "department": "ADMIN",            "name": "Admin Officer"},
    "TN-WATER-1001": {"password": "water@123",  "department": "Water Supply",     "name": "Water Dept Officer"},
    "TN-ROAD-1001":  {"password": "road@123",   "department": "Road & Transport", "name": "Road Dept Officer"},
    "TN-ELEC-1001":  {"password": "elec@123",   "department": "Electricity",      "name": "Electricity Officer"},
    "TN-SANIT-1001": {"password": "sanit@123",  "department": "Sanitation",       "name": "Sanitation Officer"},
    "TN-EDU-1001":   {"password": "edu@123",    "department": "Education",        "name": "Education Officer"},
    "TN-DRAIN-1001": {"password": "drain@123",  "department": "Drainage",         "name": "Drainage Officer"},
}

# Workers pool (assigned by officials)
workers = {
    "W001": {"name": "Rajan Kumar",    "department": "Water Supply",     "available": True},
    "W002": {"name": "Murugan S",      "department": "Water Supply",     "available": True},
    "W003": {"name": "Anbu Selvan",    "department": "Road & Transport", "available": True},
    "W004": {"name": "Karthik R",      "department": "Road & Transport", "available": True},
    "W005": {"name": "Suresh M",       "department": "Electricity",      "available": True},
    "W006": {"name": "Bala Subramani", "department": "Electricity",      "available": True},
    "W007": {"name": "Palani V",       "department": "Sanitation",       "available": True},
    "W008": {"name": "Senthil K",      "department": "Sanitation",       "available": True},
    "W009": {"name": "Mohan Raj",      "department": "Education",        "available": True},
    "W010": {"name": "Lakshmi Priya",  "department": "Education",        "available": True},
    "W011": {"name": "Vignesh T",      "department": "Drainage",         "available": True},
    "W012": {"name": "Saravanan P",    "department": "Drainage",         "available": True},
}

# ─────────────────────────────────────────────
# AI RULES
# ─────────────────────────────────────────────

rules = {
    "Water Supply":     ["water","thanni","tanni","pipe","leak","தண்ணீர்","குழாய்"],
    "Road & Transport": ["road","pothole","kuzhi","traffic","சாலை","குழி","போக்குவரத்து"],
    "Electricity":      ["current","power","light","street light","மின்சாரம்","கரண்ட்","மின்"],
    "Sanitation":       ["garbage","waste","sakkadai","குப்பை","கழிவு","சாக்கடை"],
    "Education":        ["school","teacher","education","student","scholarship","payilagam","ஆசிரியர்","பள்ளி","கல்வி","மாணவர்"],
    "Drainage":         ["drainage","drain","sewage","flood","stagnant water","sewer","வடிகால்","கழிவுநீர்","வெள்ளம்"],
}

def department_ai(text):
    text = text.lower()
    for dept, words in rules.items():
        for w in words:
            if w in text:
                return dept
    return "General Administration"

def priority_ai(text):
    high_words  = ["urgent","danger","emergency","accident","அவசரம்","ஆபத்து","உடனே"]
    med_words   = ["problem","issue","days","weeks","நாட்கள்"]
    text = text.lower()
    for w in high_words:
        if w in text: return "HIGH"
    for w in med_words:
        if w in text: return "MEDIUM"
    return "NORMAL"

# ─────────────────────────────────────────────
# SHARED CSS
# ─────────────────────────────────────────────

BASE_STYLE = """
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Tamil:wght@400;600;700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:#0a2e5c;--gold:#f5a623;--teal:#00897b;--rose:#e53935;
  --bg:#f0f4f9;--white:#fff;--grey:#6b7280;--light:#e8edf4;
  --radius:14px;--shadow:0 4px 24px rgba(10,46,92,.10);
}
body{font-family:'Inter',sans-serif;background:var(--bg);color:#1a2340;min-height:100vh}
h1,h2,h3{font-weight:800;line-height:1.2}
a{text-decoration:none;color:inherit}

/* HEADER */
.hdr{background:linear-gradient(135deg,var(--navy) 0%,#1565c0 100%);color:#fff;padding:18px 32px;display:flex;align-items:center;gap:16px}
.hdr .logo{font-size:2.4rem}
.hdr .titles h1{font-size:1.25rem;font-weight:800}
.hdr .titles p{font-size:.78rem;opacity:.75;margin-top:2px}
.hdr .badge{margin-left:auto;background:var(--gold);color:var(--navy);font-size:.7rem;font-weight:700;padding:4px 12px;border-radius:20px}

/* CARDS */
.cards{display:flex;flex-wrap:wrap;gap:16px;padding:24px 32px 0}
.card{background:var(--white);border-radius:var(--radius);box-shadow:var(--shadow);padding:22px 28px;min-width:160px;flex:1}
.card .num{font-size:2.2rem;font-weight:800;color:var(--navy)}
.card .lbl{font-size:.78rem;color:var(--grey);margin-top:4px}
.card.gold .num{color:var(--gold)}
.card.teal .num{color:var(--teal)}
.card.rose .num{color:var(--rose)}

/* SECTION */
.section{margin:24px 32px;background:var(--white);border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden}
.section-hdr{padding:16px 24px;border-bottom:2px solid var(--light);font-size:1rem;font-weight:700;display:flex;align-items:center;gap:8px}

/* TABLE */
table{width:100%;border-collapse:collapse}
th{background:var(--navy);color:#fff;padding:11px 14px;text-align:left;font-size:.78rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px}
td{padding:11px 14px;border-bottom:1px solid var(--light);font-size:.85rem;vertical-align:middle}
tr:last-child td{border:none}
tr:hover td{background:#f8faff}

/* BADGES */
.badge-high{background:#fde8e8;color:#c62828;padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700}
.badge-med{background:#fff3e0;color:#e65100;padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700}
.badge-norm{background:#e8f5e9;color:#2e7d32;padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700}
.badge-recv{background:#e3f2fd;color:#1565c0;padding:3px 8px;border-radius:20px;font-size:.72rem}
.badge-acc{background:#e8f5e9;color:#2e7d32;padding:3px 8px;border-radius:20px;font-size:.72rem}
.badge-work{background:#fff3e0;color:#e65100;padding:3px 8px;border-radius:20px;font-size:.72rem}
.badge-res{background:#f3e5f5;color:#6a1b9a;padding:3px 8px;border-radius:20px;font-size:.72rem}

/* BUTTONS */
.btn{display:inline-block;padding:8px 16px;border-radius:8px;font-size:.8rem;font-weight:600;border:none;cursor:pointer;transition:.2s}
.btn-primary{background:var(--navy);color:#fff}
.btn-success{background:var(--teal);color:#fff}
.btn-warning{background:var(--gold);color:var(--navy)}
.btn-danger{background:var(--rose);color:#fff}
.btn:hover{opacity:.88;transform:translateY(-1px)}

/* FORM */
.form-wrap{max-width:560px;margin:40px auto;background:var(--white);border-radius:20px;box-shadow:var(--shadow);overflow:hidden}
.form-hdr{background:linear-gradient(135deg,var(--navy),#1565c0);padding:28px 32px;color:#fff}
.form-hdr h2{font-size:1.4rem}
.form-hdr p{font-size:.82rem;opacity:.75;margin-top:6px}
.form-body{padding:28px 32px}
.field{margin-bottom:20px}
label{display:block;font-size:.82rem;font-weight:600;color:var(--navy);margin-bottom:6px}
input,textarea,select{width:100%;padding:11px 14px;border:1.5px solid #d1d9e6;border-radius:10px;font-size:.9rem;font-family:'Inter',sans-serif;transition:.2s}
input:focus,textarea:focus,select:focus{outline:none;border-color:var(--navy);box-shadow:0 0 0 3px rgba(10,46,92,.12)}
textarea{resize:vertical;min-height:90px}
.submit-btn{width:100%;padding:14px;background:linear-gradient(135deg,var(--navy),#1565c0);color:#fff;border:none;border-radius:10px;font-size:1rem;font-weight:700;cursor:pointer;transition:.2s}
.submit-btn:hover{opacity:.9;transform:translateY(-1px)}

/* LANG BAR */
.lang-bar{background:#fff;border-bottom:2px solid var(--light);padding:8px 32px;display:flex;align-items:center;gap:10px;font-size:.8rem;font-weight:600;color:var(--grey)}
.lang-btn{padding:5px 14px;border-radius:20px;border:1.5px solid #d1d9e6;cursor:pointer;background:#fff;font-size:.78rem;transition:.2s}
.lang-btn.active,.lang-btn:hover{background:var(--navy);color:#fff;border-color:var(--navy)}

/* FOOTER */
.footer{background:var(--navy);color:#fff;text-align:center;padding:16px;font-size:.78rem;opacity:.85;margin-top:32px}

/* LANDING */
.landing{min-height:100vh;background:linear-gradient(160deg,var(--navy) 0%,#1a3a6e 60%,#0d47a1 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:32px}
.landing .emblem{font-size:5rem;margin-bottom:12px}
.landing h1{font-size:2.2rem;color:#fff;font-weight:800;line-height:1.1}
.landing .sub{color:#90caf9;font-size:1rem;margin:10px 0 28px}
.landing .team{background:var(--gold);color:var(--navy);font-weight:800;font-size:1rem;padding:6px 22px;border-radius:20px;margin-bottom:32px;display:inline-block}
.landing .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;width:100%;max-width:900px}
.dash-card{background:rgba(255,255,255,.08);border:1.5px solid rgba(255,255,255,.18);border-radius:18px;padding:28px 20px;color:#fff;cursor:pointer;transition:.25s;text-align:center}
.dash-card:hover{background:rgba(255,255,255,.16);transform:translateY(-4px);border-color:var(--gold)}
.dash-card .icon{font-size:2.4rem;margin-bottom:10px}
.dash-card h3{font-size:1rem;font-weight:700}
.dash-card p{font-size:.78rem;opacity:.65;margin-top:6px}

/* ASSIGN MODAL area */
.assign-row{display:flex;align-items:center;gap:8px}
select.small{padding:6px 10px;font-size:.78rem;border-radius:8px;border:1.5px solid #d1d9e6;width:auto}
</style>
"""

# ─────────────────────────────────────────────
# DASHBOARD 1 — CM HACKATHON LANDING
# ─────────────────────────────────────────────

@app.route("/")
def home():
    return render_template_string(BASE_STYLE + """
<div class="landing">
  <div class="emblem">🏛️</div>
  <h1>Tamil Nadu Smart Grievance Portal</h1>
  <p class="sub">AI-Powered Public Governance System · CM Hackathon 2026</p>
  <div class="team">👥 Team TVK</div>

  <div class="grid">

    <a href="/citizen" class="dash-card">
      <div class="icon">🙋</div>
      <h3>Citizen Portal</h3>
      <p>File complaints & track status</p>
    </a>

    <a href="/official" class="dash-card">
      <div class="icon">🏢</div>
      <h3>Official Dashboard</h3>
      <p>Government officer login</p>
    </a>

    <a href="/track" class="dash-card">
      <div class="icon">🔍</div>
      <h3>Track Complaint</h3>
      <p>Check your complaint status</p>
    </a>

    <a href="/map" target="_blank" class="dash-card">
      <div class="icon">📍</div>
      <h3>Heatmap</h3>
      <p>Tamil Nadu complaint map</p>
    </a>

  </div>

  <p style="color:#90caf9;font-size:.75rem;margin-top:32px">
    Built for CM's Hackathon · Prototype Smart Governance System · Team TVK
  </p>
</div>
""")


# ─────────────────────────────────────────────
# DASHBOARD 3 — LANGUAGE SELECTION + CITIZEN PORTAL
# ─────────────────────────────────────────────

LANG_LABELS = {
    "en": {
        "title":       "Citizen Complaint Portal",
        "sub":         "Register your complaint — we'll route it to the right department",
        "name":        "Full Name",
        "phone":       "Mobile Number",
        "district":    "District",
        "complaint":   "Your Complaint",
        "comp_ph":     "Describe your issue clearly…",
        "submit":      "Submit Complaint",
        "track_link":  "Track existing complaint",
    },
    "ta": {
        "title":       "குடிமக்கள் புகார் போர்டல்",
        "sub":         "உங்கள் புகாரை பதிவு செய்யுங்கள்",
        "name":        "முழு பெயர்",
        "phone":       "கைபேசி எண்",
        "district":    "மாவட்டம்",
        "complaint":   "உங்கள் புகார்",
        "comp_ph":     "உங்கள் பிரச்சினையை விவரிக்கவும்…",
        "submit":      "புகார் சமர்ப்பிக்கவும்",
        "track_link":  "புகாரை கண்காணிக்கவும்",
    },
    "tg": {
        "title":       "Citizen Complaint Portal",
        "sub":         "Ungal complaint register pannunga — right department-ku send pannuvom",
        "name":        "Full Peyar",
        "phone":       "Mobile Number",
        "district":    "District",
        "complaint":   "Ungal Complaint",
        "comp_ph":     "Ungal issue pathi sollunga…",
        "submit":      "Complaint Submit Pannunga",
        "track_link":  "Complaint track pannunga",
    },
}

@app.route("/citizen")
def citizen():
    lang = request.args.get("lang", "en")
    L = LANG_LABELS.get(lang, LANG_LABELS["en"])
    return render_template_string(BASE_STYLE + """
<div style="background:var(--bg);min-height:100vh;padding-bottom:40px">

  <!-- Header -->
  <div class="hdr">
    <div class="logo">🙋</div>
    <div class="titles">
      <h1>Tamil Nadu Smart Grievance Portal</h1>
      <p>Citizen Complaint Registration</p>
    </div>
    <span class="badge">Team TVK</span>
  </div>

  <!-- Language Bar -->
  <div class="lang-bar">
    🌐 Language:&nbsp;
    <a href="/citizen?lang=en"><button class="lang-btn {{ 'active' if lang=='en' else '' }}">English</button></a>
    <a href="/citizen?lang=ta"><button class="lang-btn {{ 'active' if lang=='ta' else '' }}">தமிழ்</button></a>
    <a href="/citizen?lang=tg"><button class="lang-btn {{ 'active' if lang=='tg' else '' }}">Tanglish</button></a>
  </div>

  <!-- Form -->
  <div class="form-wrap" style="margin-top:32px">
    <div class="form-hdr">
      <h2>{{ L.title }}</h2>
      <p>{{ L.sub }}</p>
    </div>
    <div class="form-body">
      <form action="/submit" method="post">
        <input type="hidden" name="lang" value="{{ lang }}">

        <div class="field">
          <label>{{ L.name }}</label>
          <input name="name" required placeholder="e.g. Ramesh Kumar">
        </div>

        <div class="field">
          <label>{{ L.phone }}</label>
          <input name="phone" required placeholder="9XXXXXXXXX">
        </div>

        <div class="field">
          <label>{{ L.district }}</label>
          <select name="district">
            <option>Chennai</option><option>Coimbatore</option><option>Madurai</option>
            <option>Salem</option><option>Trichy</option><option>Tirunelveli</option>
            <option>Vellore</option><option>Erode</option><option>Thanjavur</option>
            <option>Kancheepuram</option>
          </select>
        </div>

        <div class="field">
          <label>{{ L.complaint }}</label>
          <textarea name="complaint" required placeholder="{{ L.comp_ph }}"></textarea>
        </div>

        <button class="submit-btn" type="submit">{{ L.submit }}</button>
      </form>

      <p style="text-align:center;margin-top:16px;font-size:.82rem">
        <a href="/track" style="color:var(--navy);font-weight:600">🔍 {{ L.track_link }}</a>
        &nbsp;|&nbsp;
        <a href="/" style="color:var(--grey)">← Home</a>
      </p>
    </div>
  </div>
</div>
""", L=L, lang=lang)


# ─────────────────────────────────────────────
# SUBMIT
# ─────────────────────────────────────────────

@app.route("/submit", methods=["POST"])
def submit():
    data = request.form
    cid  = "TN" + str(2024000 + len(complaints) + 1)
    now  = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")

    c = {
        "id":         cid,
        "name":       data["name"],
        "phone":      data["phone"],
        "district":   data["district"],
        "text":       data["complaint"],
        "department": department_ai(data["complaint"]),
        "priority":   priority_ai(data["complaint"]),
        "status":     "Received",
        "submitted":  now,
        "assigned_to": None,
    }
    complaints.append(c)

    p_color = {"HIGH":"#e53935","MEDIUM":"#fb8c00","NORMAL":"#43a047"}.get(c["priority"],"#43a047")

    return render_template_string(BASE_STYLE + f"""
<div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:var(--bg);padding:32px">
  <div style="background:var(--white);border-radius:20px;box-shadow:var(--shadow);padding:36px 40px;max-width:480px;width:100%;text-align:center">
    <div style="font-size:3.5rem">✅</div>
    <h2 style="color:var(--teal);margin:12px 0 4px">Complaint Submitted!</h2>
    <p style="color:var(--grey);font-size:.9rem">Your complaint has been registered successfully.</p>

    <div style="background:var(--light);border-radius:12px;padding:20px;margin:20px 0;text-align:left">
      <div style="font-size:.75rem;color:var(--grey);font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">Complaint ID</div>
      <div style="font-size:2rem;font-weight:800;color:var(--navy);letter-spacing:2px">{cid}</div>
    </div>

    <table style="width:100%;font-size:.85rem">
      <tr><td style="color:var(--grey);padding:5px 0">Department</td><td style="font-weight:600;text-align:right">{c['department']}</td></tr>
      <tr><td style="color:var(--grey);padding:5px 0">Priority</td>
          <td style="text-align:right"><span style="background:{p_color};color:#fff;padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:700">{c['priority']}</span></td></tr>
      <tr><td style="color:var(--grey);padding:5px 0">Status</td><td style="text-align:right">Received</td></tr>
      <tr><td style="color:var(--grey);padding:5px 0">Submitted</td><td style="font-weight:600;text-align:right">{now}</td></tr>
    </table>

    <p style="font-size:.78rem;color:var(--grey);margin:16px 0">Save your Complaint ID to track status anytime.</p>

    <a href="/track"><button class="btn btn-primary" style="width:100%;padding:12px;font-size:.9rem;margin-bottom:10px">🔍 Track This Complaint</button></a>
    <a href="/citizen"><button class="btn" style="width:100%;padding:12px;font-size:.9rem;background:var(--light);color:var(--navy)">← Submit Another</button></a>
  </div>
</div>
""")


# ─────────────────────────────────────────────
# TRACK
# ─────────────────────────────────────────────

@app.route("/track")
def track():
    cid    = request.args.get("id","")
    result = None
    if cid:
        for c in complaints:
            if c["id"].upper() == cid.upper():
                result = c
                break

    status_steps = ["Received","Accepted","Work Started","Resolved"]

    return render_template_string(BASE_STYLE + """
<div style="min-height:100vh;background:var(--bg);padding-bottom:40px">
  <div class="hdr">
    <div class="logo">🔍</div>
    <div class="titles">
      <h1>Track Complaint</h1>
      <p>Enter your Complaint ID to check status</p>
    </div>
    <span class="badge">Team TVK</span>
  </div>

  <div style="max-width:560px;margin:36px auto;padding:0 16px">
    <form method="get" action="/track" style="display:flex;gap:10px">
      <input name="id" value="{{ cid }}" placeholder="e.g. TN2024001" style="flex:1;padding:12px 16px;border-radius:10px;border:1.5px solid #d1d9e6;font-size:.95rem">
      <button class="btn btn-primary" type="submit" style="padding:12px 22px;font-size:.9rem">Search</button>
    </form>

    {% if cid and not result %}
    <div style="background:#fde8e8;border-radius:12px;padding:18px;margin-top:20px;color:#c62828;text-align:center">
      ❌ Complaint ID <b>{{ cid }}</b> not found. Please check and try again.
    </div>
    {% endif %}

    {% if result %}
    <div style="background:var(--white);border-radius:16px;box-shadow:var(--shadow);padding:28px;margin-top:24px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
        <div>
          <div style="font-size:.72rem;color:var(--grey);font-weight:600;text-transform:uppercase;letter-spacing:.5px">Complaint ID</div>
          <div style="font-size:1.5rem;font-weight:800;color:var(--navy)">{{ result.id }}</div>
        </div>
        {% if result.priority == 'HIGH' %}<span class="badge-high">HIGH PRIORITY</span>
        {% elif result.priority == 'MEDIUM' %}<span class="badge-med">MEDIUM</span>
        {% else %}<span class="badge-norm">NORMAL</span>{% endif %}
      </div>

      <!-- Progress -->
      <div style="margin-bottom:22px">
        <div style="display:flex;justify-content:space-between;margin-bottom:8px">
          {% for step in steps %}
          <div style="text-align:center;flex:1">
            <div style="width:28px;height:28px;border-radius:50%;margin:0 auto 4px;font-size:.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;
              background:{{ '#0a2e5c' if result.status == step or steps.index(step) < steps.index(result.status) else '#d1d9e6' }};
              color:{{ '#fff' if result.status == step or steps.index(step) <= steps.index(result.status) else '#888' }}">
              {{ loop.index }}
            </div>
            <div style="font-size:.65rem;color:{{ '#0a2e5c' if result.status==step else '#aaa' }};font-weight:{{ '700' if result.status==step else '400' }}">{{ step }}</div>
          </div>
          {% endfor %}
        </div>
      </div>

      <table style="width:100%;font-size:.87rem">
        <tr><td style="color:var(--grey);padding:6px 0">Name</td><td style="font-weight:600;text-align:right">{{ result.name }}</td></tr>
        <tr><td style="color:var(--grey);padding:6px 0">District</td><td style="font-weight:600;text-align:right">{{ result.district }}</td></tr>
        <tr><td style="color:var(--grey);padding:6px 0">Department</td><td style="font-weight:600;text-align:right">{{ result.department }}</td></tr>
        <tr><td style="color:var(--grey);padding:6px 0">Submitted</td><td style="font-weight:600;text-align:right">{{ result.submitted }}</td></tr>
        {% if result.assigned_to %}
        <tr><td style="color:var(--grey);padding:6px 0">Assigned To</td><td style="font-weight:600;text-align:right;color:var(--teal)">{{ result.assigned_to }}</td></tr>
        {% endif %}
      </table>

      <div style="background:var(--light);border-radius:10px;padding:14px;margin-top:16px;font-size:.85rem;color:#333">
        <b>Complaint:</b> {{ result.text }}
      </div>
    </div>
    {% endif %}

    <p style="text-align:center;margin-top:20px;font-size:.82rem">
      <a href="/" style="color:var(--grey)">← Back to Home</a>
    </p>
  </div>
</div>
""", cid=cid, result=result, steps=status_steps)


# ─────────────────────────────────────────────
# DASHBOARD 2 — OFFICIAL LOGIN (with title in form)
# ─────────────────────────────────────────────

@app.route("/official")
def official():
    return render_template_string(BASE_STYLE + """
<div style="min-height:100vh;background:linear-gradient(160deg,#0a2e5c 0%,#1565c0 100%);display:flex;align-items:center;justify-content:center;padding:32px">

  <div style="background:var(--white);border-radius:22px;box-shadow:0 20px 60px rgba(0,0,0,.25);overflow:hidden;width:100%;max-width:440px">

    <!-- Form Header -->
    <div style="background:linear-gradient(135deg,#0a2e5c,#1565c0);padding:28px 32px;text-align:center;color:#fff">
      <div style="font-size:2.8rem">🏢</div>
      <h2 style="margin-top:8px;font-size:1.3rem">Government Official Login</h2>
      <p style="font-size:.8rem;opacity:.7;margin-top:4px">Tamil Nadu Smart Grievance Portal</p>
      <div style="background:var(--gold);color:var(--navy);font-size:.7rem;font-weight:700;padding:3px 14px;border-radius:20px;display:inline-block;margin-top:8px">
        Team TVK · CM Hackathon 2026
      </div>
    </div>

    <div style="padding:28px 32px">

      {% if error %}
      <div style="background:#fde8e8;color:#c62828;border-radius:10px;padding:12px 16px;margin-bottom:18px;font-size:.85rem">
        ❌ {{ error }}
      </div>
      {% endif %}

      <form action="/login" method="post">
        <div class="field">
          <label>Register Number</label>
          <input name="id" placeholder="e.g. TN-WATER-1001" required autocomplete="username">
        </div>

        <div class="field">
          <label>Password</label>
          <input type="password" name="password" placeholder="••••••••" required autocomplete="current-password">
        </div>

        <button class="submit-btn" type="submit">Login →</button>
      </form>

      <div style="margin-top:20px;background:#f0f4f9;border-radius:10px;padding:14px;font-size:.75rem;color:var(--grey)">
        <b>Demo Credentials</b><br>
        Admin: TN-ADMIN-1001 / admin@123<br>
        Water: TN-WATER-1001 / water@123<br>
        Road: TN-ROAD-1001 / road@123<br>
        Electricity: TN-ELEC-1001 / elec@123<br>
        Sanitation: TN-SANIT-1001 / sanit@123<br>
        Education: TN-EDU-1001 / edu@123<br>
        Drainage: TN-DRAIN-1001 / drain@123
      </div>

      <p style="text-align:center;margin-top:16px;font-size:.82rem">
        <a href="/" style="color:var(--grey)">← Back to Home</a>
      </p>
    </div>
  </div>
</div>
""", error=request.args.get("error",""))


@app.route("/login", methods=["POST"])
def login():
    uid = request.form["id"].strip()
    pwd = request.form["password"].strip()
    if uid in officials and officials[uid]["password"] == pwd:
        session["official"] = uid
        return redirect("/dashboard")
    return redirect("/official?error=Invalid+register+number+or+password")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ─────────────────────────────────────────────
# DASHBOARD 4 — OFFICIAL DASHBOARD (accept + assign workers)
# ─────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    if "official" not in session:
        return redirect("/official")

    uid   = session["official"]
    dept  = officials[uid]["department"]
    oname = officials[uid]["name"]

    if dept == "ADMIN":
        data = complaints
    else:
        data = [c for c in complaints if c["department"] == dept]

    total    = len(data)
    pending  = len([c for c in data if c["status"] != "Resolved"])
    resolved = len([c for c in data if c["status"] == "Resolved"])
    high_p   = len([c for c in data if c["priority"] == "HIGH"])

    # Workers for this dept (or all for admin)
    if dept == "ADMIN":
        dept_workers = workers
    else:
        dept_workers = {k: v for k, v in workers.items() if v["department"] == dept}

    dept_counts = {}
    for c in complaints:
        dept_counts[c["department"]] = dept_counts.get(c["department"], 0) + 1

    return render_template_string(BASE_STYLE + """
<div style="background:var(--bg);min-height:100vh;padding-bottom:40px">

  <!-- Header -->
  <div class="hdr">
    <div class="logo">🏢</div>
    <div class="titles">
      <h1>Tamil Nadu Smart Governance Dashboard</h1>
      <p>AI-Powered Public Grievance Monitoring · {{ dept }}</p>
    </div>
    <span class="badge">Team TVK</span>
    <a href="/logout" style="margin-left:12px"><button class="btn" style="background:rgba(255,255,255,.15);color:#fff;font-size:.75rem;padding:6px 12px">Logout</button></a>
  </div>

  <!-- Officer Info Bar -->
  <div style="background:#fff;border-bottom:2px solid var(--light);padding:10px 32px;display:flex;align-items:center;gap:10px;font-size:.85rem">
    👤 <b>{{ oname }}</b> &nbsp;|&nbsp; Register No: <b>{{ uid }}</b> &nbsp;|&nbsp; Department: <b>{{ dept }}</b>
  </div>

  <!-- Stat Cards -->
  <div class="cards">
    <div class="card"><div class="num">{{ total }}</div><div class="lbl">Total Complaints</div></div>
    <div class="card gold"><div class="num">{{ pending }}</div><div class="lbl">Pending</div></div>
    <div class="card teal"><div class="num">{{ resolved }}</div><div class="lbl">Resolved</div></div>
    <div class="card rose"><div class="num">{{ high_p }}</div><div class="lbl">High Priority</div></div>
  </div>

  <!-- Map -->
  <div class="section" style="margin-top:24px">
    <div class="section-hdr">📍 Tamil Nadu Complaint Heatmap</div>
    <iframe src="/map" width="100%" height="420" style="border:none"></iframe>
  </div>

  <!-- Analytics -->
  <div class="section">
    <div class="section-hdr">📊 Department-wise Analytics</div>
    <div style="padding:20px">
      <canvas id="chart" style="max-height:260px"></canvas>
    </div>
  </div>

  <!-- Workers -->
  <div class="section">
    <div class="section-hdr">👷 Field Workers — {{ dept }}</div>
    <table>
      <tr><th>Worker ID</th><th>Name</th><th>Department</th><th>Status</th></tr>
      {% for wid, w in dept_workers.items() %}
      <tr>
        <td>{{ wid }}</td>
        <td>{{ w.name }}</td>
        <td>{{ w.department }}</td>
        <td>
          {% if w.available %}
          <span class="badge-acc">Available</span>
          {% else %}
          <span class="badge-work">On Task</span>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </table>
  </div>

  <!-- Complaints Control -->
  <div class="section">
    <div class="section-hdr">📋 Complaint Control Panel</div>
    <table>
      <tr>
        <th>ID</th><th>Name</th><th>District</th><th>Department</th>
        <th>Priority</th><th>Status</th><th>Assigned To</th><th>Actions</th>
      </tr>
      {% for c in data %}
      <tr>
        <td><b>{{ c.id }}</b></td>
        <td>{{ c.name }}</td>
        <td>{{ c.district }}</td>
        <td>{{ c.department }}</td>
        <td>
          {% if c.priority=='HIGH' %}<span class="badge-high">HIGH</span>
          {% elif c.priority=='MEDIUM' %}<span class="badge-med">MED</span>
          {% else %}<span class="badge-norm">NORM</span>{% endif %}
        </td>
        <td>
          {% if c.status=='Received' %}<span class="badge-recv">{{ c.status }}</span>
          {% elif c.status=='Accepted' %}<span class="badge-acc">{{ c.status }}</span>
          {% elif c.status=='Work Started' %}<span class="badge-work">{{ c.status }}</span>
          {% else %}<span class="badge-res">{{ c.status }}</span>{% endif %}
        </td>
        <td style="color:var(--teal);font-weight:600">{{ c.assigned_to or '—' }}</td>
        <td>
          <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
            {% if c.status == 'Received' %}
              <a href="/accept/{{ c.id }}"><button class="btn btn-success" style="font-size:.72rem;padding:5px 10px">✅ Accept</button></a>
            {% endif %}
            {% if c.status == 'Accepted' %}
              <!-- Assign Worker -->
              <form action="/assign/{{ c.id }}" method="post" style="display:flex;gap:6px;align-items:center">
                <select name="worker_id" class="small">
                  {% for wid, w in dept_workers.items() %}
                    {% if w.available %}
                    <option value="{{ wid }}">{{ w.name }}</option>
                    {% endif %}
                  {% endfor %}
                </select>
                <button class="btn btn-warning" type="submit" style="font-size:.72rem;padding:5px 10px">🔧 Assign</button>
              </form>
            {% endif %}
            {% if c.status == 'Work Started' %}
              <a href="/resolve/{{ c.id }}"><button class="btn btn-primary" style="font-size:.72rem;padding:5px 10px">🏁 Resolve</button></a>
            {% endif %}
            {% if c.status == 'Resolved' %}
              <span style="color:var(--teal);font-size:.8rem;font-weight:600">✔ Done</span>
            {% endif %}
          </div>
        </td>
      </tr>
      {% endfor %}
      {% if data|length == 0 %}
      <tr><td colspan="8" style="text-align:center;color:var(--grey);padding:28px">No complaints in your department yet.</td></tr>
      {% endif %}
    </table>
  </div>

</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
const labels = {{ dept_labels | tojson }};
const counts = {{ dept_counts_list | tojson }};
new Chart(document.getElementById("chart"),{
  type:"bar",
  data:{
    labels:labels,
    datasets:[{
      label:"Complaints by Department",
      data:counts,
      backgroundColor:["#1565c0","#00897b","#f5a623","#e53935","#8e24aa","#3949ab","#00838f"],
      borderRadius:8,
      borderSkipped:false
    }]
  },
  options:{
    responsive:true,
    plugins:{legend:{display:false}},
    scales:{y:{beginAtZero:true,grid:{color:"#f0f4f9"}},x:{grid:{display:false}}}
  }
});
</script>
<div class="footer">Tamil Nadu Smart Governance System · Team TVK · CM Hackathon 2026 · Prototype</div>
""",
    uid=uid, oname=oname, dept=dept,
    total=total, pending=pending, resolved=resolved, high_p=high_p,
    data=data,
    dept_workers=dept_workers,
    dept_labels=list(dept_counts.keys()),
    dept_counts_list=list(dept_counts.values()),
)


# ─────────────────────────────────────────────
# STATUS TRANSITIONS
# ─────────────────────────────────────────────

@app.route("/accept/<cid>")
def accept(cid):
    for c in complaints:
        if c["id"] == cid:
            c["status"] = "Accepted"
    return redirect("/dashboard")

@app.route("/assign/<cid>", methods=["POST"])
def assign(cid):
    wid = request.form.get("worker_id")
    for c in complaints:
        if c["id"] == cid:
            if wid and wid in workers:
                c["assigned_to"] = workers[wid]["name"]
                workers[wid]["available"] = False
                c["status"] = "Work Started"
    return redirect("/dashboard")

@app.route("/resolve/<cid>")
def resolve(cid):
    for c in complaints:
        if c["id"] == cid:
            # Free the worker
            for wid, w in workers.items():
                if w["name"] == c.get("assigned_to"):
                    w["available"] = True
            c["status"] = "Resolved"
    return redirect("/dashboard")


# ─────────────────────────────────────────────
# MAP
# ─────────────────────────────────────────────

@app.route("/map")
def map_view():
    m = folium.Map(location=[11.1271, 78.6569], zoom_start=7, tiles="CartoDB positron")

    district_data = {}
    for c in complaints:
        d = c["district"]
        district_data[d] = district_data.get(d, 0) + 1

    static_places = [
        ("Chennai",    13.08, 80.27, 500),
        ("Madurai",     9.92, 78.11, 200),
        ("Coimbatore", 11.01, 76.95, 300),
        ("Salem",      11.66, 78.14, 150),
        ("Trichy",     10.79, 78.70, 180),
        ("Vellore",    12.92, 79.13, 120),
    ]

    for city, lat, lon, count in static_places:
        count += district_data.get(city, 0)
        folium.CircleMarker(
            [lat, lon],
            radius=max(8, count / 30),
            color="#0a2e5c",
            fill=True,
            fill_color="#1565c0",
            fill_opacity=0.6,
            popup=folium.Popup(f"<b>{city}</b><br>Complaints: {count}", max_width=160)
        ).add_to(m)

    return m._repr_html_()

# Vercel entry point
app = app

if __name__ == "__main__":
    app.run(debug=True)
