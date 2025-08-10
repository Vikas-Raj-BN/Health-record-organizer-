from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory,session
import sqlite3
import os
import uuid

app = Flask(__name__)
app.secret_key = "secret_key"
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize Database
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Create the users table if it doesn't exist
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    phone TEXT UNIQUE,
                    password TEXT,
                    unique_id TEXT,
                    linked_phone TEXT
                )""")

    # Create the reports table if it doesn't exist
    c.execute("""CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    filename TEXT,
                    description TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )""")

    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        # Debugging: Print the registration details
        print(f"Attempting to register user with phone: {phone}, password: {password}")

        # Check if a user with the same phone number already exists
        c.execute("SELECT unique_id FROM users WHERE phone=?", (phone,))
        existing_user = c.fetchone()

        if existing_user:
            # Phone number already exists
            error_message = "User with this phone number already exists! Please log in."
            return render_template("register.html", error_message=error_message, show_login_link=True)
        else:
            # Generate a new unique_id for this phone number
            unique_id = str(uuid.uuid4())[:8]

            try:
                # Insert the new user into the database (without username)
                c.execute(
                    "INSERT INTO users (phone, password, unique_id, linked_phone) VALUES (?, ?, ?, ?)",
                    (phone, password, unique_id, phone)  # Set linked_phone to the user's own phone
                )
                conn.commit()
                conn.close()

                # Debugging: Print success message
                print(f"User registered successfully: phone: {phone}")

                # Show success message with user details
                return render_template(
                    "register.html",
                    phone=phone,
                    password=password,
                    unique_id=unique_id
                )
            except sqlite3.IntegrityError as e:
                # Debugging: Print database error
                print(f"Error registering user: {e}")

                # Phone number already exists (race condition)
                error_message = "User with this phone number already exists! Please log in."
                return render_template("register.html", error_message=error_message, show_login_link=True)
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form["phone"]
        password = request.form["password"]
        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        # Debugging: Print the phone and password being checked
        print(f"Attempting login with phone: {phone}, password: {password}")

        # Fetch the user from the database
        c.execute("SELECT * FROM users WHERE phone=?", (phone,))
        user = c.fetchone()

        # Debugging: Print the user details fetched from the database
        print(f"User details from database: {user}")

        conn.close()

        if user:
            # Check if the password matches
            if user[3] == password:  # Assuming password is in the 4th column
                # Store user ID in the session
                session["user_id"] = user[0]
                return redirect(url_for("manage_users", user_id=user[0]))
            else:
                error_message = "Incorrect credentials. Please try again."
        else:
            error_message = "User not found. Please register."

        return render_template("login.html", error_message=error_message)
    return render_template("login.html")


@app.route("/dashboard/<int:user_id>")
def dashboard(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    # Fetch the user details including linked_phone
    c.execute("SELECT id, username, linked_phone, unique_id FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    
    # Fetch the reports related to the user
    c.execute("SELECT * FROM reports WHERE user_id=?", (user_id,))
    reports = c.fetchall()
    
    conn.close()

    if user:
        # Use linked_phone as the phone number for all linked users
        return render_template("dashboard.html", username=user[1], phone=user[2], unique_id=user[3], user_id=user[0], reports=reports)
    else:
        flash("User not found!")
        return redirect(url_for('home'))

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("report")
    description = request.form.get("description")
    user_id = request.form.get("user_id")

    if not user_id:
        flash("User ID is missing. Please try again.")
        return redirect(url_for("dashboard", user_id=user_id))

    if file:
        filename = file.filename
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO reports (user_id, filename, description) VALUES (?, ?, ?)",
                  (user_id, filename, description))
        conn.commit()
        conn.close()
        flash("Upload successful!")
    else:
        flash("No file selected.")
    return redirect(url_for("dashboard", user_id=user_id))

@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        unique_id = request.form["unique_id"]
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT phone, password FROM users WHERE unique_id=?", (unique_id,))
        user = c.fetchone()
        conn.close()

        if user:
            user_details = {"phone": user[0], "password": user[1]}
            return render_template("forgot.html", user_details=user_details)
        else:
            error_message = "Unique ID does not exist. Please try again."
            return render_template("forgot.html", error_message=error_message)
    return render_template("forgot.html")

@app.route("/download/<int:report_id>")
def download(report_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT filename, user_id FROM reports WHERE id=?", (report_id,))
    report = c.fetchone()
    conn.close()
    
    if report:
        filename = report[0]
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        
        if os.path.exists(filepath):
            return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)
        else:
            flash("File not found.")
    else:
        flash("Report not found.")
    
    return redirect(url_for("dashboard", user_id=report[1]))

@app.route("/delete/<int:report_id>")
def delete(report_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT filename, user_id FROM reports WHERE id=?", (report_id,))
    report = c.fetchone()
    
    if report:
        filename = report[0]
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
        
        c.execute("DELETE FROM reports WHERE id=?", (report_id,))
        conn.commit()
        flash("Report deleted successfully!")
        conn.close()
        
        return redirect(url_for("dashboard", user_id=report[1]))
    
    conn.close()
    flash("Report not found.")
    return redirect(url_for("dashboard", user_id=report[1]))

@app.route("/about")
def about():
    return render_template("about.html")

# New Routes for Managing Linked Users
@app.route("/manage_users/<int:user_id>", methods=["GET", "POST"])
def manage_users(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Fetch the logged-in user's phone number and unique_id
    c.execute("SELECT phone, unique_id FROM users WHERE id=?", (user_id,))
    user = c.fetchone()

    if not user:
        conn.close()
        flash("User not found!")
        return redirect(url_for("home"))

    main_user_phone = user[0]  # Get the phone number
    unique_id = user[1]  # Get the unique_id for this phone number

    # Handle adding a new user
    if request.method == "POST":
        username = request.form.get("username")  # Use request.form.get() to avoid KeyError
        print(f"Form data: {request.form}")  # Debugging: Print form data
        print(f"Username: {username}")  # Debugging: Print username

        if not username:
            flash("Username is required!")
            return redirect(url_for("manage_users", user_id=user_id))

        try:
            c.execute(
                "INSERT INTO users (username, phone, password, unique_id, linked_phone) VALUES (?, ?, ?, ?, ?)",
                (username, None, None, unique_id, main_user_phone)  # Phone and password are None, reuse unique_id
            )
            conn.commit()
            flash("User added successfully!")
        except sqlite3.IntegrityError as e:
            print(f"Error adding user: {e}")  # Debugging: Print database error
            flash("Error adding user. Please try again.")
        finally:
            conn.close()
            return redirect(url_for("manage_users", user_id=user_id))

    # Fetch all users linked to this phone number
    c.execute("SELECT * FROM users WHERE linked_phone=?", (main_user_phone,))
    linked_users = c.fetchall()

    conn.close()
    return render_template("manage_users.html", user_id=user_id, linked_users=linked_users, main_user_phone=main_user_phone)

@app.route("/delete_linked_user/<int:user_id>/<int:linked_user_id>")
def delete_linked_user(user_id, linked_user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Fetch the main user's phone number
    c.execute("SELECT phone FROM users WHERE id=?", (user_id,))
    main_user = c.fetchone()

    if not main_user:
        conn.close()
        flash("Main user not found!")
        return redirect(url_for("manage_users", user_id=user_id))

    main_user_phone = main_user[0]

    # Fetch the linked user to ensure they exist and are linked to the main user
    c.execute("SELECT id, phone FROM users WHERE id=? AND linked_phone=?", (linked_user_id, main_user_phone))
    linked_user = c.fetchone()

    if not linked_user:
        conn.close()
        flash("Linked user not found or not associated with this account!")
        return redirect(url_for("manage_users", user_id=user_id))

    # Ensure the linked user is not the main user (i.e., their phone number is not the same as the main user's)
    if linked_user[1] == main_user_phone:
        conn.close()
        flash("Cannot delete the main user!")
        return redirect(url_for("manage_users", user_id=user_id))

    # Delete the linked user
    c.execute("DELETE FROM users WHERE id=?", (linked_user_id,))
    conn.commit()
    conn.close()

    flash("Linked user deleted successfully!")
    return redirect(url_for("manage_users", user_id=user_id))

if __name__ == "__main__":
    init_db()  # Initialize the database only once
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)