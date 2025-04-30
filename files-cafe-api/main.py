from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.oracle.dictionary import dictionary_meta
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
import random

app = Flask(__name__)


# CREATE DB
class Base(DeclarativeBase):
    pass
# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # map_url: Mapped[str] = mapped_column(String(500), nullable=True)

    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    #we are going to use this method to serialising our database for json to json
    def to_dict(self):
        # Method 1.
        dictionary = {}
        # we are setting a Loop through each column in the data record
        for column in self.__table__.columns:
            # Create a new dictionary entry;
            # where the key is the name of the column
            # and the value is the value of the column
            dictionary[column.name] = getattr(self, column.name)
        return dictionary

        # Method 2.  use Dictionary Comprehension to do the same thing.
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}




# @app.route("/random", methods=["GET"])
# def get_random_cafe():
#     pass


@app.route("/random")
def get_random_cafe():
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()
    random_cafe = random.choice(all_cafes)
    return jsonify(cafe=random_cafe.to_dict())

@app.route("/all")
def get_all_cafes():
    result = db.session.execute(db.select(Cafe).order_by(Cafe.name))
    all_cafes = result.scalars().all()

    #this help to split it into three part
    return jsonify(cafes=[cafe.to_dict()  for cafe in all_cafes])

@app.route("/search")
def get_cafe_at_location():
            query_location = request.args.get("loc")
            result = db.session.execute(db.select(Cafe).where(Cafe.location == query_location))
            # Note, this may get more than one cafe per location
            all_cafes = result.scalars().all()
            if all_cafes:
                return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])
            else:
                return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."}), 404

@app.route("/add", methods=["POST"])
def post_new_cafe():
    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("location"),
        seats=request.form.get("seats"),
        has_toilet=bool(int(request.form.get("has_toilet"))),
        has_wifi=bool(int(request.form.get("has_wifi",0))),
        has_sockets=bool(int(request.form.get("has_sockets",0))),
        can_take_calls=bool(int(request.form.get("can_take_calls",0))),
        coffee_price=request.form.get("coffee_price"),
    )
    db.session.add(new_cafe)
    db.session.commit()
    return jsonify(response={"success": "Cafe added successfully!"})
# HTTP GET - Read Record

# HTTP POST - Create Record

# HTTP PUT/PATCH - Update Record

# Updating the price of a cafe based on a particular id:
# http://127.0.0.1:5000/update-price/CAFE_ID?new_price=£5.67
@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def patch_new_price(cafe_id):
    new_price = request.args.get("new_price")
    try:
        cafe = db.get(Cafe, cafe_id)
    except AttributeError:
        return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404
    else:
        cafe.coffee_price = new_price
        db.session.commit()
        return jsonify(response={"success": "Successfully updated the price."}), 200

# HTTP DELETE - Delete Record
# Deletes a cafe with a particular id. Change the request type to "Delete" in Postman
# @app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
# def delete_cafe(cafe_id):
#     api_key = request.args.get("api-key")
#     if api_key == "TopSecretAPIKey":
#         try:
#             cafe = db.get(Cafe, cafe_id)
#         except AttributeError:
#             return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404
#         else:
#             db.session.delete(cafe)
#             db.session.commit()
#             return jsonify(response={"success": "Successfully deleted the cafe from the database."}), 200
#     else:
#         return jsonify(error={"Forbidden": "Sorry, that's not allowed. Make sure you have the correct api_key."}), 403
#     print("API Key received:", api_key)

@app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
def delete_cafe(cafe_id):
    api_key = request.headers.get("x-api-key")  # Get from headers

    if api_key != "TopSecretAPIKey":
        return jsonify(error={
            "Forbidden": "Invalid or missing API key."
        }), 403

    cafe = db.get(Cafe, cafe_id)
    if not cafe:
        return jsonify(error={
            "Not Found": "No cafe with that ID."
        }), 404

    db.session.delete(cafe)
    db.session.commit()
    return jsonify(response={
        "success": "Cafe deleted successfully."
    }), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
