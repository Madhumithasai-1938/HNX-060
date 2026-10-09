from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from difflib import SequenceMatcher
from datetime import datetime


app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "resqlink.db")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# DATABASE SETUP AND MIGRATION
# =========================================================

def init_db():

    conn = get_db_connection()

    # -----------------------------------------------------
    # FAMILY MEMBERS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS family_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            contact TEXT,
            family_member_name TEXT,
            relationship TEXT
        )
    """)

    # -----------------------------------------------------
    # RESCUE MEMBERS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS rescue_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            team TEXT
        )
    """)

    # -----------------------------------------------------
    # MISSING PERSONS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS missing_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT,
            name TEXT,
            age INTEGER,
            description TEXT,
            last_location TEXT,
            contact TEXT
        )
    """)

    # -----------------------------------------------------
    # FOUND PERSONS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS found_persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            description TEXT,
            current_location TEXT,
            status TEXT
        )
    """)

    # -----------------------------------------------------
    # MATCH VERIFICATIONS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS match_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            missing_id INTEGER,
            found_id INTEGER,
            match_score REAL NOT NULL DEFAULT 0,
            status TEXT,
            verified_at TEXT
        )
    """)

    conn.commit()

    # =====================================================
    # MIGRATE FAMILY MEMBERS TABLE
    # =====================================================

    existing_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(family_members)"
        ).fetchall()
    ]

    family_columns = {
        "name": "TEXT",
        "age": "INTEGER",
        "contact": "TEXT",
        "family_member_name": "TEXT",
        "relationship": "TEXT"
    }

    for column, column_type in family_columns.items():

        if column not in existing_columns:

            conn.execute(
                f"ALTER TABLE family_members "
                f"ADD COLUMN {column} {column_type}"
            )

    # =====================================================
    # MIGRATE RESCUE MEMBERS TABLE
    # =====================================================

    existing_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(rescue_members)"
        ).fetchall()
    ]

    rescue_columns = {
        "name": "TEXT",
        "age": "INTEGER",
        "team": "TEXT"
    }

    for column, column_type in rescue_columns.items():

        if column not in existing_columns:

            conn.execute(
                f"ALTER TABLE rescue_members "
                f"ADD COLUMN {column} {column_type}"
            )

    # =====================================================
    # MIGRATE MISSING PERSONS TABLE
    # =====================================================

    existing_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(missing_persons)"
        ).fetchall()
    ]

    missing_columns = {
        "case_id": "TEXT",
        "name": "TEXT",
        "age": "INTEGER",
        "description": "TEXT",
        "last_location": "TEXT",
        "contact": "TEXT"
    }

    for column, column_type in missing_columns.items():

        if column not in existing_columns:

            conn.execute(
                f"ALTER TABLE missing_persons "
                f"ADD COLUMN {column} {column_type}"
            )

    # =====================================================
    # MIGRATE FOUND PERSONS TABLE
    # =====================================================

    existing_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(found_persons)"
        ).fetchall()
    ]

    found_columns = {
        "name": "TEXT",
        "age": "INTEGER",
        "description": "TEXT",
        "current_location": "TEXT",
        "status": "TEXT"
    }

    for column, column_type in found_columns.items():

        if column not in existing_columns:

            conn.execute(
                f"ALTER TABLE found_persons "
                f"ADD COLUMN {column} {column_type}"
            )

    # =====================================================
    # MIGRATE MATCH VERIFICATIONS TABLE
    # =====================================================

    existing_columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(match_verifications)"
        ).fetchall()
    ]

    verification_columns = {
        "missing_id": "INTEGER",
        "found_id": "INTEGER",
        "match_score": "REAL NOT NULL DEFAULT 0",
        "status": "TEXT",
        "verified_at": "TEXT"
    }

    for column, column_type in verification_columns.items():

        if column not in existing_columns:

            conn.execute(
                f"ALTER TABLE match_verifications "
                f"ADD COLUMN {column} {column_type}"
            )

    conn.commit()

    # =====================================================
    # CREATE CASE IDs FOR OLD MISSING RECORDS
    # =====================================================

    old_records = conn.execute("""
        SELECT id
        FROM missing_persons
        WHERE case_id IS NULL
        OR case_id = ''
    """).fetchall()

    for record in old_records:

        case_id = (
            "RQL-OLD-"
            + str(record["id"]).zfill(4)
        )

        conn.execute("""
            UPDATE missing_persons
            SET case_id = ?
            WHERE id = ?
        """, (
            case_id,
            record["id"]
        ))

    conn.commit()

    conn.close()


# =========================================================
# TEXT SIMILARITY
# =========================================================

def text_similarity(text1, text2):

    text1 = str(text1 or "").lower().strip()
    text2 = str(text2 or "").lower().strip()

    if not text1 or not text2:
        return 0

    return SequenceMatcher(
        None,
        text1,
        text2
    ).ratio()


# =========================================================
# MATCH SCORE
# =========================================================

def calculate_match_score(missing, found):

    # -----------------------------------------------------
    # NAME = 40%
    # -----------------------------------------------------

    name_score = text_similarity(
        missing["name"],
        found["name"]
    )

    # -----------------------------------------------------
    # AGE = 25%
    # -----------------------------------------------------

    try:

        missing_age = int(missing["age"])
        found_age = int(found["age"])

        difference = abs(
            missing_age - found_age
        )

        if difference == 0:
            age_score = 1

        elif difference == 1:
            age_score = 0.7

        elif difference == 2:
            age_score = 0.4

        else:
            age_score = 0

    except:

        age_score = 0

    # -----------------------------------------------------
    # DESCRIPTION = 20%
    # -----------------------------------------------------

    description_score = text_similarity(
        missing["description"],
        found["description"]
    )

    # -----------------------------------------------------
    # LOCATION = 15%
    # -----------------------------------------------------

    location_score = text_similarity(
        missing["last_location"],
        found["current_location"]
    )

    # -----------------------------------------------------
    # TOTAL SCORE
    # -----------------------------------------------------

    total_score = (
        (name_score * 40)
        + (age_score * 25)
        + (description_score * 20)
        + (location_score * 15)
    )

    return round(total_score, 2)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "home.html"
    )


# =========================================================
# REGISTRATION OPTIONS
# =========================================================

@app.route("/registration")
def registration():

    return render_template(
        "registration.html"
    )


# =========================================================
# MAIN DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    conn = get_db_connection()

    # -----------------------------------------------------
    # COUNTS
    # -----------------------------------------------------

    family_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM family_members
    """).fetchone()["count"]

    missing_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM missing_persons
    """).fetchone()["count"]

    found_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM found_persons
    """).fetchone()["count"]

    verified_count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM match_verifications
        WHERE status = 'Verified'
    """).fetchone()["count"]

    # -----------------------------------------------------
    # MISSING PERSON LIST
    # -----------------------------------------------------

    missing_records = conn.execute("""
        SELECT *
        FROM missing_persons
        ORDER BY id DESC
    """).fetchall()

    dashboard_persons = []

    for person in missing_records:

        verification = conn.execute("""
            SELECT *
            FROM match_verifications
            WHERE missing_id = ?
            AND status = 'Verified'
            ORDER BY id DESC
            LIMIT 1
        """, (
            person["id"],
        )).fetchone()

        if verification:

            found_person = conn.execute("""
                SELECT *
                FROM found_persons
                WHERE id = ?
            """, (
                verification["found_id"],
            )).fetchone()

            if found_person:

                status = "Found"

                location = found_person[
                    "current_location"
                ]

            else:

                status = "Missing"

                location = person[
                    "last_location"
                ]

        else:

            status = "Missing"

            location = person[
                "last_location"
            ]

        dashboard_persons.append({
            "id": person["id"],
            "name": person["name"],
            "age": person["age"],
            "case_id": person["case_id"],
            "last_location": location,
            "status": status
        })

    conn.close()

    return render_template(
        "dashboard.html",
        family_count=family_count,
        missing_count=missing_count,
        found_count=found_count,
        verified_count=verified_count,
        missing_persons=dashboard_persons
    )


# =========================================================
# FIRST TIME REGISTRATION
# =========================================================

@app.route("/first-time-registration")
def first_time_registration():

    return render_template(
        "first_time_registration.html"
    )


# =========================================================
# REGISTER FAMILY
# =========================================================

@app.route(
    "/register-family",
    methods=["POST"]
)
def register_family():

    name = request.form.get(
        "name"
    )

    age = request.form.get(
        "age"
    )

    contact = request.form.get(
        "contact"
    )

    family_names = request.form.getlist(
        "family_member_name[]"
    )

    relationships = request.form.getlist(
        "relationship[]"
    )

    conn = get_db_connection()

    for i in range(
        len(family_names)
    ):

        family_name = family_names[i]

        if i < len(relationships):

            relationship = relationships[i]

        else:

            relationship = ""

        conn.execute("""
            INSERT INTO family_members
            (
                name,
                age,
                contact,
                family_member_name,
                relationship
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            age,
            contact,
            family_name,
            relationship
        ))

    conn.commit()

    members = conn.execute("""
        SELECT *
        FROM family_members
        WHERE name = ?
        AND contact = ?
        ORDER BY id
    """, (
        name,
        contact
    )).fetchall()

    conn.close()

    return render_template(
        "family_dashboard.html",
        name=name,
        age=age,
        contact=contact,
        members=members
    )


# =========================================================
# RESCUE REGISTRATION
# =========================================================

@app.route("/rescue-registration")
def rescue_registration():

    return render_template(
        "rescue_registration.html"
    )


# =========================================================
# REGISTER RESCUE MEMBER
# =========================================================

@app.route(
    "/register-rescue",
    methods=["POST"]
)
def register_rescue():

    name = request.form.get(
        "name"
    )

    age = request.form.get(
        "age"
    )

    team = request.form.get(
        "team"
    )

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO rescue_members
        (
            name,
            age,
            team
        )
        VALUES (?, ?, ?)
    """, (
        name,
        age,
        team
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "rescue_dashboard"
        )
    )


# =========================================================
# MISSING PERSON PAGE
# =========================================================

@app.route("/missing-person")
def missing_person():

    return render_template(
        "missing_person.html"
    )


# =========================================================
# REGISTER MISSING PERSON
# =========================================================

@app.route(
    "/register-missing-person",
    methods=["POST"]
)
def register_missing_person():

    name = request.form.get(
        "name"
    )

    age = request.form.get(
        "age"
    )

    description = request.form.get(
        "description"
    )

    last_location = request.form.get(
        "last_location"
    )

    contact = request.form.get(
        "contact"
    )

    conn = get_db_connection()

    cursor = conn.execute("""
        INSERT INTO missing_persons
        (
            name,
            age,
            description,
            last_location,
            contact
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        age,
        description,
        last_location,
        contact
    ))

    missing_id = cursor.lastrowid

    # Unique Case ID
    case_id = (
        "RQL-"
        + datetime.now().strftime("%Y%m%d")
        + "-"
        + str(missing_id).zfill(4)
    )

    conn.execute("""
        UPDATE missing_persons
        SET case_id = ?
        WHERE id = ?
    """, (
        case_id,
        missing_id
    ))

    conn.commit()
    conn.close()

    return render_template(
        "missing_person_success.html",
        name=name,
        case_id=case_id,
        missing_id=missing_id
    )


# =========================================================
# FOUND PERSON PAGE
# =========================================================

@app.route("/found-person")
def found_person():

    return render_template(
        "found_person.html"
    )


# =========================================================
# REGISTER FOUND PERSON
# =========================================================

@app.route(
    "/register-found-person",
    methods=["POST"]
)
def register_found_person():

    name = request.form.get(
        "name"
    )

    age = request.form.get(
        "age"
    )

    description = request.form.get(
        "description"
    )

    current_location = request.form.get(
        "current_location"
    )

    status = request.form.get(
        "status"
    )

    conn = get_db_connection()

    cursor = conn.execute("""
        INSERT INTO found_persons
        (
            name,
            age,
            description,
            current_location,
            status
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        age,
        description,
        current_location,
        status
    ))

    found_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return render_template(
        "found_person_success.html",
        name=name,
        age=age,
        current_location=current_location,
        status=status,
        found_id=found_id
    )


# =========================================================
# RESCUE TEAM DASHBOARD
# =========================================================

@app.route("/rescue-dashboard")
def rescue_dashboard():

    conn = get_db_connection()

    members = conn.execute("""
        SELECT *
        FROM rescue_members
        ORDER BY id DESC
    """).fetchall()

    missing_persons = conn.execute("""
        SELECT *
        FROM missing_persons
        ORDER BY id DESC
    """).fetchall()

    found_persons = conn.execute("""
        SELECT *
        FROM found_persons
        ORDER BY id DESC
    """).fetchall()

    verification_statuses = conn.execute("""
        SELECT *
        FROM match_verifications
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "rescue_dashboard.html",
        members=members,
        missing_persons=missing_persons,
        found_persons=found_persons,
        verification_statuses=verification_statuses
    )


# =========================================================
# FIND MATCHES
# =========================================================

@app.route(
    "/find-matches/<int:missing_id>"
)
def find_matches(missing_id):

    conn = get_db_connection()

    missing_person = conn.execute("""
        SELECT *
        FROM missing_persons
        WHERE id = ?
    """, (
        missing_id,
    )).fetchone()

    if not missing_person:

        conn.close()

        return "Missing person not found."

    found_persons = conn.execute("""
        SELECT *
        FROM found_persons
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    matches = []

    for found in found_persons:

        score = calculate_match_score(
            missing_person,
            found
        )

        matches.append(
            (found, score)
        )

    # Highest score first
    matches.sort(
        key=lambda item: item[1],
        reverse=True
    )

    return render_template(
        "match_results.html",
        missing_person=missing_person,
        matches=matches
    )


# =========================================================
# VERIFY MATCH
# =========================================================

@app.route(
    "/verify-match/<int:missing_id>/<int:found_id>",
    methods=["POST"]
)
def verify_match(
    missing_id,
    found_id
):

    conn = get_db_connection()

    # -----------------------------------------------------
    # GET MISSING PERSON
    # -----------------------------------------------------

    missing_person = conn.execute("""
        SELECT *
        FROM missing_persons
        WHERE id = ?
    """, (
        missing_id,
    )).fetchone()

    # -----------------------------------------------------
    # GET FOUND PERSON
    # -----------------------------------------------------

    found_person = conn.execute("""
        SELECT *
        FROM found_persons
        WHERE id = ?
    """, (
        found_id,
    )).fetchone()

    if not missing_person or not found_person:

        conn.close()

        return "Person record not found."

    # -----------------------------------------------------
    # CALCULATE MATCH SCORE
    # -----------------------------------------------------

    match_score = calculate_match_score(
        missing_person,
        found_person
    )

    current_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # -----------------------------------------------------
    # CHECK EXISTING VERIFICATION
    # -----------------------------------------------------

    existing = conn.execute("""
        SELECT *
        FROM match_verifications
        WHERE missing_id = ?
        AND found_id = ?
    """, (
        missing_id,
        found_id
    )).fetchone()

    if existing:

        conn.execute("""
            UPDATE match_verifications
            SET status = ?,
                match_score = ?,
                verified_at = ?
            WHERE missing_id = ?
            AND found_id = ?
        """, (
            "Verified",
            match_score,
            current_time,
            missing_id,
            found_id
        ))

    else:

        conn.execute("""
            INSERT INTO match_verifications
            (
                missing_id,
                found_id,
                match_score,
                status,
                verified_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            missing_id,
            found_id,
            match_score,
            "Verified",
            current_time
        ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "rescue_dashboard"
        )
    )


# =========================================================
# REJECT MATCH
# =========================================================

@app.route(
    "/reject-match/<int:missing_id>/<int:found_id>",
    methods=["POST"]
)
def reject_match(
    missing_id,
    found_id
):

    conn = get_db_connection()

    missing_person = conn.execute("""
        SELECT *
        FROM missing_persons
        WHERE id = ?
    """, (
        missing_id,
    )).fetchone()

    found_person = conn.execute("""
        SELECT *
        FROM found_persons
        WHERE id = ?
    """, (
        found_id,
    )).fetchone()

    if not missing_person or not found_person:

        conn.close()

        return "Person record not found."

    # Calculate score
    match_score = calculate_match_score(
        missing_person,
        found_person
    )

    current_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    existing = conn.execute("""
        SELECT *
        FROM match_verifications
        WHERE missing_id = ?
        AND found_id = ?
    """, (
        missing_id,
        found_id
    )).fetchone()

    if existing:

        conn.execute("""
            UPDATE match_verifications
            SET status = ?,
                match_score = ?,
                verified_at = ?
            WHERE missing_id = ?
            AND found_id = ?
        """, (
            "Rejected",
            match_score,
            current_time,
            missing_id,
            found_id
        ))

    else:

        conn.execute("""
            INSERT INTO match_verifications
            (
                missing_id,
                found_id,
                match_score,
                status,
                verified_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            missing_id,
            found_id,
            match_score,
            "Rejected",
            current_time
        ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "find_matches",
            missing_id=missing_id
        )
    )


# =========================================================
# COMMUNITY SEARCH
# =========================================================

@app.route("/community-search")
def community_search():

    search = request.args.get(
        "search",
        ""
    ).strip()

    persons = []

    search_performed = False

    if search:

        search_performed = True

        conn = get_db_connection()

        records = conn.execute("""
            SELECT *
            FROM missing_persons
            WHERE case_id LIKE ?
            OR name LIKE ?
            ORDER BY id DESC
        """, (
            "%" + search + "%",
            "%" + search + "%"
        )).fetchall()

        for person in records:

            # -------------------------------------------------
            # CHECK FOR VERIFIED MATCH
            # -------------------------------------------------

            verification = conn.execute("""
                SELECT *
                FROM match_verifications
                WHERE missing_id = ?
                AND status = 'Verified'
                ORDER BY id DESC
                LIMIT 1
            """, (
                person["id"],
            )).fetchone()

            if verification:

                found_person = conn.execute("""
                    SELECT *
                    FROM found_persons
                    WHERE id = ?
                """, (
                    verification["found_id"],
                )).fetchone()

                if found_person:

                    status = "Found"

                    location = found_person[
                        "current_location"
                    ]

                    verification_text = (
                        "Verified by Rescue Team"
                    )

                else:

                    status = "Missing"

                    location = person[
                        "last_location"
                    ]

                    verification_text = (
                        "Search in progress"
                    )

            else:

                status = "Missing"

                location = person[
                    "last_location"
                ]

                verification_text = (
                    "Search in progress"
                )

            persons.append({
                "name": person["name"],
                "case_id": person["case_id"],
                "age": person["age"],
                "status": status,
                "location": location,
                "verification": verification_text
            })

        conn.close()

    return render_template(
        "community_search.html",
        persons=persons,
        search=search,
        search_performed=search_performed
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=os.environ.get("RESQLINK_DEBUG", "0") == "1"
    )