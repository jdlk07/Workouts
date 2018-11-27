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

muscles = session.query(BodyParts).order_by('name').all()


@app.route('/')
def main():
    return render_template('index.html', muscles = muscles)

@app.route('/json')
def all_json():
    Items = []
    for muscle in muscles:
        exercises = session.query(Exercises).filter_by(bodyPart_id=muscle.id).order_by('name').all()
        ExerciseItems = []
        for exercise in exercises:
            ExerciseItem = {
            'name' : exercise.name,
            'muscle' : muscle.name,
            'description' : exercise.description}
            ExerciseItems.append(ExerciseItem)
        Item = {
        'muscle' : muscle.name,
        'exercises' : ExerciseItems
        }
        Items.append(Item)
    return jsonify(Items)

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, muscles = muscles)

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s" % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


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
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user. Might have expired?'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

@app.route('/disconnect')
def disconnect():
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
    muscle = session.query(BodyParts).filter_by(name = muscle_name).one()
    exercises = session.query(Exercises).filter_by(bodyPart_id = muscle.id).all()
    return render_template('exercises.html', exercises = exercises, muscle = muscle, muscles = muscles)

@app.route('/<muscle_name>/exercises/json', methods=['GET'])
def view_exercises_json(muscle_name):
    muscle = session.query(BodyParts).filter_by(name = muscle_name).one()
    exercises = session.query(Exercises).filter_by(bodyPart_id = muscle.id).all()
    Items = []
    for exercise in exercises:
        item = {
        'name' : exercise.name,
        'muscle' : muscle.name,
        'description' : exercise.description}
        Items.append(item)
    return jsonify(Items)

@app.route('/<muscle_name>/exercises/<exercise_name>', methods = ['GET'])
def view_exercise(muscle_name, exercise_name):
    exercise = session.query(Exercises).filter_by(name = exercise_name).one()
    muscle = session.query(BodyParts).filter_by(name = muscle_name).one()
    creator = getUserInfo(exercise.user_id)
    if 'username' not in login_session or exercise.user_id != login_session['user_id']:
        return render_template('view_exercise_public.html', exercise = exercise, muscles = muscles, muscle = muscle, creator = creator)
    else:
        return render_template('view_exercise.html', exercise = exercise, muscles = muscles, muscle = muscle, creator = creator)

@app.route('/<muscle_name>/exercises/<exercise_name>/json')
def view_exercise_json(muscle_name, exercise_name):
    exercise = session.query(Exercises).filter_by(name = exercise_name).one()
    muscle = session.query(BodyParts).filter_by(name = muscle_name).one()
    return jsonify({
    'name':exercise.name,
    'muscle':muscle.name,
    'description':exercise.description})

@app.route('/<muscle_name>/exercises/add', methods = ['GET', 'POST'])
def add_exercise(muscle_name):
    muscle = session.query(BodyParts).filter_by(name = muscle_name).one()
    if 'username' not in login_session:
        flash("You need to log in to add an exercise")
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name'] == "" or request.form['description'] =="":
            flash("Name or Description can not be blank")
            return render_template('add_exercise.html', muscle = muscle, muscles = muscles)
        else:
            NewExercise = Exercises(name = request.form['name'], description = request.form['description'], bodyPart_id = muscle.id, user_id=login_session['user_id'])
            session.add(NewExercise)
            session.commit()
            flash("Your exercise has been added!")
            return redirect(url_for('view_exercises', muscle_name = muscle_name))
    else:
        return render_template('add_exercise.html', muscle = muscle, muscles = muscles)


@app.route('/<muscle_name>/exercises/<exercise_name>/edit', methods=['GET', 'POST'])
def edit_exercise(muscle_name, exercise_name):
    muscle = session.query(BodyParts).filter_by(name = muscle_name).one()
    exercise = session.query(Exercises).filter_by(name = exercise_name).one()
    ItemToEdit = exercise
    if 'username' not in login_session:
        flash("You need to login to do that!")
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
        flash("Exercise has been updated!")
        return redirect(url_for('view_exercise', muscle_name = muscle_name, exercise_name = exercise.name))
    else:
        return render_template('edit_exercise.html', muscle = muscle, exercise = exercise, muscles = muscles)

@app.route('/<muscle_name>/exercises/<exercise_name>/delete', methods=['GET', 'POST'])
def delete_exercise(muscle_name, exercise_name):
    muscle = session.query(BodyParts).filter_by(name = muscle_name).one()
    exercise = session.query(Exercises).filter_by(name = exercise_name).one()
    ItemToDelete = exercise
    if 'username' not in login_session:
        flash("You need to login to do that!")
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


# @app.route('/<muscle_name>/exercises/<int:exercise_id>/json')
# def view_exercise_json(bodyPart_id, exercise_id):
#     exercise = session.query(Exercises).filter_by(id = exercise_id).one()
#     muscle = session.query(BodyParts).filter_by(id = bodyPart_id).one()
#     return jsonify({
#     'name':exercise.name,
#     'muscle':muscle.name,
#     'description':exercise.description})








if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 8000)
