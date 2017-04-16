from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask import session as login_session
import string, random

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Restaurant, Base, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(open('client_secret.json', 'r').read())["web"]["client_id"]

@app.route("/")
@app.route("/restaurants")
def homepageRoute():
	restaurants = session.query(Restaurant).all()

	return render_template("homePage.html", restaurants = restaurants)

@app.route("/api/json/restaurants/add_restaurant", methods=["GET", "POST"])
@app.route("/restaurants/add_restaurant", methods=["GET", "POST"])
def restaurantAddRoute():
	if(request.method == "POST"):
		restaurant = Restaurant(name = request.form["name"], 
								locality = request.form["location"],
								description = request.form["description"])
		session.add(restaurant)
		session.commit()
		if("/api/json/" not in request.url):
			return redirect(url_for('homepageRoute'))
		else:
			return jsonify(restaurant=restaurant.serialize)
	return render_template("addRestaurant.html")


@app.route("/restaurants/<int:restaurant_id>/")
def restaurantRoute(restaurant_id):

	restaurant = session.query(Restaurant).filter_by(id= restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()

	return render_template("restaurantTemplate.html", restaurant=restaurant, items = items)

@app.route("/api/json/restaurants/<int:restaurant_id>/edit/", methods=["GET", "POST"])
@app.route("/restaurants/<int:restaurant_id>/edit/", methods=["GET", "POST"])
def restaurantEditRoute(restaurant_id):
	if(request.method == "POST"):
		restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
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
		restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
		return render_template("editRestaurantpage.html", restaurant=restaurant)

@app.route("/api/json/restaurants/<int:restaurant_id>/delete/", methods=["GET", "POST"])
@app.route("/restaurants/<int:restaurant_id>/delete/", methods=["GET", "POST"])
def restaurantDeleteRoute(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	if(request.method == "POST"):
		session.delete(restaurant)
		session.commit()
		return redirect(url_for("homepageRoute"))
	else:
		return render_template("deleteRestaurantpage.html", restaurant = restaurant)

@app.route("/api/json/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit/", methods=["GET", "POST"])
@app.route("/restaurants/<int:restaurant_id>/menu/<int:menu_id>/edit/", methods=["GET", "POST"])
def menuItemEditRoute(restaurant_id, menu_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	item = session.query(MenuItem).filter_by(id = menu_id, restaurant_id = restaurant_id).one()
	if(request.method == "POST"):
		item.name = request.form["name"]
		item.price = request.form["price"]
		item.course = request.form["course"]
		item.description = request.form["description"]
		session.add(item)
		session.commit()
		return redirect(url_for("restaurantRoute", restaurant_id = restaurant_id))
	else:
		return render_template("editMenuItemPage.html", restaurant = restaurant, item=item)

@app.route("/api/json/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete/", methods=["GET", "POST"])
@app.route("/restaurants/<int:restaurant_id>/menu/<int:menu_id>/delete/", methods=["GET", "POST"])
def menuItemDeleteRoute(restaurant_id, menu_id):
	restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
	item = session.query(MenuItem).filter_by(id = menu_id, restaurant_id = restaurant_id).one()
	if(request.method == "POST"):
		session.delete(item)
		session.commit()
		return redirect(url_for("restaurantRoute", restaurant_id = restaurant_id))
	else:
		return render_template("deleteItemPage.html", restaurant = restaurant, item=item)

@app.route("/api/json/restaurants/<int:restaurant_id>/menu/new_item", methods=["GET", "POST"])
@app.route("/restaurants/<int:restaurant_id>/menu/new_item", methods=["GET", "POST"])
def menuItemAddRoute(restaurant_id):
	restaurant = session.query(Restaurant).filter_by(id= restaurant_id).one()
	if(request.method == "POST"):
		newItem = MenuItem(	name = request.form["name"],
							description = request.form["description"],
							course = request.form["course"],
							price = request.form["price"],
							restaurant_id = restaurant_id)
		session.add(newItem)
		session.commit()
		return redirect(url_for("restaurantRoute", restaurant_id = restaurant_id))
	else:
		return render_template("newMenuItemPage.html", restaurant = restaurant)


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
		oauth_flow = flow_from_clientsecrets("client_secret.json", scope="")
		oauth_flow.redirect_url = "postmessage"
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps("Failed to convert authorization code to credentials!"), 401)
		response.headers["Content-Type"] = "application/json"
		return response

	access_token = credentials.access_token
	url = ("https://googleapis.com/oauth2/v1/tokeninfo?access_token=%s" % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, "GET")[1])

	#If error in access token info abort
	if result["error"] is not None:
		response = make_response(json.dumps(result.get("error")), 500)
		response.headers["Content-Type"] = "application/json"
		return response
	#Verify that the access token is for correct user
	gplus_id = credentials.id_token["sub"]
	if result["issued_to"] == gplus_id:
		response = make_response(json.dumps("Tokens Client Id doesn't matches apps"), 401)
		print "Tokens Client Id doesn't matches apps"
		response.headers["Content-Type"] = "application/json"
		return response

	# Check to see if user already logged in
	stored_credentials = login_session.get("credentials")
	stored_gplus_id = login_session.get("gplus_id")
	if(stored_credentials is not None and gplus_id == stored_gplus_id):
		response = make_response(json.dump("Current user is already logged in!"), 200)
		response.headers["Content-Type"] = "application/json"

	# store the user credentials and user id in the current session
	login_session["credentials"] = credentials
	login_session["gplus_id"] = gplus_id


	#Get user info
	user_info_url = "http://www.googleapis.com/oauth2/v1/userinfo"
	params = {"access_token": credentials.access_token, "alt": "json"}
	answer = requests.get(user_info_url, params = params)
	data = json.loads(answer.text)

	login_session["user_name"] = data["name"]
	login_session["picture"] = data["picture"]
	login_session["email"] = data["email"]
	flash("You are now logged in as %s" % login_session["user_name"])
	return redirect(url_for("homepageRoute"))


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