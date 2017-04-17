from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask import session as login_session
import string, random

from oauth2client.client import flow_from_clientsecrets, OAuth2WebServerFlow
from oauth2client.client import FlowExchangeError, Credentials
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import User, Restaurant, Base, MenuItem

engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(open('client_secret.json', 'r').read())["web"]["client_id"]


# User Related Functions

def createUser(login_session):
	newUser = User(	name = login_session["user_name"], 
					email = login_session["email"],
					picture = login_session["picture"] )
	session.add(newUser)
	session.commit()
	user = session.query(User).filter_by(email = login_session["email"]).one()
	return user.id

def getUserInfo(user_id):
	user = session.query(User).filter_by(id = user_id).one()
	return user

def getUserId(email):
	try:
		user = session.query(User).filter_by(email = email).one()
		return user.id
	except:
		return None


@app.route("/")
@app.route("/restaurants")
def homepageRoute():
	restaurants = session.query(Restaurant).all()
	user_id = "user_id" in login_session and login_session["user_id"]
	return render_template("homePage.html", restaurants = restaurants, user_id = user_id)

@app.route("/api/json/restaurants/add_restaurant", methods=["GET", "POST"])
@app.route("/restaurants/add_restaurant", methods=["GET", "POST"])
def restaurantAddRoute():
	if("user_name" not in login_session):
		return redirect(url_for(showLogin))
	if(request.method == "POST"):
		restaurant = Restaurant(name = request.form["name"], 
								locality = request.form["location"],
								description = request.form["description"],
								user_id = login_session["user_id"])
		session.add(restaurant)
		session.commit()
		if("/api/json/" not in request.url):
			return redirect(url_for('homepageRoute'))
		else:
			return jsonify(restaurant=restaurant.serialize)
	else:
		user_id = login_session["user_id"]
		return render_template("addRestaurant.html", user_id = user_id)


@app.route("/restaurants/<int:restaurant_id>/")
def restaurantRoute(restaurant_id):
	if("user_name" not in login_session):
		return redirect(url_for(showLogin))
	restaurant = session.query(Restaurant).filter_by(id= restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	return render_template("restaurantTemplate.html", restaurant=restaurant, items = items, user_id = login_session["user_id"])

@app.route("/api/json/restaurants/<int:restaurant_id>/edit/", methods=["GET", "POST"])
@app.route("/restaurants/<int:restaurant_id>/edit/", methods=["GET", "POST"])
def restaurantEditRoute(restaurant_id):
	if("user_name" not in login_session):
		return redirect(url_for(showLogin))
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if(restaurant.user_id != login_session["user_id"]):
		flash("You are not permitted to modify others restaurant data!")
		return redirect(url_for("homepageRoute"))

	if(request.method == "POST"):
		
		restaurant.name = request.form["name"]
		restaurant.locality = request.form["location"]
		restaurant.description = request.form["description"]
		session.add(restaurant)
		session.commit()
		if("/api/json/" not in request.url):
			return redirect(url_for('restaurantRoute', restaurant_id = restaurant_id))
		else:
			return jsonify(restaurant=restaurant.serialize)
		
	else:
		return render_template("editRestaurantpage.html", restaurant=restaurant, user_id = login_session["user_id"])

@app.route("/api/json/restaurants/<int:restaurant_id>/delete/", methods=["GET", "POST"])
@app.route("/restaurants/<int:restaurant_id>/delete/", methods=["GET", "POST"])
def restaurantDeleteRoute(restaurant_id):
	if("user_name" not in login_session):
		return redirect(url_for(showLogin))
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if(restaurant.user_id != login_session["user_id"]):
		flash("You are not permitted to delete others restaurant's data!")
		return redirect(url_for("homepageRoute"))
	if(request.method == "POST"):
		session.delete(restaurant)
		session.commit()
		return redirect(url_for("homepageRoute"))
	else:
		return render_template("deleteRestaurantpage.html", restaurant = restaurant, user_id = login_session["user_id"])

@app.route("/api/json/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit/", methods=["GET", "POST"])
@app.route("/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit/", methods=["GET", "POST"])
def menuItemEditRoute(restaurant_id, menu_id):
	if("user_name" not in login_session):
		return redirect(url_for(showLogin))
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	item = session.query(MenuItem).filter_by(id = menu_id, restaurant_id = restaurant_id).one()
	if(item.user_id != login_session["user_id"]):
		flash("You are not permitted to modify others restaurant's menu!")
		return redirect(url_for("homepageRoute"))
	if(request.method == "POST"):
		item.name = request.form["name"]
		item.price = request.form["price"]
		item.course = request.form["course"]
		item.description = request.form["description"]
		session.add(item)
		session.commit()
		return redirect(url_for("restaurantRoute", restaurant_id = restaurant_id))
	else:
		return render_template("editMenuItemPage.html", restaurant = restaurant, item=item, user_id = login_session["user_id"])

@app.route("/api/json/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete/", methods=["GET", "POST"])
@app.route("/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete/", methods=["GET", "POST"])
def menuItemDeleteRoute(restaurant_id, menu_id):
	if("user_name" not in login_session):
		return redirect(url_for(showLogin))
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	item = session.query(MenuItem).filter_by(id = menu_id, restaurant_id = restaurant_id).one()
	if(item.user_id != login_session["user_id"]):
		flash("You are not permitted to modify others restaurant's menu!")
		return redirect(url_for("homepageRoute"))
	if(request.method == "POST"):
		session.delete(item)
		session.commit()
		return redirect(url_for("restaurantRoute", restaurant_id = restaurant_id))
	else:
		return render_template("deleteItemPage.html", restaurant = restaurant, item=item, user_id = login_session["user_id"])

@app.route("/api/json/restaurants/<int:restaurant_id>/menu/new_item", methods=["GET", "POST"])
@app.route("/restaurants/<int:restaurant_id>/menu/new_item", methods=["GET", "POST"])
def menuItemAddRoute(restaurant_id):
	if("user_name" not in login_session):
		return redirect(url_for(showLogin))

	restaurant = session.query(Restaurant).filter_by(id= restaurant_id).one()
	if(restaurant.user_id != login_session["user_id"]):
		flash("You are not permitted to modify others restaurant's menu!")
		return redirect(url_for("homepageRoute"))
	if(request.method == "POST"):
		newItem = MenuItem(	name = request.form["name"],
							description = request.form["description"],
							course = request.form["course"],
							price = request.form["price"],
							restaurant_id = restaurant_id,
							user_id = restaurant.user_id)
		session.add(newItem)
		session.commit()
		return redirect(url_for("restaurantRoute", restaurant_id = restaurant_id))
	else:
		return render_template("newMenuItemPage.html", restaurant = restaurant, user_id = login_session["user_id"])


@app.route("/api/json/restaurants/")
def apiRestaurants():
	restaurants = session.query(Restaurant).all()
	return jsonify(restaurants=[restaurant.serialize for restaurant in restaurants])

@app.route("/api/json/restaurants/<int:restaurant_id>/")
def apiSingleRestaurant(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
	return jsonify(restaurant=restaurant.serialize)

@app.route("/api/json/restaurants/<int:restaurant_id>/menu/")
def apiRestaurantMenuItem(restaurant_id):
	items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id).all()
	return jsonify(restaurants=[item.serialize for item in items])

@app.route("/api/json/restaurants/<int:restaurant_id>/menu/<int:menu_id>")
def apiSingleMenuItem(restaurant_id, menu_id):
	menuItem = session.query(MenuItem).filter_by(id = menu_id).one()
	return jsonify(restaurant=menuItem.serialize)

@app.route("/login")
def showLogin():
	state = "".join([random.choice(string.ascii_uppercase + string.digits) for x in xrange(32)])
	login_session["state"] = state
	return render_template("login.html", state = login_session["state"])

@app.route("/gconnect", methods=["POST"])
def gconnect():
	if(request.args.get("state") != login_session["state"]):
		response = make_response(json.dumps("Invalid State Params!"), 401)
		response.headers["Content-Type"] = "application/json"
		return response
	code = request.data
	try:
		#Upgrade authorization code to a credentials object
		oauth_flow = OAuth2WebServerFlow(	client_id='782771806612-7u84sa1hse9e4bau6gdae112ntpm557m.apps.googleusercontent.com',
                           					client_secret='kEpPfrDXJgaHVl7wPj71WIas',
                           					scope='',
                           					redirect_uri='postmessage')
		oauth_flow.redirect_url = "postmessage"
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		print FlowExchangeError.error
		response = make_response(json.dumps("Failed to convert authorization code to credentials!"), 401)
		response.headers["Content-Type"] = "application/json"
		return response

	access_token = credentials.access_token
	url = ("https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=%s" % access_token)
	h = httplib2.Http(disable_ssl_certificate_validation=True)
	result = json.loads(h.request(url, "GET")[1])
	#If error in access token info abort
	if "error" in result and result["error"] is not None:
		response = make_response(json.dumps(result.get("error")), 500)
		response.headers["Content-Type"] = "application/json"
		return response
	#Verify that the access token is for correct user
	gplus_id = credentials.id_token["sub"]
	if result["sub"] != gplus_id:
		response = make_response(json.dumps("Tokens Client Id doesn't matches apps"), 401)
		print "Tokens Client Id doesn't matches apps"
		response.headers["Content-Type"] = "application/json"
		return response

	# Check to see if user already logged in
	stored_credentials = login_session.get("credentials") and Credentials.from_json(login_session.get("credentials"))
	stored_gplus_id = login_session.get("gplus_id")
	if(stored_credentials is not None and gplus_id == stored_gplus_id):
		response = make_response(json.dumps("Current user is already logged in!"), 200)
		response.headers["Content-Type"] = "application/json"

	# store the user credentials and user id in the current session
	login_session["credentials"] = credentials.to_json()
	login_session["gplus_id"] = gplus_id


	#Get user info
	user_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {"access_token": credentials.access_token, "alt": "json"}
	answer = requests.get(user_info_url, params = params)
	data = json.loads(answer.text)

	login_session["user_name"] = data["name"]
	login_session["picture"] = data["picture"]
	login_session["email"] = data["email"]

	user_id = getUserId(login_session["email"])
	if(not user_id):
		user_id = createUser(login_session)
	login_session["user_id"] = user_id

	flash("You are now logged in as %s" % login_session["user_name"])
	output = ''
	output += '<h1>Welcome, '
	output += login_session['user_name']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	print "done!"
	return json.dumps(output)


#Revoke the user from the app
@app.route("/gdisconnect")
def gdisconnect():
	credentials = login_session.get("credentials") and Credentials.new_from_json(login_session.get("credentials"))
	if credentials is None:
		flash("User Not Logged In!")
		return redirect(url_for("homepageRoute"))
	access_token = credentials.access_token
	url = "https://accounts.google.com/o/oauth2/revoke?token=%s" % access_token
	h = httplib2.Http()
	result = h.request(url, "GET")[0]

	if result["status"] == "200":
		del login_session["credentials"]
		del login_session["gplus_id"]
		del login_session["user_name"]
		del login_session["picture"]
		del login_session["email"]
		del login_session["user_id"]
		flash("User logged out successful!")
		return redirect(url_for("homepageRoute"))
	else:
		response = make_response(json.dumps("Failed to logout user!"), 401)
		response.headers["Content-Type"] = "application/json"
		return response
@app.after_request
def afterRequest(response):
	response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	response.headers["Pragma"] = "no-cache"
	response.headers["Expires"] = "0"
	return response

if __name__ == "__main__":
	app.secret_key = "super_secret_key"
	app.debug = True
	app.run(host = "0.0.0.0", port = 5000)