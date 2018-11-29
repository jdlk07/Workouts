#!/usr/bin/env python2.7

import time
import random
import string
from functools import update_wrapper
from flask import request, g
from flask import Flask, jsonify, flash, redirect, url_for
from flask import render_template
from database_setup import Base, BodyParts, Exercises, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import make_response, flash
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

muscles = (
    session.query(BodyParts)
    .order_by('name')
    .all()
    )


@app.route('/')
def main():
    """
    Renders the index file.
    Passing the BodyParts database collection as a global variable "muscles".
    The BodyParts database is used in all pages as it is used to populate the navigation bar with the names of the muscles.
    """
    return render_template('index.html', muscles=muscles)


@app.route('/json')
def all_json():
    """
    Collects all the data from the BodyParts database and compiles a JSON endpoint.
    Each item in the BodyParts JSON object has nested JSON objects containing all the exercises from the Exercises database.
    """
    Items = []
    for muscle in muscles:
        exercises = (
            session.query(Exercises)
            .filter_by(bodyPart_id=muscle.id)
            .order_by('name')
            .all()
            )
        ExerciseItems = []
        for exercise in exercises:
            ExerciseItem = {
            'name': exercise.name,
            'muscle': muscle.name,
            'description': exercise.description}
            ExerciseItems.append(ExerciseItem)
        Item = {
        'muscle': muscle.name,
        'exercises': ExerciseItems
        }
        Items.append(Item)
    return jsonify(Items)


@app.route('/login')
def showLogin():
    """
    Renders the Login page to login with users Google accounts.
    The state token is used to prevent CSRF (Cross Site Reference Forgery).
    The token is sent to the user along with the HTML page.
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, muscles=muscles)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    URL endpoint for Google Sign In to connect to the Google authentication page.
    Function first ensures that the state token which was sent with the Login page is the same token that has been returned along with the request.
    The access token is then assigned to variable "credentials" which is then checked against Google to ensure its validity.
    The access token is then checked to ensure that it is for the same user that is logged in.
    The access token is then checked against the App ID ensuring it was issued for the appropriate app.
    The user is then checked to see if they're already logged in or if someone else is logged in.
    If all the checks passed, then the users credentials are assigned to the login_session dictionary.
    Finally HTML code is returned as a loading screen to confirm user is logged in.
    """
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

    # Check if the requesting user is already logged in.
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already logged in.'), 200)
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

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<p>Welcome, '
    output += login_session['username']
    output += '!</p>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style="Width: 150px; height: 150px;border-radius: 15-px;-webkit-border-radius: 150px;-mox-border-radius: 150px;>"'
    flash("you are now logged in as %s!" % login_session['username'])
    print "Done with validation!"
    return output


def createUser(login_session):
    """
    Upon logging in for the first time, the users information obtained from Google is stored into the User database.
    """
    newUser = User(username=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = (
        session.query(User)
        .filter_by(email=login_session['email'])
        .one()
        )
    return user.id


def getUserInfo(user_id):
    """
    If the user has logged into the site before with the same Google account then their information is obtained from the User database.
    """
    user = (
        session.query(User)
        .filter_by(id=user_id)
        .one()
        )
    return user


def getUserID(email):
    """
    Upon logging in the users email is queried against the User database to see if they exist in the User database or not.
    """
    try:
        user = (
            session.query(User)
            .filter_by(email=email)
            .one()
            )
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    """
    Checks to see if a user is logged in by checking the value of the variable access_token which was assigned the access token returned from Google.
    If a user is logged in, the accesss token is sent to Google to be revoked.
    """
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
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user. Might have expired?'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/disconnect')
def disconnect():
    """
    Function was created to handle Google and Facebook disconnects however the Facebook authorization could not be implemented.
    This function is called upon when logging out.
    The function checks to see which service was used to login (Google or Facebook).
    The appropriate function is called to revoke the access token. The users credentials are they removed from the login_session dictionary.
    """
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        print "The Disconnect was successful"
        return redirect(url_for('main'))
    else:
        flash("You were not logged in")
        print "You need to be logged in to log out"
        return redirect(url_for('main'))


@app.route('/<muscle_name>/exercises', methods=['GET'])
def view_exercises(muscle_name):
    """
    Depending on which item in the BodyParts database was selected from the navigation bar, this function will return all the exercises from the Exercises database with the same foreign key from BodyParts.
    """
    muscle = (
        session.query(BodyParts)
        .filter_by(name=muscle_name)
        .one()
        )
    exercises = (session.query(Exercises)
        .filter_by(bodyPart_id=muscle.id)
        .all()
        )
    return render_template('exercises.html', exercises=exercises, muscle=muscle, muscles=muscles)


@app.route('/<muscle_name>/exercises/json', methods=['GET'])
def view_exercises_json(muscle_name):
    """
    Returns the exercises from the Exercises table depending on which item was chosen from the BodyParts table in a JSON endpoint.
    """
    muscle = (
        session.query(BodyParts)
        .filter_by(name=muscle_name)
        .one()
        )
    exercises = (
        session.query(Exercises)
        .filter_by(bodyPart_id=muscle.id)
        .all()
        )
    Items = []
    for exercise in exercises:
        item = {
        'name': exercise.name,
        'muscle': muscle.name,
        'description': exercise.description}
        Items.append(item)
    return jsonify(Items)


@app.route('/<muscle_name>/exercises/<exercise_name>', methods=['GET'])
def view_exercise(muscle_name, exercise_name):
    """
    Renders the page to view a specific exercise from the Exercises table.
    The login_session dictionary is used to see if the user who added the exercise is logged in or not.
    The appropriate page is then rendered depending on if the user is the owner of the exercise.
    """
    exercise = (
        session.query(Exercises)
        .filter_by(name=exercise_name)
        .one()
        )
    muscle = (
        session.query(BodyParts)
        .filter_by(name=muscle_name)
        .one()
        )
    creator = getUserInfo(exercise.user_id)
    if 'username' not in login_session or exercise.user_id != login_session['user_id']:
        return render_template('view_exercise_public.html', exercise=exercise, muscles=muscles, muscle=muscle, creator=creator)
    else:
        return render_template('view_exercise.html', exercise=exercise, muscles=muscles, muscle=muscle, creator=creator)


@app.route('/<muscle_name>/exercises/<exercise_name>/json')
def view_exercise_json(muscle_name, exercise_name):
    """
    Returns the specific exercise from the Exercises table in a JSON endpoint.
    """
    exercise = (
        session.query(Exercises)
        .filter_by(name=exercise_name)
        .one()
        )
    muscle = (
        session.query(BodyParts)
        .filter_by(name=muscle_name)
        .one()
        )
    return jsonify({
    'name': exercise.name,
    'muscle': muscle.name,
    'description': exercise.description})


@app.route('/<muscle_name>/exercises/add', methods=['GET', 'POST'])
def add_exercise(muscle_name):
    """
    Function first checks to see if a user is logged in, if not they are redirected to the Login page.
    If logged in, the user is allowed to add an item to the Exercises database. The item must have both "name" and "description" fields filled in or else the submission is rejected.
    A state token is provided along with the GET request of the page and is again checked when a POST request is recieved to prevent CSRF.
    """
    muscle = (
        session.query(BodyParts)
        .filter_by(name=muscle_name)
        .one()
        )
    if 'username' not in login_session:
        flash("You need to log in to add an exercise")
        return redirect('/login')
    if request.method == 'POST':
        if request.args.get("STATE") != login_session['state']:
            state1 = request.args.get("STATE")
            state2 = login_session['state']
            print "This is the request token %s and this is the login_session token %s" % (state1, state2)
            flash("There was a problem with the state token. Please try again.")
            return render_template('add_exercise.html', muscle=muscle, muscles=muscles)
        if request.form['name'] == "" or request.form['description'] == "":
            flash("Name and/or Description can not be blank")
            return render_template('add_exercise.html', muscle=muscle, muscles=muscles)
        else:
            NewExercise = Exercises(name=request.form['name'], description=request.form['description'], bodyPart_id=muscle.id, user_id=login_session['user_id'])
            session.add(NewExercise)
            session.commit()
            flash("Your exercise has been added!")
            return redirect(url_for('view_exercises', muscle_name=muscle_name))
    else:
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        login_session['state'] = state
        print "This is the current token %s" % state
        return render_template('add_exercise.html', muscle=muscle, muscles=muscles, STATE=state)


@app.route('/<muscle_name>/exercises/<exercise_name>/edit', methods=['GET', 'POST'])
def edit_exercise(muscle_name, exercise_name):
    """
    Allows users to edit an item in the Exercises database if they are the owner/creator of the specific item.
    The function first checks to ensure a user is logged in after which the logged in users ID is checked against the ID of the owner of the Exercise.
    To prevent CSRF a state token is passed with the GET request of the page and checked when a POST request is made.
    A user may edit only one field ("name" or "description") as if there is no value in a particular field then that field is omitted from the database insert.
    """
    muscle = (
        session.query(BodyParts)
        .filter_by(name=muscle_name)
        .one()
        )
    exercise = (
        session.query(Exercises)
        .filter_by(name=exercise_name)
        .one()
        )
    ItemToEdit = exercise
    if 'username' not in login_session:
        flash("You need to login to do that!")
        return redirect('/login')
    if ItemToEdit.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this exercise as it does not belong to you!');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.args.get("STATE") != login_session['state']:
            flash("There was a problem with the state token. Please try again.")
            return redirect(url_for('view_exercise', muscle_name=muscle_name, exercise_name=exercise.name))
        if request.form['name']:
            ItemToEdit.name = request.form['name']
        if request.form['description']:
            ItemToEdit.description = request.form['description']
        session.add(ItemToEdit)
        session.commit()
        print "The SQL Entry was Edited Succesfully!"
        flash("Exercise has been updated!")
        return redirect(url_for('view_exercise', muscle_name=muscle_name, exercise_name=exercise.name))
    else:
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        login_session['state'] = state
        return render_template('edit_exercise.html', muscle=muscle, exercise=exercise, muscles=muscles, STATE=state)


@app.route('/<muscle_name>/exercises/<exercise_name>/delete', methods=['GET', 'POST'])
def delete_exercise(muscle_name, exercise_name):
    """
    Allows users to delete an item in the Exercises database if they are the owner/creator of the specific item.
    The function first checks to ensure a user is logged in after which the logged in users ID is checked against the ID of the owner of the Exercise.
    To prevent CSRF a state token is passed with the GET request of the page and checked when a POST request is made.
    If all checks have passed, then the item is deleted from the Exercises database.
    """
    muscle = (
        session.query(BodyParts)
        .filter_by(name=muscle_name)
        .one()
        )
    exercise = (
        session.query(Exercises)
        .filter_by(name=exercise_name)
        .one()
        )
    ItemToDelete = exercise
    if 'username' not in login_session:
        flash("You need to login to do that!")
        return redirect('/login')
    if ItemToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this exercise as it does not belong to you!');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.args.get("STATE") != login_session['state']:
            flash("There was a problem with the state token. Please try again.")
            return redirect(url_for('view_exercise', muscle_name=muscle_name, exercise_name=exercise.name))
        session.delete(ItemToDelete)
        session.commit()
        print "*** \n Item Was Deleted \n ***"
        return redirect(url_for('view_exercises', muscle_name=muscle.name))
    else:
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        login_session['state'] = state
        return render_template('delete_exercise.html', muscle=muscle, exercise=exercise, muscles=muscles, STATE=state)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
