from ssl import AlertDescription
from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import json
import http.client
import requests

url = "https://online-movie-database.p.rapidapi.com/title/v2/find"
querystring = {"title":"","titleType":"movie","limit":"5","paginationKey":"0","sortArg":"moviemeter,asc"}

urlPopular = "https://online-movie-database.p.rapidapi.com/title/get-most-popular-movies"
querystringPopular = {"currentCountry":"GB","purchaseCountry":"GB","homeCountry":"GB"}

urlPopDet = "https://online-movie-database.p.rapidapi.com/title/get-details"
querystringPopDet = {"tconst":""}

urlDetails = "https://online-movie-database.p.rapidapi.com/title/get-overview-details"
querystringDetails = {"tconst":"","currentCountry":"US"}

headers = {
	"X-RapidAPI-Key": "",
	"X-RapidAPI-Host": "online-movie-database.p.rapidapi.com"
}

response = requests.request("GET", url, headers=headers, params=querystring)
responsePopular = requests.request("GET", urlPopular, headers=headers, params=querystringPopular)
responsePopularDetails = requests.request("GET", urlPopDet, headers=headers, params=querystringPopDet)
responseMoreDetails = requests.request("GET", urlDetails, headers=headers, params=querystringDetails)


app = Flask(__name__)
a = False
app.secret_key = "this_is_my_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flaskDB.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(days=5)

db = SQLAlchemy(app)

class users(db.Model):
    email = db.Column(db.String(100), primary_key=True)
    firstName = db.Column(db.String(32))
    lastName = db.Column(db.String(32))
    password = db.Column(db.Integer)
    favourites = db.Column(db.String)

    def __init__(self, email, firstName, lastName, password, favourites):
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.password = password
        self.favourites = favourites

class films(db.Model):
    _id = db.Column("filmId", db.Integer, primary_key=True)
    filmName = db.Column(db.String(64))
    description = db.Column(db.String(128))
    rating = db.Column(db.Float)

    def __init__(self, filmName, description, rating):
        self.filmName = filmName
        self.description = description
        self.rating = rating

class popularFilms(db.Model):
    _id = db.Column("id", db.String(10), primary_key=True)
    title = db.Column(db.String(64))
    url = db.Column(db.String(256))

    def __init__(self, _id, title, url):
        self._id = _id
        self.title = title
        self.url = url

@app.route('/search', methods=['POST'])
def search():
        search = request.form["search"]
        if search != "":
            search = search.strip
            print(search)
            return render_template("search.html", length=1, values=search)
        else:
            return render_template("index.html", values=popularFilms.query.all(), length=len(popularFilms.query.all()))
    
@app.route("/film/<id>")
def film(id):
    querystringDetails["tconst"] = id
    responseMoreDetails = json.loads(requests.request("GET", urlDetails, headers=headers, params=querystringDetails).text)
    print(responseMoreDetails)
    if "rating" in responseMoreDetails["ratings"]:
        rating = responseMoreDetails["ratings"]["rating"]
    else:
        rating = 0
    return render_template("film.html", title=responseMoreDetails["title"]["title"], url=responseMoreDetails["title"]["image"]["url"], desc=responseMoreDetails["plotOutline"]["text"], rat=rating)

@app.route("/viewUsers")
def view():
    return render_template("view.html", values=users.query.all())
    #return json.dumps(users.query.all())


@app.route("/")
def home():
    jsonList = {"films": []}
    return render_template("index.html", values=popularFilms.query.all(), length=len(popularFilms.query.all()))
    #return z
"""
    limit = 100
    for index, item in enumerate(json.loads(responsePopular.text)):
        if index == limit:
            break
        item = item.replace("/title/", "")
        item = item.replace("/", "")


        x = json.dumps(jsonList)
        z = json.loads(x)
        querystringPopDet["tconst"] = item
        responsePopularDetails = requests.request("GET", urlPopDet, headers=headers, params=querystringPopDet)
        
        print(json.loads(responsePopularDetails.text))
        
        popFilm = popularFilms(item, json.loads(responsePopularDetails.text)["title"], json.loads(responsePopularDetails.text)["image"]["url"])
        db.session.add(popFilm)
        db.session.commit()

        z["films"].append(responsePopularDetails.text)
        jsonList = z

    conn.request("GET", "/auto-complete?q=game%20of%20thr", headers=headers)
    res = conn.getresponse()
    data = res.read()

    return json.dumps(data, default=str)
    """

@app.route("/user", methods=["POST","GET"])
def user():
    if "email" in session:
        curremail = session["email"]
        if request.method == "POST":
            emailInput = request.form["email"]
            fname = request.form["fname"]
            lname = request.form["lname"]
            session["email"] = emailInput
            session["fname"] = fname
            session["lname"] = lname
            found_user = users.query.filter_by(email=curremail).first()
            found_user.email = emailInput
            found_user.firstName = fname
            found_user.lastName = lname
            db.session.commit()
            flash("Details were saved!", "info")
        return render_template("user.html", fname=session["fname"], lname=session["lname"], email=session["email"])
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
    if "email" in session:
        email = session["email"] 
        users.query.filter_by(email=email).delete()
        db.session.commit()
        session.pop("email", None)
        session.pop("fname", None)
        session.pop("lname", None)
        flash("Deleted Account!")
        return redirect(url_for("login"))
    else:
        flash("you must login to delete an account")
        return redirect(url_for("login"))


@app.route("/login/", methods=["POST","GET"])
def login():
    if request.method == "POST":
        email = request.form["logemail"]
        password = request.form["logpass"]
        if len(email) != 0 and len(password) != 0:
            session.permanent = True
            session["email"] = email
            found_user = users.query.filter_by(email=email).first()
            if found_user:
                if password == found_user.password:
                    session["email"] = found_user.email
                    session["fname"] = found_user.firstName
                    session["lname"] = found_user.lastName
                    flash("Logged in successfully.", "info")
                    return redirect(url_for("user"))
                else:
                    flash("email or password is incorrect", "info")
                    return render_template("login.html")
            else:
                usr = users(email, None, None, password)
                db.session.add(usr)
                db.session.commit()
                flash("Created account.", "info")
                return redirect(url_for("user"))

        else:
            return render_template("login.html")
    else:
        if "email" in session:
            flash("Already Logged In!", "info")
            return redirect(url_for("user"))
        else:
            return render_template("login.html")


@app.route("/logout")
def logout():
    if "email" in session:
        session.pop("email", None)
        session.pop("fname", None)
        session.pop("lname", None)
        flash("You have logged out successfully", "info")
        return redirect(url_for("login"))
    else:
        flash("You are currently not logged in", "info")
        return redirect(url_for("login"))
    

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)     # (debug=True) Makes changes active so dont have to CTRL+C everytime