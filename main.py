import os
import json
import tkinter as tk
from tkinter import messagebox

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
    def get_location(self):
        """Prompt the user to enter their location."""
        location = input("Enter your location (e.g., city name): ")
        return location

    def fetch_weather_data(self, location):
        """Fetch weather data for the given location."""
        # Placeholder for weather data fetching logic
        print(f"Fetching weather data for {location}...")
        return {"weather": "sunny"}  # Example weather data

class MovieRecommender:
    def recommend_movies(self, weather):
        """Recommend movies based on the weather."""
        # Placeholder for movie recommendation logic
        print(f"Recommending movies for {weather} weather...")
        return ["Movie 1", "Movie 2"]  # Example movie list

class GUIApplication:
    def __init__(self):
        self.window = self.create_main_window()
        self.signed_in_email = tk.StringVar()
        self.auth_frame = tk.Frame(self.window)
        self.auth_frame.pack()
        self.post_sign_in_frame = tk.Frame(self.window)
        self.user_manager = UserManager()
        self.weather_service = WeatherService()
        self.movie_recommender = MovieRecommender()

        self.setup_auth_frame()
        self.setup_post_sign_in_frame()

    def create_main_window(self):
        window = tk.Tk()
        window.title("Weather-based Movie Recommendation System")
        window.geometry("400x300")
        return window

    def setup_auth_frame(self):
        tk.Button(self.auth_frame, text="Register", command=self.register_user_gui).pack()
        tk.Button(self.auth_frame, text="Sign In", command=self.sign_in_user_gui).pack()
        tk.Button(self.auth_frame, text="Reset Password", command=self.reset_password_gui).pack()

    def setup_post_sign_in_frame(self):
        tk.Button(self.post_sign_in_frame, text="Sign Out", command=self.sign_out_user_gui).pack()
        tk.Button(self.post_sign_in_frame, text="Reset Password", command=self.reset_password_gui).pack()
        tk.Button(self.post_sign_in_frame, text="Edit Profile", command=self.edit_profile_gui).pack()
        tk.Button(self.post_sign_in_frame, text="Delete Account", command=self.delete_account_gui).pack()
        tk.Button(self.post_sign_in_frame, text="Set Notifications", command=self.set_notifications_gui).pack()
        tk.Button(self.post_sign_in_frame, text="Get Recommendations", command=self.get_recommendations_gui).pack()

    def register_user_gui(self):
        def register():
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            if self.user_manager.register_user(email, password):
                messagebox.showinfo("Success", "User registered successfully.")
                register_window.destroy()
                self.auth_frame.pack()
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
                self.auth_frame.pack_forget()
                self.post_sign_in_frame.pack()
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
        self.post_sign_in_frame.pack_forget()
        self.auth_frame.pack()

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
                self.post_sign_in_frame.pack_forget()
                self.auth_frame.pack()
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

    def get_recommendations_gui(self):
        def get_recommendations():
            location = location_entry.get().strip()
            weather_data = self.weather_service.fetch_weather_data(location)
            weather = weather_data.get("weather")
            movies = self.movie_recommender.recommend_movies(weather)
            recommendations = "\n".join(movies)
            messagebox.showinfo("Movie Recommendations", f"Based on the {weather} weather, we recommend:\n{recommendations}")
            recommendations_window.destroy()

        recommendations_window = tk.Toplevel()
        recommendations_window.title("Get Movie Recommendations")

        tk.Label(recommendations_window, text="Enter your location (e.g., city name):").pack()
        location_entry = tk.Entry(recommendations_window)
        location_entry.pack()

        tk.Button(recommendations_window, text="Get Recommendations", command=get_recommendations).pack()

    def run(self):
        self.window.mainloop()

def main():
    app = GUIApplication()
    app.run()

if __name__ == "__main__":
    main()
    
