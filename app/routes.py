from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from .storage import load_data, save_data, next_id, find_by_id, now

main = Blueprint("main", __name__)

def logged_in():
    return "user_id" in session

@main.route("/")
def index():
    return redirect(url_for("main.dashboard") if logged_in() else url_for("main.login"))

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")

        data = load_data()
        user = next(
            (u for u in data["users"]
             if u["email"].lower() == email
             and u["password"] == password
             and u["role"] == role),
            None
        )

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            return redirect(url_for("main.dashboard"))

        flash("Invalid email, password or login type.", "error")

    return render_template("login.html")

@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))

@main.route("/dashboard")
def dashboard():
    if not logged_in():
        return redirect(url_for("main.login"))

    data = load_data()
    stats = {
        "members": len(data["members"]),
        "families": len(data["families"]),
        "rescued": len(data["rescued_people"]),
        "volunteers": len(data["volunteers"])
    }
    return render_template("dashboard.html", stats=stats)

@main.route("/register", methods=["GET", "POST"])
def register():
    data = load_data()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        family_id = request.form.get("family_id", "").strip()
        family_name = request.form.get("family_name", "").strip()

        if not name:
            flash("Member name is required.", "error")
            return redirect(url_for("main.register"))

        if not family_id:
            family_id = "FAM-" + (phone[-4:] if len(phone) >= 4 else str(next_id(data["families"])).zfill(4))

        if not any(f["family_id"].lower() == family_id.lower() for f in data["families"]):
            data["families"].append({
                "id": next_id(data["families"]),
                "family_id": family_id,
                "family_name": family_name or "Registered Family"
            })

        data["members"].append({
            "id": next_id(data["members"]),
            "family_id": family_id,
            "name": name,
            "age": request.form.get("age", ""),
            "gender": request.form.get("gender", ""),
            "phone": phone,
            "relation": request.form.get("relation", ""),
            "address": request.form.get("address", "")
        })

        save_data(data)
        flash("Member registered successfully.", "success")
        return redirect(url_for("main.register"))

    family_names = {f["family_id"]: f["family_name"] for f in data["families"]}
    members = []
    for m in reversed(data["members"]):
        item = dict(m)
        item["family_name"] = family_names.get(m["family_id"], "")
        members.append(item)

    return render_template("register.html", members=members)

@main.route("/family")
def family():
    data = load_data()
    q = request.args.get("q", "").strip().lower()
    results = []

    if q:
        for member in data["members"]:
            text = " ".join([
                str(member.get("name", "")),
                str(member.get("phone", "")),
                str(member.get("family_id", "")),
                str(member.get("relation", ""))
            ]).lower()
            if q in text:
                item = dict(member)
                rescue = next(
                    (r for r in data["rescued_people"] if r["member_id"] == member["id"]),
                    None
                )
                item["community_id"] = rescue["community_id"] if rescue else "Not rescued / not registered"
                item["current_location"] = rescue["current_location"] if rescue else member.get("address", "")
                results.append(item)

    return render_template("family.html", rows=results, q=q)

@main.route("/rescue", methods=["GET", "POST"])
def rescue():
    data = load_data()

    if request.method == "POST":
        try:
            member_id = int(request.form.get("member_id"))
            team_id = int(request.form.get("team_id"))
        except (TypeError, ValueError):
            flash("Please select a valid person and rescue team.", "error")
            return redirect(url_for("main.rescue"))

        location = request.form.get("location", "").strip()
        member = find_by_id(data["members"], member_id)
        team = find_by_id(data["teams"], team_id)

        if not member or not team or not location:
            flash("Complete all rescue details.", "error")
            return redirect(url_for("main.rescue"))

        existing = next(
            (r for r in data["rescued_people"] if r["member_id"] == member_id),
            None
        )

        if existing:
            flash("This member already has a Community ID.", "error")
        else:
            cid = "CID-" + str(member_id).zfill(4)

            record = {
                "id": next_id(data["rescued_people"]),
                "member_id": member_id,
                "community_id": cid,
                "team_id": team_id,
                "team_name": team["team_name"],
                "rescue_location": location,
                "current_location": location,
                "status": "Rescued",
                "rescued_at": now()
            }

            data["rescued_people"].append(record)
            data["movement_history"].append({
                "id": next_id(data["movement_history"]),
                "community_id": cid,
                "location": location,
                "moved_at": now()
            })
            save_data(data)
            flash("Rescue record created. Community ID: " + cid, "success")

        return redirect(url_for("main.rescue"))

    selected = request.args.get("team", "")
    people = []

    for rescue_record in reversed(data["rescued_people"]):
        if selected and str(rescue_record["team_id"]) != selected:
            continue

        item = dict(rescue_record)
        member = find_by_id(data["members"], rescue_record["member_id"])
        if member:
            item.update({
                "name": member["name"],
                "phone": member["phone"],
                "family_id": member["family_id"]
            })
        people.append(item)

    return render_template(
        "rescue.html",
        teams=data["teams"],
        members=data["members"],
        people=people,
        selected=selected
    )

@main.route("/community")
def community():
    data = load_data()
    people = []

    for record in reversed(data["rescued_people"]):
        item = dict(record)
        member = find_by_id(data["members"], record["member_id"])
        if member:
            item.update({
                "name": member["name"],
                "phone": member["phone"],
                "family_id": member["family_id"]
            })

        history = [
            h for h in data["movement_history"]
            if h["community_id"] == record["community_id"]
        ]
        item["history"] = history
        people.append(item)

    return render_template("community.html", people=people)

@main.route("/volunteers", methods=["GET", "POST"])
def volunteers():
    data = load_data()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        skill = request.form.get("skill", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not skill or not phone:
            flash("Please enter all volunteer details.", "error")
            return redirect(url_for("main.volunteers"))

        volunteer_id = "VOL-" + str(next_id(data["volunteers"])).zfill(4)

        data["volunteers"].append({
            "id": next_id(data["volunteers"]),
            "volunteer_id": volunteer_id,
            "name": name,
            "skill": skill,
            "phone": phone,
            "status": "Available",
            "registered_at": now()
        })

        save_data(data)
        flash("Volunteer registered. Volunteer ID: " + volunteer_id, "success")
        return redirect(url_for("main.volunteers"))

    return render_template(
        "volunteers.html",
        volunteers=list(reversed(data["volunteers"]))
    )

@main.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "storage": "JSON file",
        "database_required": False
    })
