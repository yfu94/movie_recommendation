from flask import Flask, render_template, request
import pandas as pd
from fuzzywuzzy import process

class Movie:
    def __init__(self, title, director, actors, year, genre, rating, votes, runtime, revenue, metascore):
        self.title = title
        self.director = director
        self.actors = actors
        self.year = year
        self.genre = genre
        self.rating = rating
        self.votes = votes
        self.runtime = runtime
        self.revenue = revenue
        self.metascore = metascore

    def display_info(self):
        print(f"{self.title} directed by {self.director}, released in {self.year}, Genre: {self.genre}, Rating: {self.rating}.")

# load data 
def load_data(file_path):
    # Load the dataset
    df_movies = pd.read_csv(file_path)

    movies = []
    genre_dict = {}
    for index, row in df_movies.iterrows():
        movie = Movie(
            title=row['Title'],
            director=row['Director'],
            actors=row['Actors'],
            year=row['Year'],
            genre=row['Genre'],
            rating=row['Rating'],
            votes=row['Votes'],
            runtime=row['Runtime (Minutes)'],
            revenue=row['Revenue (Millions)'],
            metascore=row['Metascore']
        )
        movies.append(movie)
        individual_genre = [g.strip().lower() for g in row['Genre'].split(',')]
        for genre in individual_genre:
            if genre not in genre_dict:
                genre_dict[genre] = []
            genre_dict[genre].append(movie)
        
    return movies, genre_dict
# data loading
movies, genre_dict = load_data('./imdb_movie_dataset.csv')


class MovieRecommendationSystem:
    def __init__(self):
        self.movie_list = movies  # List of Movie objects
        self.genre_dict = genre_dict
    
    # developer use only, add new movie from backend
    def add_movie(self, title, director, actors, year, genre, rating, votes, runtime, revenue, metascore):
        new_movie = Movie(title, director, actors, year, genre, rating, votes, runtime, revenue, metascore)
        for individual_genre in genre:
            if individual_genre not in self.genre_dict:
                self.genre_dict[genre] = []
            self.genre_dict.append(new_movie)

    # for final display of result, thinking of user behavior, we rank by two parameters when ranking by year/rating
    def rank_movies(self, results, ranking_option):
        # Ensure results are sorted based on the ranking_option
        if ranking_option == "title":
            return sorted(results, key=lambda x: x.title.lower())  # sort by title alphabetically
        elif ranking_option == "rating":
            return sorted(results, key=lambda x: (-x.rating, -x.year))  # sort by rating (highest first), then year
        elif ranking_option == "year":
            return sorted(results, key=lambda x: (-x.year, -x.rating))  # sort by year (latest first), then rating
        return results

    def get_movies_by_title(self, user_title):
        # Invalid input handling moved to frontend, prevent from submissiom
        user_title = user_title.strip()
        # Exact match
        exact_matches = [movie for movie in self.movie_list if movie.title.lower() == user_title.lower()]
        
        # Fuzzy search (partial match)
        partial_matches = [movie for movie in self.movie_list if user_title.lower() in movie.title.lower()]
    
        if exact_matches:
            return exact_matches, "Exact match found:"
        elif partial_matches:
            return partial_matches, f"No exact match found for '{user_title}'. Did you mean:"
        else:
            return None, "No result found. Please try again with another movie."


    def get_movies_by_genre(self, user_genre):
        # unify format (lower-case) for easier search
        user_genre = user_genre.lower()
        # Exact match results
        if user_genre in self.genre_dict:
            filtered_movies = self.genre_dict[user_genre]
            return filtered_movies, f"{len(filtered_movies)} movies found for genre '{user_genre}':"
        
        # handle fuzzy matching if no exact match using 3rd party library
        genre_list = list(self.genre_dict.keys())
        best_match, score = process.extractOne(user_genre, genre_list)
        if score < 80:
            # No good matches found
            return None, f"No close matches found for genre '{user_genre}'. Please try again."

        # return fuzzy match results
        filtered_movies = self.genre_dict[best_match]
        return filtered_movies, f"No exact match found for '{user_genre}'. Did you mean '{best_match}'?"


    def get_movies_by_rating(self, user_rating):
        # Invalid input handling moved to frontend, prevent from submissiom
        user_rating = float(user_rating.strip())
        # Filter movies based on the minimum rating
        filtered_movies = [movie for movie in self.movie_list if movie.rating >= user_rating]
        if not filtered_movies:
            return None, f"No movies found with a rating of {user_rating} or higher"
        return filtered_movies, f"Found {len(filtered_movies)} with rating of {user_rating} or higher:"
    

    def get_movies_by_year(self, user_year):
        # Invalid input handling moved to frontend, prevent from submissiom
        user_year = int(user_year.strip())
        filtered_movies = [movie for movie in self.movie_list if movie.year == user_year]
        if not filtered_movies:
            return None, f"No movies found for the year {user_year}."
        return filtered_movies, f"Found {len(filtered_movies)} for the year {user_year}:"
    

    def get_top_rated_movies(self, user_top_n):
        # Invalid input handling moved to frontend, prevent from submissiom
        user_top_n = int(user_top_n.strip())
        # in case out of index
        movie_list_len = len(self.movie_list)
        final_top_n = min(user_top_n, movie_list_len)
        top_movies = sorted(self.movie_list, key=lambda x: (-x.rating, -x.year))[:final_top_n]
        if user_top_n > movie_list_len:
            return top_movies, f"You entered a value greater than the number of movies we have. Showing the maximum {movie_list_len} of movies:"
        else:
            return top_movies, f"Showing the top {user_top_n} of movies:"


# Flask App
app = Flask(__name__)
rs = MovieRecommendationSystem()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search_by_title", methods=["POST", "GET"])
def search_by_title():
    if request.method == "POST":
        title = request.form["title"]
        results, message = rs.get_movies_by_title(title)
        ranking_option = request.form.get("ranking_option", "title")  # since member searched title
        current_source = "search_by_title"
        current_default_sort = "title"   
        if results:
            # Rank movies based on user selection
            ranked_results = rs.rank_movies(results, ranking_option)
            return render_template("results_search.html", results=ranked_results, message=message, source =current_source, default_sort=current_default_sort)
        else:
            return render_template("results_search.html", results=None, message=message, source =current_source, default_sort=current_default_sort)
    return render_template("search_by_title.html")

@app.route("/search_by_genre", methods=["POST", "GET"])
def search_by_genre():
    if request.method == "POST":
        genre = request.form["genre"]
        results, message = rs.get_movies_by_genre(genre)
        ranking_option = request.form.get("ranking_option", "year")  # since member searched genre, let's show latest movie first 
        current_source = "search_by_genre"
        current_default_sort = "year"       
        if results:
            # Rank movies based on user selection
            ranked_results = rs.rank_movies(results, ranking_option)
            return render_template("results_search.html", results=ranked_results, message=message, source =current_source, default_sort=current_default_sort)
        else:
            return render_template("results_search.html", results=None, message=message, source =current_source, default_sort=current_default_sort)
    return render_template("search_by_genre.html")

@app.route("/search_by_rating", methods=["POST", "GET"])
def search_by_rating():
    if request.method == "POST":
        rating = request.form["rating"]
        results, message = rs.get_movies_by_rating(rating)
        ranking_option = request.form.get("ranking_option", "rating")  # Default to ranking by rating
        current_source = "search_by_rating"
        current_default_sort = "rating" # since member searched on rating
        if results:
            # Rank movies based on user selection
            ranked_results = rs.rank_movies(results, ranking_option)
            return render_template("results_search.html", results=ranked_results, message=message, source =current_source, default_sort=current_default_sort)
        else:
            return render_template("results_search.html", results=None, message=message, source =current_source, default_sort=current_default_sort)
    return render_template("search_by_rating.html")

@app.route("/search_by_year", methods=["POST", "GET"])
def search_by_year():
    if request.method == "POST":
        year = request.form["year"]
        results, message = rs.get_movies_by_year(year)
        ranking_option = request.form.get("ranking_option", "rating")  # since year is fixed, show highest rating movie first
        current_source = "search_by_year"
        current_default_sort = "rating"
        if results:
            # Rank movies based on user selection
            ranked_results = rs.rank_movies(results, ranking_option)
            return render_template("results_search.html", results=ranked_results, message=message, source =current_source, default_sort=current_default_sort)
        else:
            return render_template("results_search.html", results=None, message=message, source =current_source, default_sort=current_default_sort)
    return render_template("search_by_year.html")

@app.route("/top_rated_movies", methods=["POST", "GET"])
def top_rated_movies():
    if request.method == "POST":
        top_n = request.form["top_n"]
        results, message = rs.get_top_rated_movies(top_n)
        ranking_option = request.form.get("ranking_option", "rating")  # Default to ranking by rating, since user want top rated movies
        current_source = "top_rated_movies"
        current_default_sort = "rating"
        if results:
            ranked_results = rs.rank_movies(results, ranking_option)
            return render_template("results_search.html", results=ranked_results, message=message, source =current_source, default_sort=current_default_sort)
        else:
            return render_template("results_search.html", results=None, message=message, source =current_source, default_sort=current_default_sort)
    return render_template("top_rated_movies.html")

@app.route("/recommendation", methods=["POST", "GET"])
def recommend():
    if request.method == "POST":
        recommendation_type = request.form["recommendation_type"].lower()
        
        # Handle recommendations based on genre or rating
        if recommendation_type == "genre":
            genre = request.form["genre"]
            results, message = rs.get_movies_by_genre(genre)
            num = min(len(results), 20) # default to top 20 movies, if returned result is less than 20, show number of returned result
            new_message = f"Recommended following {num} movies that you may be interested!"
            ranking_option = request.form.get("ranking_option", "year")  # since member searched genre, let's show latest movie first 
            current_source = "search_by_genre"
            current_default_sort = "year"       
        
        elif recommendation_type == "rating":
            rating = request.form["rating"]
            results, message = rs.get_movies_by_rating(rating)
            num = min(len(results), 20) # default to top 20 movies, if returned result is less than 20, show number of returned result 
            new_message = f"Recommended top {num} movies for you!"
            ranking_option = request.form.get("ranking_option", "rating")  # # since member searched on rating
            current_source = "search_by_rating"
            current_default_sort = "rating" 

        # Limit results to top 20 and render results page
        if results:
            # Rank movies based on user selection
            ranked_results = rs.rank_movies(results, ranking_option)[:20]
            return render_template("results_recommendation.html", results=ranked_results, message=new_message, source =current_source, default_sort=current_default_sort, recommendation_type=recommendation_type)
        else:
            return render_template("results_recommendation.html", results=None, message=new_message, source =current_source, default_sort=current_default_sort, recommendation_type=recommendation_type)

    return render_template("recommendation.html")


if __name__ == "__main__":
    app.run(debug=True)