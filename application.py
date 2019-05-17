from flask import Flask, render_template, url_for, session, request, redirect, g

import os
import smtplib
import sqlite3

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


#@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=()):

    cur = get_db().execute(query, args)

    rv = cur.fetchall()
    cur.close()
    #return (rv[0] if rv else None) if one else rv
    return rv


app = Flask(__name__)
#@app.run(host='0.0.0.0')

@app.route("/", methods=["GET", "POST"])

def index():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if request.form.get("username") == "oprah" and request.form.get("password") == "cats":
             return render_template("index.html")

        else:
            query = 'select * from accounts where username = "' + username + '" and password = "' + password +'"'
            user = query_db(query)
            if not user:
                print ('No such user')
                return render_template("oops.html")

            else:
                session['username'] = user[0][1] #store user name as session variable
                session['id'] = user[0][0] #store id as session variable
                session['forum'] = user[0][3] #store forum as session variable
                return render_template("index.html")

    else:
          return render_template("index.html")

@app.route('/login')
def login():
    """ Displays the page greats who ever comes to visit it.
    """
    return render_template('login.html')

@app.route('/create', methods=["GET", "POST"])
def create():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = query_db('insert into accounts ("username","password") VALUES (?,?)', (username, password))
        get_db().commit()

        return render_template("login.html")

    else: #get request
        return render_template("create.html")

@app.route('/survey', methods=["GET", "POST"])
def survey():

    if request.method == "POST":

        #add to sql survey table
        grade = request.form.get("grade")
        if grade == "freshman":
            forum = "1"
        elif grade == "sophomore":
            forum = "2"
        elif grade == "junior":
            forum = "3"
        else:
            forum = "4"

        id = str(session['id']) #store the id of the person currently logged in (our session variable, in the table with their personality test score
        user = query_db('update accounts set forum = ' + forum + ' where id = ' + id)
        get_db().commit()

        session['forum'] = int(forum)

        return render_template("index.html")

    else: #get request, if user is logged in (username in session - show them the survey, otherwise send to login page)
        if 'username' in session:
            return render_template("survey.html")
        else:
            return render_template("login.html")

@app.route('/your_forum', methods=["GET", "POST"])
def your_forum():

    if request.method == "POST":
        text = request.form.get("message")
        id = session['id'] #get id of currently logged in user so this id can be stored in the thoughts table with their thought
        forum = session['forum']

        user = query_db('insert into posts ("userid", "forum", "content") VALUES (?,?,?)', (id, forum, text))
        get_db().commit()
        return render_template("your_forum.html", msg=text)

    else:

        if 'username' in session: #if user is logged in, get all their previous thoughts using their session id and querying thoughts table with it
            id = str(session['id'])
            forum = str(session['forum'])

            query = 'select accounts.username, posts.content from accounts join posts where posts.forum = ' + forum
            forum_posts = query_db(query)

            options={}
            if not forum_posts:
                send = "none"

            else: #build a string of all their thoughts that were returned from table, to send as variable to thoughts.html
                send=""

                for post in forum_posts:
                    send += post[0] + '\n' + post[1] + '\n\n'

            return render_template("your_forum.html", msg=send)
        else:
            return render_template("login.html") #if not logged in, render login page

@app.route('/matches', methods=["GET", "POST"])
def matches():


    if request.method == "POST":
        text = request.form.get("message")
        id = session['id']
        user = query_db('insert into thoughts ("accountOwner", "thoughts") VALUES (?,?)', (id, text))
        get_db().commit()

        return render_template("index.html")

    else:

        if 'username' in session:
            id = session['id']
            id = str(id)
            query = 'select score1 from surveyinfo where userid = "' + id + '"'

            msgs = query_db(query)
            idlist=""
            if not msgs:

                send = "You have no matches because you didn't take the survey"
            else:
                send=""


                yourscore = msgs[0][0]
                yourscore = str(yourscore)
                query2 = 'select userid from surveyinfo where score1 = "' + yourscore + '"'

                matches = query_db(query2)

                for match in matches:
                    matchid = str(match[0])
                    if matchid != id:
                        query3 = 'select name from accounts where uniqueId = "' + matchid + '"'
                        user = query_db(query3)
                        send += user[0][0] + '\n'
                        idlist += matchid + ';'
                print(send)
            return render_template("matches.html", msg=send, ids=idlist)
        else:
            return render_template("login.html")


@app.route('/logout')
def logout():

   session.pop('username', None) #removes username from session variable
   session.pop('id', None) #no longer logged in
   return render_template("index.html")

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT' #needed to use sessions