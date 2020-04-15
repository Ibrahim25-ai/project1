import os
import requests
import json
from loginrequired import *
from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.secret_key="shitshitshit"
# Check for environment variable
if not os.getenv("DATABASE1_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE1_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/user/<string:name>/<int:user_id>",methods=["GET","POST"])
@login_required
def index(name,user_id):
    
    user=session.get("name")
    message = ''
    session["books"]=[]
    user_db = db.execute("SELECT * FROM users WHERE name=:a",{"a":user}).fetchone()
    data1 = db.execute("SELECT * FROM books LIMIT 20").fetchall()
    if not(user_db.id == user_id) or not(user == name):
        return render_template("error.html", message="ERROR .")
    if request.method == "POST":
        
        text = request.form.get('text')
        if text :
            data = db.execute("SELECT * FROM books WHERE _isbn LIKE '%"+text+"%' OR _title LIKE '%"+text+"%' OR author LIKE '%"+text+"%'").fetchall()
            for i in data:
                session["books"].append(i)
            if session["books"] == [] :
                message="NO RESULTS FOUND"
    return render_template('index.html', message=message , name=name , data=session["books"], data1=data1, user_id=user_id)

@app.route("/<string:name>/<string:isbn>/<string:title>",methods=["GET","POST"])
@login_required
def book(name,isbn,title):
    user=session.get("name")
    action=''
    message=''
    #user id
    user_inf = db.execute("SELECT * FROM users WHERE name=:a ",{"a":user}).fetchone()
    id = user_inf.id
    #MAKE A TABLE WITH JOINING REVIEW AND USERS then test if username have a review or not
    test = db.execute("SELECT *,id,name FROM review JOIN users  ON users.id=review.user_id WHERE isbn_rev=:a and name=:b",{"a":isbn,"b":user}).fetchone()
    data1 = db.execute("SELECT * FROM books WHERE _isbn=:a ",{"a":isbn}).fetchone()
        
    if request.method == "POST" :
        action = request.form.get('action') 
        if (action =='addrev') and (test is None):
            op_rev = request.form.get('rev')
            sc = request.form.get('score')
            if (op_rev != ' ') and (sc != None) :
                db.execute("INSERT INTO review (isbn_rev, opinion_rev, score, user_id) VALUES (:a,:b,:c,:d)",{"a":isbn,"b":op_rev,"c":sc,"d":id})
                db.commit()   
            else :
                message='ENTER YOUR REV'
                return render_template("error.html", message=message)
        if (action =='addrev') and (test ):
            message = 'you can t add 2 reviews'
            return render_template("error.html", message=message)
        if (action =='update') and (test):
            op_rev = request.form.get('rev')
            sc = request.form.get('score')
            if op_rev and sc :
                db.execute("UPDATE review SET opinion_rev =:a ,score =:b WHERE  user_id =:c ",{"a":op_rev, "b":sc, "c":id})
                db.commit()
            else :
                message="ERROR enter your rev"
                return render_template("error.html", message=message)
        if (action =='update') and (test is None ):
            message = 'you don t have any review'
            return render_template("error.html", message=message)
        if (action =='delete') and (test):
            db.execute("DELETE FROM review WHERE user_id=:a",{"a":id})
            db.commit()
        if (action =='delete') and not(test):
            message='no message to delete'
            return render_template("error.html", message=message)

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "mdoj3bVaFym3tf8fav72iQ", "isbns": isbn})
    average_rating=res.json()['books'][0]['average_rating']
    work_ratings_count=res.json()['books'][0]['work_ratings_count']
    # all the reviews
    data = db.execute("SELECT *,id,name FROM review JOIN users  ON users.id=review.user_id WHERE isbn_rev=:a ",{"a":isbn}).fetchall()

    return render_template("book.html",data=data,c=data1,name=user,average_rating=average_rating,work_ratings_count=work_ratings_count,message=message,isbn=isbn,title=title,inf=user_inf)

@app.route("/api/<string:isbn>")
@login_required
def api(isbn):
    data=db.execute("SELECT * FROM books WHERE _isbn = :isbn",{"isbn":isbn}).fetchone()
    if data==None:
        return render_template('404.html')
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "mdoj3bVaFym3tf8fav72iQ", "isbns": isbn})
    average_rating=res.json()['books'][0]['average_rating']
    work_ratings_count=res.json()['books'][0]['work_ratings_count']
    return jsonify({
    "title": data._title,
    "author": data.author,
    "year": data.year,
    "isbn": isbn,
    "review_count": work_ratings_count,
    "average_score": average_rating
          })

@app.route("/login",methods=["GET","POST"])
def login(): 
    user = request.form.get('user')
    data = db.execute("SELECT * FROM users WHERE name=:a",{"a":user}).fetchone()
    message = '' 
    if request.method == "POST":  

        if user and data :
            password = request.form.get('password')
            if  (data.password == password):
                session["name"] = user
                return redirect(url_for("index", name = user, user_id = data.id))
            else:
                message = 'Wrong username or password'
        elif user and not(data):
            message = 'Wrong username or password'
    
    return render_template("login.html", message = message, data = data)

@app.route("/", methods=["GET","POST"])
def register():
    message = ''
   
    if request.method == "POST":
        user = request.form.get('user')
        data = db.execute("SELECT * FROM users WHERE name= :a",{"a":user}).fetchall()
        if data :
            message = "NAME IS ALREADY USED"
        elif user :
            password = request.form.get('password')
            if password:
                db.execute("INSERT INTO users (name,password) VALUES (:user, :pass)",{"user":user, "pass":password})
                db.commit()
                message="Success! You can log in now."
            else :
                message="NO password Entered"
        elif user is None:
            message="No Name Entered"
    return render_template("register.html",message=message)
  
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))
