from flask import Flask, render_template, redirect, request, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import os
from dotenv  import load_dotenv
load_dotenv()


app = Flask(__name__)
# Flask Bootstrap
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
# Flask SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# The Movie Database API
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
TMDB_URL = os.getenv('TMDB_URL')


# Database
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(255), nullable=True)
    img_url = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Title: {self.title}>"


if not os.path.exists('movie-collection.db'):
    db.create_all()


# edit movie form
class EditMovie(FlaskForm):
    rating = FloatField(
        label='Your Rating Out of 10 e.g. 7.5',
        validators=[
            DataRequired(),
        ]
    )
    review = StringField(
        label='Your Review',
        validators=[
            DataRequired()
        ]
    )
    submit = SubmitField(label='Done')


# add movie form
class AddMovie(FlaskForm):
    title = StringField(
        label='Movie TItle',
        validators=[
            DataRequired(),
        ]
    )
    submit = SubmitField(label='Add Movie')


# new_movie = Movie(
#     title="Phone Boothsss",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg",
# )
# db.session.add(new_movie)
# db.session.commit()


@app.route("/")
def home():
    try:
        rating_ordered_movies = Movie.query.order_by(Movie.rating).all()
        x = -1
        for movie in rating_ordered_movies:
            x += 1
            selected_movie = Movie.query.filter_by(rating=movie.rating).first()
            selected_movie.ranking = (int(len(rating_ordered_movies)) - x)
            db.session.commit()

        movie_list = Movie.query.order_by(Movie.ranking).all()
        movie_list.reverse()

    except OperationalError:
        movie_list = []
    
    return render_template("index.html", movies=movie_list)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    movie_id = request.args.get('id')
    selected_movie = Movie.query.get(movie_id)

    edit_movie = EditMovie()
    if edit_movie.validate_on_submit():
        new_rating = edit_movie.rating.data
        new_review = edit_movie.review.data
        movie_to_update = Movie.query.get(movie_id)
        movie_to_update.rating = new_rating
        movie_to_update.review = new_review
        db.session.commit()
        return redirect("/")

    return render_template("edit.html", movie=selected_movie, form=edit_movie)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect("/")


@app.route("/add", methods=['POST', 'GET'])
def add():
    add_movie = AddMovie()
    if add_movie.validate_on_submit():
        movie_title = add_movie.title.data

        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US',
            'query': movie_title,
            'page': 1
        }
        url = f"{TMDB_URL}/search/movie"
        response = requests.get(url=url, params=params)
        response.raise_for_status()
        data = response.json()
        movie_lists = data['results']

        return render_template('select.html', movies=movie_lists)

    return render_template("add.html", form=add_movie)


@app.route("/select")
def select():
    movie_id = request.args.get('id')

    params = {
        'api_key': TMDB_API_KEY,
        'language': 'en-US',
    }
    url = f"{TMDB_URL}/movie/{movie_id}"
    response = requests.get(url=url, params=params)
    response.raise_for_status()
    data = response.json()

    title = data['original_title']
    img_url = f"http://image.tmdb.org/t/p/w185{data['poster_path']}"
    year = data['release_date']
    description = data['overview']

    new_movie = Movie(
        title=title,
        year=year,
        description=description,
        img_url=img_url,
    )
    db.session.add(new_movie)
    db.session.commit()

    movie_selected = Movie.query.filter_by(title=title).first()
    movie_id = movie_selected.id

    return redirect(url_for('edit', id=movie_id))


if __name__ == '__main__':
    app.run(debug=True)
