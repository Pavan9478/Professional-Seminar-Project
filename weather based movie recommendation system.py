import os
import json
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import requests
import pandas as pd
import random
import re
import io
import hashlib
import logging
from imdb import IMDb  # Import cinemagoer

# Configure logging
logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class User:
    def __init__(self, email, password, genres=None, notifications=False, watchlist=None, ratings=None, genre_preferences=None):
        self.email = email
        self.password = self.hash_password(password) if not self.is_hashed(password) else password
        self.genres = genres if genres else []
        self.notifications = notifications
        self.watchlist = watchlist if watchlist else []  # 3.2 Watchlist
        self.ratings = ratings if ratings else {}        # 3.3 Ratings
        # 3.4 Genre preferences per weather condition
        self.genre_preferences = genre_preferences if genre_preferences else {
            "thunderstorm": ["Action", "Thriller"],
            "drizzle": ["Drama", "Romance"],
            "rain": ["Drama", "Romance"],
            "snow": ["Animation", "Family"],
            "mist": ["Mystery", "Fantasy"],
            "fog": ["Mystery", "Fantasy"],
            "haze": ["Mystery", "Fantasy"],
            "clear": ["Adventure", "Comedy"],
            "clouds": ["Documentary", "Sci-Fi"]
        }

    @staticmethod
    def hash_password(password):
        """Hash the password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def is_hashed(password):
        """Check if the password is already hashed."""
        return bool(re.fullmatch(r'[a-fA-F0-9]{64}', password))

    def to_dict(self):
        return {
            'email': self.email,
            'password': self.password,
            'genres': self.genres,
            'notifications': self.notifications,
            'watchlist': self.watchlist,             # 3.2 Watchlist
            'ratings': self.ratings,                 # 3.3 Ratings
            'genre_preferences': self.genre_preferences  # 3.4 Genre Preferences
        }

    @staticmethod
    def from_dict(data):
        return User(
            email=data['email'],
            password=data['password'],  # Assumes password is already hashed
            genres=data.get('genres', []),
            notifications=data.get('notifications', False),
            watchlist=data.get('watchlist', []),
            ratings=data.get('ratings', {}),
            genre_preferences=data.get('genre_preferences', {
                "thunderstorm": ["Action", "Thriller"],
                "drizzle": ["Drama", "Romance"],
                "rain": ["Drama", "Romance"],
                "snow": ["Animation", "Family"],
                "mist": ["Mystery", "Fantasy"],
                "fog": ["Mystery", "Fantasy"],
                "haze": ["Mystery", "Fantasy"],
                "clear": ["Adventure", "Comedy"],
                "clouds": ["Documentary", "Sci-Fi"]
            })
        )

class UserManager:
    def __init__(self, filename='users.json'):
        self.filename = filename
        self.users = self.load_users()

    def load_users(self):
        if not os.path.exists(self.filename):
            logging.info(f"{self.filename} not found. Starting with an empty user list.")
            return []
        with open(self.filename, 'r') as file:
            try:
                data = json.load(file)
                if isinstance(data, list):
                    users = []
                    for user_data in data:
                        if isinstance(user_data, dict):
                            if 'password' in user_data:
                                user = User.from_dict(user_data)
                                users.append(user)
                            else:
                                logging.error(f"User data missing 'password' field: {user_data}")
                        else:
                            logging.error(f"Invalid user data format: {user_data}")
                    return users
                else:
                    logging.error(f"{self.filename} does not contain a list.")
                    return []
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding JSON from {self.filename}: {e}")
                return []

    def save_users(self):
        with open(self.filename, 'w') as file:
            data = [user.to_dict() for user in self.users]
            json.dump(data, file, indent=4)
            logging.info("Users saved successfully.")

    def register_user(self, email, password):
        if any(user.email == email for user in self.users):
            logging.warning(f"Registration failed: Email {email} is already registered.")
            return False
        new_user = User(email, password)
        self.users.append(new_user)
        self.save_users()
        logging.info(f"User registered successfully: {email}")
        return True

    def sign_in_user(self, email, password):
        hashed_password = User.hash_password(password)
        for user in self.users:
            if user.email == email and user.password == hashed_password:
                logging.info(f"Sign-in successful for user: {email}")
                return True
        logging.warning(f"Sign-in failed for user: {email}")
        return False

    def find_user(self, email):
        for user in self.users:
            if user.email == email:
                return user
        return None

    def reset_password(self, email, new_password):
        user = self.find_user(email)
        if user:
            user.password = User.hash_password(new_password)
            self.save_users()
            logging.info(f"Password reset successful for user: {email}")
            return True
        logging.error(f"Password reset failed: Email {email} not found.")
        return False

    def delete_account(self, email):
        user = self.find_user(email)
        if user:
            self.users.remove(user)
            self.save_users()
            logging.info(f"Account deleted successfully for user: {email}")
            return True
        logging.error(f"Account deletion failed: Email {email} not found.")
        return False

    def edit_profile(self, email, new_email=None, new_password=None, new_genres=None, new_genre_preferences=None):
        user = self.find_user(email)
        if user:
            if new_email:
                if any(u.email == new_email for u in self.users):
                    logging.warning(f"Edit profile failed: New email {new_email} is already taken.")
                    return False, "Email is already taken."
                user.email = new_email
            if new_password:
                user.password = User.hash_password(new_password)
            if new_genres is not None:
                user.genres = new_genres
            if new_genre_preferences is not None:
                user.genre_preferences = new_genre_preferences
            self.save_users()
            logging.info(f"Profile updated successfully for user: {email}")
            return True, "Profile updated successfully."
        logging.error(f"Profile update failed: Email {email} not found.")
        return False, "Email not found."

    def set_notifications(self, email, notifications):
        user = self.find_user(email)
        if user:
            user.notifications = notifications
            self.save_users()
            logging.info(f"Notification preferences updated for user: {email}")
            return True
        logging.error(f"Setting notifications failed: Email {email} not found.")
        return False

class WeatherService:
    def __init__(self, weather_api_key):
        self.weather_api_key = weather_api_key
        self.location = None

    def fetch_weather_data(self, location):
        """Fetch weather data for the given location using OpenWeatherMap API."""
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "APPID": self.weather_api_key,
            "units": "metric"  # For temperature in Celsius
        }
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            if "weather" in data:
                weather_description = data["weather"][0]["description"]
                temperature = data["main"]["temp"]
                icon_code = data["weather"][0]["icon"]
                logging.info(f"Weather data fetched successfully for location: {location}")
                return {
                    "weather": weather_description.capitalize(),
                    "temperature": temperature,
                    "icon_code": icon_code
                }
            else:
                logging.error(f"Weather data unavailable for location: {location}")
                return {"weather": "Unavailable", "temperature": "N/A", "icon_code": None}
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching weather data for {location}: {e}")
            return {"weather": "Unavailable", "temperature": "N/A", "icon_code": None}

class MovieRecommender:
    def __init__(self, movies_file_path, cinemagoer_instance):
        self.movies_data = self.load_movies(movies_file_path)
        self.cinemagoer = cinemagoer_instance
        if not self.movies_data.empty:
            self.movies_data['year'] = self.movies_data['title'].apply(self.extract_year)
            self.movies_data['clean_title'] = self.movies_data['title'].apply(self.clean_title)
        else:
            logging.error("Movies data is empty. Please check the movies.csv file.")

    def load_movies(self, path):
        if not os.path.exists(path):
            logging.error(f"Movies file not found at path: {path}")
            return pd.DataFrame()
        try:
            data = pd.read_csv(path)
            logging.info(f"Movies data loaded successfully from {path}")
            return data
        except Exception as e:
            logging.error(f"Error loading movies data from {path}: {e}")
            return pd.DataFrame()

    @staticmethod
    def extract_year(title):
        """Extract year from movie title."""
        match = re.search(r'\((\d{4})\)', title)
        if match:
            return int(match.group(1))
        return None

    @staticmethod
    def clean_title(title):
        """Remove the year from the title if present."""
        return re.sub(r'\s*\(\d{4}\)', '', title).strip()

    def get_movie_details(self, title):
        """Fetch movie details using cinemagoer (IMDb)."""
        try:
            search_results = self.cinemagoer.search_movie(title)
            if not search_results:
                logging.warning(f"No IMDb results found for movie: {title}")
                return None
            # Assume the first result is the correct one
            movie = search_results[0]
            self.cinemagoer.update(movie)
            details = {
                "Title": movie.get('title', 'N/A'),
                "Year": movie.get('year', 'N/A'),
                "Genre": ', '.join(movie.get('genres', [])),
                "Language": ', '.join(movie.get('languages', [])),
                "Plot": movie.get('plot outline', 'N/A'),
                "Poster": movie.get('full-size cover url', None)
            }
            logging.info(f"Fetched details for movie: {title}")
            return details
        except Exception as e:
            logging.error(f"Error fetching details for {title}: {e}")
            return None

    def recommend_movies(self, weather, genre_preferences, decade=None, filters=None, user_ratings=None):
        """Recommend movies based on the weather, genre preferences, optionally filter by decade and other filters."""
        weather_genre_mapping = genre_preferences

        recommended_movies = []
        for key, genres in weather_genre_mapping.items():
            if key in weather.lower():
                filtered_movies = self.movies_data[
                    self.movies_data['genres'].str.contains('|'.join(genres), case=False, na=False)
                ]

                filtered_movies = filtered_movies[filtered_movies['year'].notna()]
                if decade:
                    filtered_movies = filtered_movies[
                        (filtered_movies['year'] >= decade) & (filtered_movies['year'] < decade + 10)
                    ]

                # Apply additional filters
                if filters:
                    if 'genre' in filters and filters['genre']:
                        filtered_movies = filtered_movies[
                            filtered_movies['genres'].str.contains(filters['genre'], case=False, na=False)
                        ]
                    if 'year' in filters and filters['year']:
                        try:
                            year = int(filters['year'])
                            filtered_movies = filtered_movies[
                                self.movies_data['year'] == year
                            ]
                        except ValueError:
                            messagebox.showerror("Error", "Please enter a valid year for filtering.")
                            return ["No movies found for the selected criteria."]

                if not filtered_movies.empty:
                    # Incorporate user ratings by preferring higher-rated movies
                    if user_ratings:
                        filtered_movies['rating'] = filtered_movies['title'].apply(lambda x: user_ratings.get(x, 0))
                        filtered_movies = filtered_movies.sort_values(by='rating', ascending=False)

                    recommended_movies = filtered_movies.sample(n=min(5, len(filtered_movies)))['title'].tolist()
                    logging.info(f"Recommended movies based on weather '{weather}', decade '{decade}', and filters '{filters}'")
                    return recommended_movies

        logging.warning(f"No movies found for the selected weather '{weather}', decade '{decade}', and filters '{filters}'.")
        return ["No movies found for the selected criteria."]

class GUIApplication:
    def __init__(self):
        # Create main window
        self.window = self.create_main_window()
        self.signed_in_email = tk.StringVar()
        self.user_manager = UserManager()
        # Initialize weather service and movie recommender
        self.weather_service = WeatherService(weather_api_key="9317738386fb8a28b8b117a760bfe9d0")  # Replace with your OpenWeatherMap API key
        self.cinemagoer_instance = IMDb()
        self.movie_recommender = MovieRecommender(
            movies_file_path="C:/Users/kalya/Desktop/Homeworks/Fall 2024/Term 1/Raja Pavan Pasupuleti/Professional Seminar Pitts/Project/3/movies.csv",
            cinemagoer_instance=self.cinemagoer_instance
        )
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=1, fill="both")
        
        # Create tabs
        self.auth_tab = ttk.Frame(self.notebook)
        self.profile_tab = ttk.Frame(self.notebook)
        self.recommendations_tab = ttk.Frame(self.notebook)
        self.watchlist_tab = ttk.Frame(self.notebook)  # 3.2 Watchlist
        self.search_tab = ttk.Frame(self.notebook)     # 3.5 Search

        # Add auth_tab to notebook
        self.notebook.add(self.auth_tab, text="Authentication")
        
        # Setup the tabs
        self.setup_auth_tab()
        # Do not setup other tabs yet; they will be set up after login

    def create_main_window(self):
        window = tk.Tk()
        window.title("Weather-based Movie Recommendation System")
        window.geometry("800x700")
        return window

    def setup_auth_tab(self):
        # Set up the authentication tab
        tk.Button(self.auth_tab, text="Register", width=20, command=self.register_user_gui).pack(pady=20)
        tk.Button(self.auth_tab, text="Sign In", width=20, command=self.sign_in_user_gui).pack(pady=20)
        tk.Button(self.auth_tab, text="Reset Password", width=20, command=self.reset_password_gui).pack(pady=20)
        
    def setup_profile_tab(self):
        # Clear any existing widgets in profile_tab
        for widget in self.profile_tab.winfo_children():
            widget.destroy()
        
        # Set up the profile tab
        tk.Button(self.profile_tab, text="Edit Profile", width=20, command=self.edit_profile_gui).pack(pady=10)
        tk.Button(self.profile_tab, text="Delete Account", width=20, command=self.delete_account_gui).pack(pady=10)
        tk.Button(self.profile_tab, text="Set Notifications", width=20, command=self.set_notifications_gui).pack(pady=10)
        tk.Button(self.profile_tab, text="View Watchlist", width=20, command=self.view_watchlist_gui).pack(pady=10)  # 3.2 Watchlist
        tk.Button(self.profile_tab, text="Sign Out", width=20, command=self.sign_out_user_gui).pack(pady=10)

    def setup_recommendations_tab(self):
        # Clear any existing widgets in recommendations_tab
        for widget in self.recommendations_tab.winfo_children():
            widget.destroy()
        
        # Set up the recommendations tab
        location_frame = tk.Frame(self.recommendations_tab)
        location_frame.pack(pady=10)
        
        tk.Label(location_frame, text="Location:").grid(row=0, column=0, padx=5, pady=5)
        self.location_entry = tk.Entry(location_frame, width=25)
        self.location_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(location_frame, text="Set Location", command=self.set_location).grid(row=0, column=2, padx=5, pady=5)
        tk.Button(location_frame, text="Detect Location", command=self.detect_location).grid(row=0, column=3, padx=5, pady=5)
        
        self.weather_label = tk.Label(self.recommendations_tab, text="Weather: ", font=("Arial", 12))
        self.weather_label.pack(pady=10)
        
        self.weather_icon_label = tk.Label(self.recommendations_tab)
        self.weather_icon_label.pack(pady=10)
        
        decade_frame = tk.Frame(self.recommendations_tab)
        decade_frame.pack(pady=10)
        
        tk.Label(decade_frame, text="Select Decade:").grid(row=0, column=0, padx=5, pady=5)
        self.decade_var = tk.IntVar(value=1990)
        ttk.Combobox(decade_frame, textvariable=self.decade_var, values=[1970, 1980, 1990, 2000, 2010, 2020]).grid(row=0, column=1, padx=5, pady=5)
        
        # Filters Frame
        filters_frame = tk.Frame(self.recommendations_tab)
        filters_frame.pack(pady=10)
        
        tk.Label(filters_frame, text="Filter by Genre:").grid(row=0, column=0, padx=5, pady=5)
        self.filter_genre_var = tk.StringVar()
        self.filter_genre_entry = tk.Entry(filters_frame, textvariable=self.filter_genre_var, width=15)
        self.filter_genre_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Removed Filter by Language
        
        tk.Label(filters_frame, text="Filter by Year:").grid(row=0, column=2, padx=5, pady=5)
        self.filter_year_var = tk.StringVar()
        self.filter_year_entry = tk.Entry(filters_frame, textvariable=self.filter_year_var, width=10)
        self.filter_year_entry.grid(row=0, column=3, padx=5, pady=5)
        
        buttons_frame = tk.Frame(self.recommendations_tab)
        buttons_frame.pack(pady=10)
        
        tk.Button(buttons_frame, text="Refresh Weather", width=15, command=self.refresh_weather).grid(row=0, column=0, padx=10, pady=5)
        tk.Button(buttons_frame, text="Get Recommendations", width=20, command=self.get_recommendations).grid(row=0, column=1, padx=10, pady=5)
        
        # Recommendations List
        self.recommendations_listbox = tk.Listbox(self.recommendations_tab, width=80, selectmode=tk.SINGLE)
        self.recommendations_listbox.pack(pady=10)
        self.recommendations_listbox.bind('<Double-1>', self.view_movie_details_gui)  # 3.6 View Details
        
        # Save to Watchlist Button
        tk.Button(self.recommendations_tab, text="Save to Watchlist", width=20, command=self.save_to_watchlist).pack(pady=5)
        
        # Rate Movie Button
        tk.Button(self.recommendations_tab, text="Rate Movie", width=20, command=self.rate_movie_gui).pack(pady=5)
        
    def setup_watchlist_tab(self):
        # Clear any existing widgets in watchlist_tab
        for widget in self.watchlist_tab.winfo_children():
            widget.destroy()
        
        # Set up the watchlist tab
        self.watchlist_listbox = tk.Listbox(self.watchlist_tab, width=80, selectmode=tk.SINGLE)
        self.watchlist_listbox.pack(pady=10)
        self.watchlist_listbox.bind('<Double-1>', self.view_movie_details_gui)  # 3.6 View Details
        
        # Remove from Watchlist Button
        tk.Button(self.watchlist_tab, text="Remove from Watchlist", width=25, command=self.remove_from_watchlist).pack(pady=5)

    def setup_search_tab(self):
        # Clear any existing widgets in search_tab
        for widget in self.search_tab.winfo_children():
            widget.destroy()
        
        # Set up the search tab
        search_frame = tk.Frame(self.search_tab)
        search_frame.pack(pady=10)
        
        tk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=5, pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(search_frame, text="Search", command=self.search_movies_gui).grid(row=0, column=2, padx=5, pady=5)
        
        # Search Results Listbox
        self.search_results_listbox = tk.Listbox(self.search_tab, width=80, selectmode=tk.SINGLE)
        self.search_results_listbox.pack(pady=10)
        self.search_results_listbox.bind('<Double-1>', self.view_movie_details_gui)  # 3.6 View Details
        
        # Save to Watchlist Button
        tk.Button(self.search_tab, text="Save to Watchlist", width=20, command=self.save_search_to_watchlist).pack(pady=5)
        
        # Rate Movie Button
        tk.Button(self.search_tab, text="Rate Movie", width=20, command=self.rate_search_movie_gui).pack(pady=5)

    def register_user_gui(self):
        def register():
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            confirm_password = confirm_password_entry.get().strip()
            if not email or not password or not confirm_password:
                messagebox.showerror("Error", "All fields are required.")
                return
            if password != confirm_password:
                messagebox.showerror("Error", "Passwords do not match.")
                return
            if self.user_manager.register_user(email, password):
                messagebox.showinfo("Success", "User registered successfully.")
                register_window.destroy()
            else:
                messagebox.showerror("Error", "Email is already registered.")

        register_window = tk.Toplevel()
        register_window.title("Register")
        register_window.geometry("300x250")
        
        tk.Label(register_window, text="Email:").pack(pady=5)
        email_entry = tk.Entry(register_window, width=30)
        email_entry.pack(pady=5)
        
        tk.Label(register_window, text="Password:").pack(pady=5)
        password_entry = tk.Entry(register_window, show="*", width=30)
        password_entry.pack(pady=5)
        
        tk.Label(register_window, text="Confirm Password:").pack(pady=5)
        confirm_password_entry = tk.Entry(register_window, show="*", width=30)
        confirm_password_entry.pack(pady=5)
        
        tk.Button(register_window, text="Register", width=15, command=register).pack(pady=20)

    def sign_in_user_gui(self):
        def sign_in():
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            if not email or not password:
                messagebox.showerror("Error", "All fields are required.")
                return
            if self.user_manager.sign_in_user(email, password):
                messagebox.showinfo("Success", "Sign-in successful.")
                self.signed_in_email.set(email)
                sign_in_window.destroy()
                # After successful login, setup and add the extra tabs
                self.setup_profile_tab()
                self.setup_recommendations_tab()
                self.setup_watchlist_tab()   # 3.2 Watchlist Tab
                self.setup_search_tab()      # 3.5 Search Tab
                self.notebook.add(self.profile_tab, text="Profile")
                self.notebook.add(self.recommendations_tab, text="Movie Recommendations")
                self.notebook.add(self.watchlist_tab, text="Watchlist")   # 3.2 Watchlist
                self.notebook.add(self.search_tab, text="Search")         # 3.5 Search
                self.notebook.forget(self.auth_tab)
                # Optionally, switch to recommendations tab
                self.notebook.select(self.recommendations_tab)
            else:
                messagebox.showerror("Error", "Invalid email or password.")

        sign_in_window = tk.Toplevel()
        sign_in_window.title("Sign In")
        sign_in_window.geometry("300x200")
        
        tk.Label(sign_in_window, text="Email:").pack(pady=5)
        email_entry = tk.Entry(sign_in_window, width=30)
        email_entry.pack(pady=5)
        
        tk.Label(sign_in_window, text="Password:").pack(pady=5)
        password_entry = tk.Entry(sign_in_window, show="*", width=30)
        password_entry.pack(pady=5)
        
        tk.Button(sign_in_window, text="Sign In", width=15, command=sign_in).pack(pady=20)

    def sign_out_user_gui(self):
        self.signed_in_email.set("")
        messagebox.showinfo("Sign Out", "You have been signed out.")
        # Remove extra tabs
        self.notebook.forget(self.profile_tab)
        self.notebook.forget(self.recommendations_tab)
        self.notebook.forget(self.watchlist_tab)   # 3.2 Watchlist
        self.notebook.forget(self.search_tab)      # 3.5 Search
        # Add auth_tab back
        self.notebook.add(self.auth_tab, text="Authentication")
        # Switch back to auth_tab
        self.notebook.select(self.auth_tab)
        logging.info("User signed out.")

    def reset_password_gui(self):
        def reset():
            email = email_entry.get().strip()
            new_password = new_password_entry.get().strip()
            confirm_new_password = confirm_password_entry.get().strip()
            if not email or not new_password or not confirm_new_password:
                messagebox.showerror("Error", "All fields are required.")
                return
            if new_password != confirm_new_password:
                messagebox.showerror("Error", "Passwords do not match.")
                return
            if self.user_manager.reset_password(email, new_password):
                messagebox.showinfo("Success", "Password reset successful.")
                reset_window.destroy()
            else:
                messagebox.showerror("Error", "Email not found.")

        reset_window = tk.Toplevel()
        reset_window.title("Reset Password")
        reset_window.geometry("300x250")
        
        tk.Label(reset_window, text="Email:").pack(pady=5)
        email_entry = tk.Entry(reset_window, width=30)
        email_entry.pack(pady=5)
        
        tk.Label(reset_window, text="New Password:").pack(pady=5)
        new_password_entry = tk.Entry(reset_window, show="*", width=30)
        new_password_entry.pack(pady=5)
        
        tk.Label(reset_window, text="Confirm New Password:").pack(pady=5)
        confirm_password_entry = tk.Entry(reset_window, show="*", width=30)
        confirm_password_entry.pack(pady=5)
        
        tk.Button(reset_window, text="Reset Password", width=15, command=reset).pack(pady=20)

    def edit_profile_gui(self):
        def edit():
            email = self.signed_in_email.get()
            new_email = new_email_entry.get().strip()
            new_password = password_entry.get().strip()
            confirm_new_password = confirm_password_entry.get().strip()
            new_genres = genres_entry.get().strip()
            # 3.4 Genre Preferences
            new_genre_preferences = {}
            for condition in self.movie_recommender.cinemagoer.genre_preferences.keys():
                genre = genre_prefs_entries[condition].get().strip()
                if genre:
                    new_genre_preferences[condition] = [g.strip() for g in genre.split(',')]

            if new_password and new_password != confirm_new_password:
                messagebox.showerror("Error", "Passwords do not match.")
                return

            new_genres_list = [genre.strip() for genre in new_genres.split(',')] if new_genres else None

            # If new_email is provided, check if it's different from current and not taken
            if new_email and new_email != email:
                if self.user_manager.find_user(new_email):
                    messagebox.showerror("Error", "The new email is already taken.")
                    return

            success, msg = self.user_manager.edit_profile(
                email,
                new_email=new_email if new_email else None,
                new_password=new_password if new_password else None,
                new_genres=new_genres_list,
                new_genre_preferences=new_genre_preferences if new_genre_preferences else None
            )

            if success:
                messagebox.showinfo("Success", msg)
                # If email was changed, update signed_in_email
                if new_email and new_email != email:
                    self.signed_in_email.set(new_email)
                edit_window.destroy()
            else:
                messagebox.showerror("Error", msg)

        edit_window = tk.Toplevel()
        edit_window.title("Edit Profile")
        edit_window.geometry("400x600")
        
        tk.Label(edit_window, text="New Email:").pack(pady=5)
        new_email_entry = tk.Entry(edit_window, width=30)
        new_email_entry.pack(pady=5)
        
        tk.Label(edit_window, text="New Password:").pack(pady=5)
        password_entry = tk.Entry(edit_window, show="*", width=30)
        password_entry.pack(pady=5)
        
        tk.Label(edit_window, text="Confirm New Password:").pack(pady=5)
        confirm_password_entry = tk.Entry(edit_window, show="*", width=30)
        confirm_password_entry.pack(pady=5)
        
        tk.Label(edit_window, text="Preferred Genres (comma-separated):").pack(pady=5)
        genres_entry = tk.Entry(edit_window, width=30)
        genres_entry.pack(pady=5)
        
        # 3.4 Genre Preferences
        genre_prefs_frame = tk.LabelFrame(edit_window, text="Customize Genres per Weather Condition")
        genre_prefs_frame.pack(pady=10, padx=10, fill="both", expand="yes")
        
        genre_prefs_entries = {}
        user = self.user_manager.find_user(self.signed_in_email.get())
        for condition in self.movie_recommender.cinemagoer.genre_preferences.keys():
            frame = tk.Frame(genre_prefs_frame)
            frame.pack(pady=5, padx=5, fill="x")
            tk.Label(frame, text=f"{condition.capitalize()}:").pack(side=tk.LEFT, padx=5)
            entry = tk.Entry(frame, width=25)
            entry.pack(side=tk.LEFT, padx=5)
            # Pre-fill with existing preferences
            entry.insert(0, ', '.join(user.genre_preferences.get(condition, [])))
            genre_prefs_entries[condition] = entry
        
        tk.Button(edit_window, text="Update Profile", width=20, command=edit).pack(pady=20)

    def delete_account_gui(self):
        def delete():
            email = self.signed_in_email.get()
            confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete your account? This action cannot be undone.")
            if confirm:
                if self.user_manager.delete_account(email):
                    messagebox.showinfo("Success", "Account deleted successfully.")
                    self.signed_in_email.set("")
                    # Remove extra tabs
                    self.notebook.forget(self.profile_tab)
                    self.notebook.forget(self.recommendations_tab)
                    self.notebook.forget(self.watchlist_tab)   # 3.2 Watchlist
                    self.notebook.forget(self.search_tab)      # 3.5 Search
                    # Add auth_tab back
                    self.notebook.add(self.auth_tab, text="Authentication")
                    # Switch back to auth_tab
                    self.notebook.select(self.auth_tab)
                    delete_window.destroy()
                else:
                    messagebox.showerror("Error", "Failed to delete account.")

        delete_window = tk.Toplevel()
        delete_window.title("Delete Account")
        delete_window.geometry("300x150")
        
        tk.Label(delete_window, text="Are you sure you want to delete your account?", wraplength=250).pack(pady=20)
        tk.Button(delete_window, text="Delete Account", width=15, command=delete).pack(pady=10)

    def set_notifications_gui(self):
        def set_notifications():
            email = self.signed_in_email.get()
            notifications = notify_var.get()
            if self.user_manager.set_notifications(email, notifications):
                messagebox.showinfo("Success", "Notification preferences updated.")
                notify_window.destroy()
            else:
                messagebox.showerror("Error", "Failed to update notification preferences.")

        notify_window = tk.Toplevel()
        notify_window.title("Set Notifications")
        notify_window.geometry("350x150")
        
        notify_var = tk.BooleanVar()
        user = self.user_manager.find_user(self.signed_in_email.get())
        notify_var.set(user.notifications)
        tk.Checkbutton(notify_window, text="Receive notifications about new movie releases", variable=notify_var).pack(pady=20)
        
        tk.Button(notify_window, text="Update Preferences", width=20, command=set_notifications).pack(pady=10)

    def view_watchlist_gui(self):
        self.setup_watchlist_tab()
        self.notebook.select(self.watchlist_tab)
        self.refresh_watchlist()

    def refresh_watchlist(self):
        user = self.user_manager.find_user(self.signed_in_email.get())
        self.watchlist_listbox.delete(0, tk.END)
        for movie in user.watchlist:
            self.watchlist_listbox.insert(tk.END, movie)

    def save_to_watchlist(self):
        selected = self.recommendations_listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a movie to save.")
            return
        movie = self.recommendations_listbox.get(selected[0])
        if movie == "No movies found for the selected criteria.":
            messagebox.showerror("Error", "No valid movie selected.")
            return
        user = self.user_manager.find_user(self.signed_in_email.get())
        if movie not in user.watchlist:
            user.watchlist.append(movie)
            self.user_manager.save_users()
            messagebox.showinfo("Success", f"'{movie}' added to your watchlist.")
            self.refresh_watchlist()  # Refresh the watchlist after adding
        else:
            messagebox.showwarning("Warning", f"'{movie}' is already in your watchlist.")

    def remove_from_watchlist(self):
        selected = self.watchlist_listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a movie to remove.")
            return
        movie = self.watchlist_listbox.get(selected[0])
        user = self.user_manager.find_user(self.signed_in_email.get())
        if movie in user.watchlist:
            user.watchlist.remove(movie)
            self.user_manager.save_users()
            self.refresh_watchlist()
            messagebox.showinfo("Success", f"'{movie}' removed from your watchlist.")
        else:
            messagebox.showerror("Error", f"'{movie}' not found in your watchlist.")

    def rate_movie_gui(self):
        selected = self.recommendations_listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a movie to rate.")
            return
        movie = self.recommendations_listbox.get(selected[0])

        def rate():
            rating = rating_var.get()
            if rating not in ['1', '2', '3', '4', '5']:
                messagebox.showerror("Error", "Please enter a valid rating between 1 and 5.")
                return
            user = self.user_manager.find_user(self.signed_in_email.get())
            user.ratings[movie] = int(rating)
            self.user_manager.save_users()
            messagebox.showinfo("Success", f"Rated '{movie}' with {rating} stars.")
            rate_window.destroy()

        rate_window = tk.Toplevel()
        rate_window.title("Rate Movie")
        rate_window.geometry("300x150")
        
        tk.Label(rate_window, text=f"Rate '{movie}':").pack(pady=10)
        rating_var = tk.StringVar()
        rating_entry = tk.Entry(rate_window, textvariable=rating_var, width=10)
        rating_entry.pack(pady=5)
        tk.Label(rate_window, text="Enter a rating between 1 and 5").pack(pady=5)
        tk.Button(rate_window, text="Submit Rating", command=rate).pack(pady=10)

    def rate_search_movie_gui(self):
        selected = self.search_results_listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a movie to rate.")
            return
        movie = self.search_results_listbox.get(selected[0])
        if movie.startswith("No movies"):
            messagebox.showerror("Error", "No valid movie selected.")
            return

        def rate():
            rating = rating_var.get()
            if rating not in ['1', '2', '3', '4', '5']:
                messagebox.showerror("Error", "Please enter a valid rating between 1 and 5.")
                return
            user = self.user_manager.find_user(self.signed_in_email.get())
            user.ratings[movie] = int(rating)
            self.user_manager.save_users()
            messagebox.showinfo("Success", f"Rated '{movie}' with {rating} stars.")
            rate_window.destroy()

        rate_window = tk.Toplevel()
        rate_window.title("Rate Movie")
        rate_window.geometry("300x150")
        
        tk.Label(rate_window, text=f"Rate '{movie}':").pack(pady=10)
        rating_var = tk.StringVar()
        rating_entry = tk.Entry(rate_window, textvariable=rating_var, width=10)
        rating_entry.pack(pady=5)
        tk.Label(rate_window, text="Enter a rating between 1 and 5").pack(pady=5)
        tk.Button(rate_window, text="Submit Rating", command=rate).pack(pady=10)

    def set_location(self):
        location = self.location_entry.get().strip()
        if location:
            self.weather_service.location = location
            self.update_weather()
        else:
            messagebox.showerror("Error", "Please enter a valid location.")

    def detect_location(self):
        try:
            ipgeo_api_key = "8aebec29b3654308bc34de91bed9dbd0"  # Consider using environment variables
            response = requests.get(f"https://api.ipgeolocation.io/ipgeo?apiKey={ipgeo_api_key}")
            if response.status_code == 200:
                data = response.json()
                city = data.get("city")
                if city:
                    self.weather_service.location = city
                    self.location_entry.delete(0, tk.END)
                    self.location_entry.insert(0, city)
                    self.update_weather()
                else:
                    messagebox.showerror("Error", "Could not detect city from location data.")
            else:
                messagebox.showerror("Error", "Could not detect location. Try again.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error during location detection: {e}")
            messagebox.showerror("Error", f"Network error: {e}")

    def refresh_weather(self):
        if self.weather_service.location:
            self.update_weather()
        else:
            messagebox.showerror("Error", "Set a location before refreshing weather data.")

    def update_weather(self):
        weather_data = self.weather_service.fetch_weather_data(self.weather_service.location)
        weather = weather_data.get("weather", "Unknown")
        temperature = weather_data.get("temperature", "N/A")
        icon_code = weather_data.get("icon_code")

        self.weather_label.config(text=f"Weather: {weather}, Temp: {temperature}°C")

        if icon_code:
            icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
            try:
                response = requests.get(icon_url)
                response.raise_for_status()
                img_data = response.content
                img = Image.open(io.BytesIO(img_data))
                img = img.resize((100, 100))
                icon = ImageTk.PhotoImage(img)
                self.weather_icon_label.config(image=icon)
                self.weather_icon_label.image = icon
                logging.info(f"Weather icon updated for icon code: {icon_code}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Error loading weather icon: {e}")
        else:
            self.weather_icon_label.config(image='')
            self.weather_icon_label.image = None

    def get_recommendations(self):
        if not self.weather_service.location:
            messagebox.showerror("Error", "Set a location to get movie recommendations.")
            return
        weather_data = self.weather_service.fetch_weather_data(self.weather_service.location)
        weather = weather_data.get("weather", "Unknown")
        decade = self.decade_var.get()
        filters = {
            "genre": self.filter_genre_var.get().strip(),
            # Removed 'language' filter
            "year": self.filter_year_var.get().strip()
        }
        user = self.user_manager.find_user(self.signed_in_email.get())
        # 3.3 Use user ratings
        user_ratings = user.ratings if user else None
        recommendations = self.movie_recommender.recommend_movies(
            weather=weather,
            genre_preferences=user.genre_preferences,
            decade=decade,
            filters=filters,
            user_ratings=user_ratings
        )
        self.recommendations_listbox.delete(0, tk.END)
        for movie in recommendations:
            self.recommendations_listbox.insert(tk.END, movie)

    def search_movies_gui(self, event=None):
        query = self.search_var.get().strip().lower()
        if not query:
            messagebox.showerror("Error", "Please enter a search term.")
            return
        user = self.user_manager.find_user(self.signed_in_email.get())
        if not user:
            messagebox.showerror("Error", "User not found.")
            return
        # Search by title or genre
        results = self.movie_recommender.movies_data[
            self.movie_recommender.movies_data['clean_title'].str.lower().str.contains(query) |
            self.movie_recommender.movies_data['genres'].str.lower().str.contains(query)
        ]['title'].tolist()
        self.search_results_listbox.delete(0, tk.END)
        if results:
            for movie in results:
                self.search_results_listbox.insert(tk.END, movie)
        else:
            self.search_results_listbox.insert(tk.END, "No movies found matching the search criteria.")

    def save_search_to_watchlist(self):
        selected = self.search_results_listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a movie to save.")
            return
        movie = self.search_results_listbox.get(selected[0])
        if movie.startswith("No movies"):
            messagebox.showerror("Error", "No valid movie selected.")
            return
        user = self.user_manager.find_user(self.signed_in_email.get())
        if movie not in user.watchlist:
            user.watchlist.append(movie)
            self.user_manager.save_users()
            messagebox.showinfo("Success", f"'{movie}' added to your watchlist.")
            self.refresh_watchlist()  # Refresh the watchlist after adding
        else:
            messagebox.showwarning("Warning", f"'{movie}' is already in your watchlist.")

    def view_movie_details_gui(self, event):
        widget = event.widget
        selection = widget.curselection()
        if not selection:
            return
        movie = widget.get(selection[0])
        if movie.startswith("No movies"):
            return
        details = self.movie_recommender.get_movie_details(movie)
        if details:
            details_window = tk.Toplevel()
            details_window.title(f"Details of {movie}")
            details_window.geometry("600x700")
            
            tk.Label(details_window, text=details["Title"], font=("Arial", 16, "bold")).pack(pady=10)
            tk.Label(details_window, text=f"Year: {details['Year']}").pack(pady=5)
            tk.Label(details_window, text=f"Genre: {details['Genre']}").pack(pady=5)
            tk.Label(details_window, text=f"Language: {details['Language']}").pack(pady=5)
            tk.Label(details_window, text="Synopsis:", font=("Arial", 12, "bold")).pack(pady=5)
            synopsis_text = tk.Text(details_window, wrap=tk.WORD, height=10, width=70)
            synopsis_text.insert(tk.END, details["Plot"])
            synopsis_text.config(state=tk.DISABLED)
            synopsis_text.pack(pady=5)
            
            if details["Poster"]:
                try:
                    response = requests.get(details["Poster"])
                    response.raise_for_status()
                    img_data = response.content
                    img = Image.open(io.BytesIO(img_data))
                    img = img.resize((200, 300))
                    poster = ImageTk.PhotoImage(img)
                    poster_label = tk.Label(details_window, image=poster)
                    poster_label.image = poster
                    poster_label.pack(pady=10)
                except requests.exceptions.RequestException as e:
                    logging.error(f"Error loading poster for {movie}: {e}")
        else:
            messagebox.showerror("Error", f"Details not found for '{movie}'.")

    def run(self):
        self.window.mainloop()

def main():
    app = GUIApplication()
    app.run()

if __name__ == "__main__":
    main()
