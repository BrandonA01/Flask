from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import json
import http.client
import requests

url = "https://online-movie-database.p.rapidapi.com/title/v2/find"

querystring = {"title":"matrix","titleType":"movie","limit":"6","paginationKey":"0","sortArg":"moviemeter,asc"}

headers = {
	"X-RapidAPI-Key": "f8441a6a6bmsh72724c87376c9a4p163c8cjsnf48b2a3445ef",
	"X-RapidAPI-Host": "online-movie-database.p.rapidapi.com"
}

response = requests.request("GET", url, headers=headers, params=querystring)


app = Flask(__name__)
a = False
app.secret_key = "this_is_my_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flaskDB.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(days=5)

"""
conn = http.client.HTTPSConnection("online-movie-database.p.rapidapi.com")
headers = {
    'X-RapidAPI-Key': "f8441a6a6bmsh72724c87376c9a4p163c8cjsnf48b2a3445ef",
    'X-RapidAPI-Host': "online-movie-database.p.rapidapi.com"
    }
"""

db = SQLAlchemy(app)

class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    firstName = db.Column(db.String(32))
    lastName = db.Column(db.String(32))
    email = db.Column(db.String(100))

    def __init__(self, firstName, lastName, email):
        self.firstName = firstName
        self.lastName = lastName
        self.email = email

class films(db.Model):
    _id = db.Column("filmId", db.Integer, primary_key=True)
    filmName = db.Column(db.String(64))
    description = db.Column(db.String(128))
    rating = db.Column(db.Float)

    def __init__(self, filmName, description, rating):
        self.filmName = filmName
        self.description = description
        self.rating = rating

@app.route("/viewUsers")
def view():
    return render_template("view.html", values=users.query.all())
    #return json.dumps(users.query.all())


@app.route("/")
def home():
    return render_template("index.html", values=json.loads(response.text)["results"], length=len(json.loads(response.text)["results"]))
    #return render_template("index.html", values=films.query.all())
    
    """
    conn.request("GET", "/auto-complete?q=game%20of%20thr", headers=headers)
    res = conn.getresponse()
    data = res.read()

    return json.dumps(data, default=str)
    """

@app.route("/user/", methods=["POST","GET"])
def user():
    email = None
    if "user" in session:
        user = session["user"]
        if request.method == "POST":
            email = request.form["email"]
            session["email"] = email
            found_user = users.query.filter_by(firstName=user).first()
            found_user.email = email
            db.session.commit()
            flash("Email was saved!", "info")
        else:
            if "email" in session:
                email = session["email"]
        return render_template("user.html", user=user, email=email)
    else:
        flash("You are not logged in.", "info")
        return redirect(url_for("login"))


@app.route("/admin/")
def admin():
    if a:
        return "You are an admin"
    else:
        return redirect(url_for("user", name="You are not an admin"))


@app.route("/delete", methods=["POST", "GET"])
def delete():
    if "user" in session:
        user = session["user"] 
        users.query.filter_by(firstName=user).delete()
        db.session.commit()
        session.pop("user", None)
        session.pop("email", None)
        flash("Shit just got real")
        return redirect(url_for("login"))
    else:
        flash("you must login to delete an account")
        return redirect(url_for("login"))


@app.route("/login/", methods=["POST","GET"])
def login():
    if request.method == "POST":
        user = request.form["nm"]
        if len(user) != 0:
            session.permanent = True
            session["user"] = user            
            found_user = users.query.filter_by(firstName=user).first()
            if found_user:
                session["email"] = found_user.email

            else:
                usr = users(user, None, None)
                db.session.add(usr)
                db.session.commit()

            flash("Logged in successfully.", "info")
            return redirect(url_for("user"))
        else:
            return render_template("login.html")
    else:
        if "user" in session:
            flash("Already Logged In!", "info")
            return redirect(url_for("user"))
        else:
            return render_template("login.html")


@app.route("/logout")
def logout():
    if "user" in session:
        session.pop("user", None)
        session.pop("email", None)
        flash("You have logged out successfully", "info")
        return redirect(url_for("login"))
    else:
        flash("You are currently not logged in", "info")
        return redirect(url_for("login"))
    



if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)     # (debug=True) Makes changes active so dont have to CTRL+C everytime