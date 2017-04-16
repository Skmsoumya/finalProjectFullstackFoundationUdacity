from flask import Flask, render_template, redirect, url_for, request, jsonify

from dummyData import dummyData

app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Restaurant, Base, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

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