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

class User:
    def __init__(self, email, password, genres=None, notifications=False):
        self.email = email
        self.password = password
        self.genres = genres if genres else []
        self.notifications = notifications

    def to_dict(self):
        return {
            'email': self.email,
            'password': self.password,
            'genres': self.genres,
            'notifications': self.notifications
        }

    @staticmethod
    def from_dict(data):
        return User(
            email=data['email'],
            password=data['password'],
            genres=data.get('genres', []),
            notifications=data.get('notifications', False)
        )

class UserManager:
    def __init__(self, filename='users.json'):
        self.filename = filename
        self.users = self.load_users()

    def load_users(self):
        if not os.path.exists(self.filename):
            return []
        with open(self.filename, 'r') as file:
            data = json.load(file)
            return [User.from_dict(user_data) for user_data in data]

    def save_users(self):
        with open(self.filename, 'w') as file:
            data = [user.to_dict() for user in self.users]
            json.dump(data, file)

    def register_user(self, email, password):
        if any(user.email == email for user in self.users):
            print("Email is already registered.")
            return False
        new_user = User(email, password)
        self.users.append(new_user)
        self.save_users()
        print("User registered successfully.")
        return True

    def sign_in_user(self, email, password):
        for user in self.users:
            if user.email == email and user.password == password:
                print("Sign-in successful.")
                return True
        print("Invalid email or password.")
        return False

    def find_user(self, email):
        for user in self.users:
            if user.email == email:
                return user
        return None

    def reset_password(self, email, new_password):
        user = self.find_user(email)
        if user:
            user.password = new_password
            self.save_users()
            print("Password reset successful.")
            return True
        print("Email not found.")
        return False

    def delete_account(self, email):
        user = self.find_user(email)
        if user:
            self.users.remove(user)
            self.save_users()
            print("Account deleted successfully.")
            return True
        print("Email not found.")
        return False

    def edit_profile(self, email, new_password=None, new_genres=None):
        user = self.find_user(email)
        if user:
            if new_password:
                user.password = new_password
            if new_genres is not None:
                user.genres = new_genres
            self.save_users()
            print("Profile updated successfully.")
            return True
        print("Email not found.")
        return False

    def set_notifications(self, email, notifications):
        user = self.find_user(email)
        if user:
            user.notifications = notifications
            self.save_users()
            print("Notification preferences updated.")
            return True
        print("Email not found.")
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
                return {
                    "weather": weather_description.capitalize(),
                    "temperature": temperature,
                    "icon_code": icon_code
                }
            else:
                return {"weather": "Unavailable", "temperature": "N/A", "icon_code": None}
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return {"weather": "Unavailable", "temperature": "N/A", "icon_code": None}

class MovieRecommender:
    def __init__(self, movies_file_path):
        self.movies_data = pd.read_csv(movies_file_path)
        self.movies_data['year'] = self.movies_data['title'].apply(self.extract_year)

    @staticmethod
    def extract_year(title):
        """Extract year from movie title."""
        match = re.search(r'\((\d{4})\)', title)
        if match:
            return int(match.group(1))
        return None

    def recommend_movies(self, weather, decade=None):
        """Recommend movies based on the weather and optionally filter by decade."""
        weather_genre_mapping = {
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

                if not filtered_movies.empty:
                    recommended_movies = filtered_movies.sample(n=min(5, len(filtered_movies)))['title'].tolist()
                    return recommended_movies

        return ["No movies found for the selected weather and decade."]

class GUIApplication:
    def __init__(self):
        # Create main window
        self.window = self.create_main_window()
        self.signed_in_email = tk.StringVar()
        self.user_manager = UserManager()
        # Initialize weather service and movie recommender
        self.weather_service = WeatherService(weather_api_key="9317738386fb8a28b8b117a760bfe9d0")
        self.movie_recommender = MovieRecommender(movies_file_path="C:/Users/Pasupuleti/Professional Seminar Pitts/Project/3/movies.csv")
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=1, fill="both")
        
        # Create tabs
        self.auth_tab = ttk.Frame(self.notebook)
        self.profile_tab = ttk.Frame(self.notebook)
        self.recommendations_tab = ttk.Frame(self.notebook)
        
        # Add auth_tab to notebook
        self.notebook.add(self.auth_tab, text="Authentication")
        
        # Setup the tabs
        self.setup_auth_tab()
        # Do not setup other tabs yet; they will be set up after login

    def create_main_window(self):
        window = tk.Tk()
        window.title("Weather-based Movie Recommendation System")
        window.geometry("500x600")
        return window

    def setup_auth_tab(self):
        # Set up the authentication tab
        tk.Button(self.auth_tab, text="Register", command=self.register_user_gui).pack(pady=5)
        tk.Button(self.auth_tab, text="Sign In", command=self.sign_in_user_gui).pack(pady=5)
        tk.Button(self.auth_tab, text="Reset Password", command=self.reset_password_gui).pack(pady=5)
        
    def setup_profile_tab(self):
        # Set up the profile tab
        tk.Button(self.profile_tab, text="Edit Profile", command=self.edit_profile_gui).pack(pady=5)
        tk.Button(self.profile_tab, text="Delete Account", command=self.delete_account_gui).pack(pady=5)
        tk.Button(self.profile_tab, text="Set Notifications", command=self.set_notifications_gui).pack(pady=5)
        tk.Button(self.profile_tab, text="Sign Out", command=self.sign_out_user_gui).pack(pady=5)

    def setup_recommendations_tab(self):
        # Set up the recommendations tab
        self.location_entry = tk.Entry(self.recommendations_tab, width=30)
        self.location_entry.pack(pady=5)
        tk.Button(self.recommendations_tab, text="Set Location", command=self.set_location).pack(pady=5)
        tk.Button(self.recommendations_tab, text="Detect Location", command=self.detect_location).pack(pady=5)

        self.weather_label = tk.Label(self.recommendations_tab, text="Weather: ", font=("Arial", 12))
        self.weather_label.pack(pady=5)

        self.weather_icon_label = tk.Label(self.recommendations_tab)
        self.weather_icon_label.pack(pady=5)

        self.decade_var = tk.IntVar(value=1990)
        tk.Label(self.recommendations_tab, text="Select Decade:").pack(pady=5)
        ttk.Combobox(self.recommendations_tab, textvariable=self.decade_var, values=[1970, 1980, 1990, 2000, 2010, 2020]).pack()

        tk.Button(self.recommendations_tab, text="Refresh Weather", command=self.refresh_weather).pack(pady=5)
        tk.Button(self.recommendations_tab, text="Get Recommendations", command=self.get_recommendations).pack(pady=5)

    def register_user_gui(self):
        def register():
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            if self.user_manager.register_user(email, password):
                messagebox.showinfo("Success", "User registered successfully.")
                register_window.destroy()
            else:
                messagebox.showerror("Error", "Email is already registered.")

        register_window = tk.Toplevel()
        register_window.title("Register")

        tk.Label(register_window, text="Email:").pack()
        email_entry = tk.Entry(register_window)
        email_entry.pack()

        tk.Label(register_window, text="Password:").pack()
        password_entry = tk.Entry(register_window, show="*")
        password_entry.pack()

        tk.Button(register_window, text="Register", command=register).pack()

    def sign_in_user_gui(self):
        def sign_in():
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            if self.user_manager.sign_in_user(email, password):
                messagebox.showinfo("Success", "Sign-in successful.")
                self.signed_in_email.set(email)
                sign_in_window.destroy()
                # After successful login, add the extra tabs and set them up
                self.setup_profile_tab()
                self.setup_recommendations_tab()
                self.notebook.add(self.profile_tab, text="Profile")
                self.notebook.add(self.recommendations_tab, text="Movie Recommendations")
                # Optionally, switch to recommendations tab
                self.notebook.select(self.recommendations_tab)
            else:
                messagebox.showerror("Error", "Invalid email or password.")

        sign_in_window = tk.Toplevel()
        sign_in_window.title("Sign In")

        tk.Label(sign_in_window, text="Email:").pack()
        email_entry = tk.Entry(sign_in_window)
        email_entry.pack()

        tk.Label(sign_in_window, text="Password:").pack()
        password_entry = tk.Entry(sign_in_window, show="*")
        password_entry.pack()

        tk.Button(sign_in_window, text="Sign In", command=sign_in).pack()

    def sign_out_user_gui(self):
        self.signed_in_email.set("")
        messagebox.showinfo("Sign Out", "You have been signed out.")
        # Remove extra tabs
        self.notebook.forget(self.profile_tab)
        self.notebook.forget(self.recommendations_tab)
        # Switch back to auth_tab
        self.notebook.select(self.auth_tab)

    def reset_password_gui(self):
        def reset():
            email = email_entry.get().strip()
            new_password = new_password_entry.get().strip()
            if self.user_manager.reset_password(email, new_password):
                messagebox.showinfo("Success", "Password reset successful.")
                reset_window.destroy()
            else:
                messagebox.showerror("Error", "Email not found.")

        reset_window = tk.Toplevel()
        reset_window.title("Reset Password")

        tk.Label(reset_window, text="Email:").pack()
        email_entry = tk.Entry(reset_window)
        email_entry.pack()

        tk.Label(reset_window, text="New Password:").pack()
        new_password_entry = tk.Entry(reset_window, show="*")
        new_password_entry.pack()

        tk.Button(reset_window, text="Reset Password", command=reset).pack()

    def edit_profile_gui(self):
        def edit():
            email = self.signed_in_email.get()
            new_password = password_entry.get().strip()
            new_genres = genres_entry.get().strip()

            new_genres_list = new_genres.split(',') if new_genres else None

            if self.user_manager.edit_profile(email, new_password if new_password else None, new_genres_list):
                messagebox.showinfo("Success", "Profile updated successfully.")
                edit_window.destroy()
            else:
                messagebox.showerror("Error", "Email not found.")

        edit_window = tk.Toplevel()
        edit_window.title("Edit Profile")

        tk.Label(edit_window, text="New Password:").pack()
        password_entry = tk.Entry(edit_window, show="*")
        password_entry.pack()

        tk.Label(edit_window, text="Preferred Genres (comma-separated):").pack()
        genres_entry = tk.Entry(edit_window)
        genres_entry.pack()

        tk.Button(edit_window, text="Update Profile", command=edit).pack()

    def delete_account_gui(self):
        def delete():
            email = self.signed_in_email.get()
            if self.user_manager.delete_account(email):
                messagebox.showinfo("Success", "Account deleted successfully.")
                self.signed_in_email.set("")
                # Remove extra tabs
                self.notebook.forget(self.profile_tab)
                self.notebook.forget(self.recommendations_tab)
                # Switch back to auth_tab
                self.notebook.select(self.auth_tab)
                delete_window.destroy()
            else:
                messagebox.showerror("Error", "Failed to delete account.")

        delete_window = tk.Toplevel()
        delete_window.title("Delete Account")

        tk.Label(delete_window, text="Are you sure you want to delete your account?").pack()
        tk.Button(delete_window, text="Delete Account", command=delete).pack()

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

        notify_var = tk.BooleanVar()
        tk.Checkbutton(notify_window, text="Receive notifications about new movie releases", variable=notify_var).pack()

        tk.Button(notify_window, text="Update Preferences", command=set_notifications).pack()

    def set_location(self):
        location = self.location_entry.get().strip()
        if location:
            self.weather_service.location = location
            self.update_weather()
        else:
            messagebox.showerror("Error", "Please enter a valid location.")

    def detect_location(self):
        try:
            ipgeo_api_key = "8aebec29b3654308bc34de91bed9dbd0"
            response = requests.get(f"https://api.ipgeolocation.io/ipgeo?apiKey={ipgeo_api_key}")
            if response.status_code == 200:
                data = response.json()
                self.weather_service.location = data["city"]
                self.location_entry.delete(0, tk.END)
                self.location_entry.insert(0, data["city"])
                self.update_weather()
            else:
                messagebox.showerror("Error", "Could not detect location. Try again.")
        except requests.exceptions.RequestException as e:
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
            except requests.exceptions.RequestException as e:
                print(f"Error loading icon: {e}")

    def get_recommendations(self):
        if not self.weather_service.location:
            messagebox.showerror("Error", "Set a location to get movie recommendations.")
            return
        weather_data = self.weather_service.fetch_weather_data(self.weather_service.location)
        weather = weather_data.get("weather", "Unknown")
        decade = self.decade_var.get()
        movies = self.movie_recommender.recommend_movies(weather, decade)
        recommendations = "\n".join(movies)
        messagebox.showinfo("Movie Recommendations", f"Movies for {weather} weather in the {decade}s:\n{recommendations}")

    def run(self):
        self.window.mainloop()

def main():
    app = GUIApplication()
    app.run()

if __name__ == "__main__":
    main()
