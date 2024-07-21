from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

def restaurant_to_dict(restaurant):
    return {
        'id': restaurant.id,
        'name': restaurant.name,
        'address': restaurant.address
    }

def restaurant_with_pizzas_to_dict(restaurant):
    return {
        'id': restaurant.id,
        'name': restaurant.name,
        'address': restaurant.address,
        'restaurant_pizzas': [restaurant_pizza_to_dict(rp) for rp in restaurant.restaurant_pizzas]
    }

def pizza_to_dict(pizza):
    return {
        'id': pizza.id,
        'name': pizza.name,
        'ingredients': pizza.ingredients
    }

def restaurant_pizza_to_dict(restaurant_pizza):
    return {
        'id': restaurant_pizza.id,
        'price': restaurant_pizza.price,
        'restaurant_id': restaurant_pizza.restaurant_id,
        'pizza_id': restaurant_pizza.pizza_id,
        'pizza': pizza_to_dict(restaurant_pizza.pizza)
    }

class RestaurantListResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return make_response(jsonify([restaurant_to_dict(restaurant) for restaurant in restaurants]), 200)

class RestaurantResource(Resource):
    def get(self, id):
        restaurant = db.session.get(Restaurant, id)
        if restaurant is None:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        return make_response(jsonify(restaurant_with_pizzas_to_dict(restaurant)), 200)

    def delete(self, id):
        restaurant = db.session.get(Restaurant, id)
        if restaurant is None:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)
        db.session.delete(restaurant)
        db.session.commit()
        return make_response('', 204)

class PizzaListResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return make_response(jsonify([pizza_to_dict(pizza) for pizza in pizzas]), 200)

class RestaurantPizzaResource(Resource):
    def post(self):
        data = request.json
        restaurant_id = data.get("restaurant_id")
        pizza_id = data.get("pizza_id")
        price = data.get("price")

        restaurant = db.session.get(Restaurant, restaurant_id)
        if not restaurant:
            return make_response(jsonify({"error": "Restaurant not found"}), 404)

        pizza = db.session.get(Pizza, pizza_id)
        if not pizza:
            return make_response(jsonify({"error": "Pizza not found"}), 404)

        if price is None or not 1 <= price <= 30:
            return make_response(jsonify({"errors": ["validation errors"]}), 400)

        restaurant_pizza = RestaurantPizza(restaurant_id=restaurant_id, pizza_id=pizza_id, price=price)
        db.session.add(restaurant_pizza)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({"error": str(e)}), 500)

        return make_response(jsonify({
            "id": restaurant_pizza.id,
            "pizza": pizza_to_dict(pizza),
            "pizza_id": pizza_id,
            "price": price,
            "restaurant": restaurant_to_dict(restaurant),
            "restaurant_id": restaurant_id,
        }), 201)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({"error": "Resource not found"}), 404)

api.add_resource(RestaurantListResource, '/restaurants')
api.add_resource(RestaurantResource, '/restaurants/<int:id>')
api.add_resource(PizzaListResource, '/pizzas')
api.add_resource(RestaurantPizzaResource, '/restaurant_pizzas')

if __name__ == "__main__":
    app.run(port=5555, debug=True)