from redis import Redis
import time, random, string
from functools import update_wrapper
from flask import request, g
from flask import Flask, jsonify, flash, redirect, url_for
from flask import render_template
from database_setup import Base, BodyParts, Exercises, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import make_response
import requests
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy import create_engine
from flask_httpauth import HTTPBasicAuth
import json
from flask import session as login_session

auth = HTTPBasicAuth()

engine = create_engine('sqlite:///exercises.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = scoped_session(DBSession)
app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

muscles = session.query(BodyParts).order_by('name').all()


@app.route('/')
def main():
    return render_template('index.html', muscles = muscles)

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, muscles = muscles)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match app's client ID."), 401)
        print "Token's Client ID does not match app's Client ID."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected homie.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style="Width: 300px; height: 300px;border-radius: 15-px;-webkit-border-radius: 150px;-mox-border-radius: 150px;>"'
    flash("you are now logged in as %s my man!" % login_session['username'])
    print "Done with validation!"
    return output

def createUser(login_session):
    newUser = User(username=login_session['username'], email = login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print "In gdisconnect access token is %s" % access_token
    print "User Name is: "
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print "result is "
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user. Might have expired?'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/<muscle_name>/exercises', methods=['GET'])
def view_exercises(muscle_name):
    muscle = session.query(BodyParts).filter_by(name = muscle_name).one()
    exercises = session.query(Exercises).filter_by(bodyPart_id = muscle.id).all()
    json = []
    for exercise in exercises:
        item = {
        'name':exercise.name,
        'muscle':muscle.name,
        'description':exercise.description}
        json.append(item)
    return render_template('exercises.html', exercises = exercises, muscle = muscle, muscles = muscles, json = json)


@app.route('/<muscle_name>/exercises/<exercise_name>', methods = ['GET'])
def view_exercise(muscle_name, exercise_name):
    exercise = session.query(Exercises).filter_by(name = exercise_name).one()
    muscle = session.query(BodyParts).filter_by(name = muscle_name).one()
    creator = getUserInfo(exercise.user_id)
    if 'username' not in login_session or exercise.user_id != login_session['user_id']:
        return render_template('view_exercise_public.html', exercise = exercise, muscles = muscles, muscle = muscle, creator = creator)
    else:
        return render_template('view_exercise.html', exercise = exercise, muscles = muscles, muscle = muscle, creator = creator)

@app.route('/<muscle_name>/exercises/add', methods = ['GET', 'POST'])
def add_exercise(muscle_name):
    muscle = session.query(BodyParts).filter_by(name = muscle_name).one()
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        NewExercise = Exercises(name = request.form['name'], description = request.form['description'], bodyPart_id = muscle.id, user_id=login_session['user_id'])
        session.add(NewExercise)
        session.commit()
        return redirect(url_for('view_exercises', muscle_name = muscle_name))
    else:
        return render_template('add_exercise.html', muscle = muscle, muscles = muscles)


@app.route('/<muscle_name>/exercises/<exercise_name>/edit', methods=['GET', 'POST'])
def edit_exercise(muscle_name, exercise_name):
    muscle = session.query(BodyParts).filter_by(name = muscle_name).one()
    exercise = session.query(Exercises).filter_by(name = exercise_name).one()
    ItemToEdit = exercise
    if 'username' not in login_session:
        return redirect('/login')
    if ItemToEdit.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this exercise as it does not belong to you!');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            ItemToEdit.name = request.form['name']
        if request.form['description']:
            ItemToEdit.description = request.form['description']
        session.add(ItemToEdit)
        session.commit()
        print "The SQL Entry was Edited Succesfully!"
        return redirect(url_for('view_exercise', muscle_name = muscle_name, exercise_name = exercise.name))
    else:
        return render_template('edit_exercise.html', muscle = muscle, exercise = exercise, muscles = muscles)

@app.route('/<muscle_name>/exercises/<exercise_name>/delete', methods=['GET', 'POST'])
def delete_exercise(muscle_name, exercise_name):
    muscle = session.query(BodyParts).filter_by(name = muscle_name).one()
    exercise = session.query(Exercises).filter_by(name = exercise_name).one()
    ItemToDelete = exercise
    if 'username' not in login_session:
        return redirect('/login')
    if ItemToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this exercise as it does not belong to you!');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(ItemToDelete)
        session.commit()
        print "*** \n Item Was Deleted \n ***"
        return redirect(url_for('view_exercises', muscle_name = muscle.name))
    else:
        return render_template('delete_exercise.html', muscle = muscle, exercise = exercise, muscles = muscles)


@app.route('/<muscle_name>/exercises/<int:exercise_id>/json')
def view_exercise_json(bodyPart_id, exercise_id):
    exercise = session.query(Exercises).filter_by(id = exercise_id).one()
    muscle = session.query(BodyParts).filter_by(id = bodyPart_id).one()
    return jsonify({
    'name':exercise.name,
    'muscle':muscle.name,
    'description':exercise.description})


@app.route('/<muscle_name>/exercises/new' , methods=['GET','POST'])
def new_exercise(bodyPart_id):
    body_part = session.query(BodyParts).filter_by(id = bodyPart_id).one()
    if request.method == 'POST':
        NewExercise = Exercises(name = request.form['name'], description = request.form['description'], bodyPart_id = bodyPart_id)
        session.add(NewExercise)
        session.commit()
        flash("New Exercise Added!")
        return redirect(url_for())







if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)
