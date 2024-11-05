def get_location():
    """Prompt the user to enter their location."""
    location = input("Enter your location (e.g., city name): ")
    return location

def fetch_weather_data(location):
    """Fetch weather data for the given location."""
    # Placeholder for weather data fetching logic
    print(f"Fetching weather data for {location}...")
    return {"weather": "sunny"}  # Example weather data

def recommend_movies(weather):
    """Recommend movies based on the weather."""
    # Placeholder for movie recommendation logic
    print(f"Recommending movies for {weather} weather...")
    return ["Movie 1", "Movie 2"]  # Example movie list

def hello():
    """Print a greeting."""
    print("hello")

import tkinter as tk
from tkinter import messagebox
import json

def edit_profile(email, auth_frame, post_sign_in_frame):
    """Edit user profile information."""
    # Load existing users
    with open('users.json', 'r') as file:
        users = json.load(file)

    # Find the user with the given email
    for user in users:
        if user['email'] == email:
            print("Editing profile for:", email)
            new_password = input("Enter your new password (leave blank to keep current): ").strip()
            if new_password:
                user['password'] = new_password

            new_genres = input("Enter your preferred movie genres (comma-separated): ").strip()
            if new_genres:
                user['genres'] = new_genres.split(',')

            with open('users.json', 'w') as file:
                json.dump(users, file)
            print("Profile updated successfully.")
            auth_frame.pack_forget()  # Hide the auth frame
            post_sign_in_frame.pack()  # Show the post-sign-in frame

    print("Email not found.")
    return False

def delete_account(email):
    """Delete user account."""
    # Load existing users
    with open('users.json', 'r') as file:
        users = json.load(file)

    # Remove the user with the given email
    users = [user for user in users if user['email'] != email]

    with open('users.json', 'w') as file:
        json.dump(users, file)

    print("Account deleted successfully.")
    return True

def set_notifications(email):
    """Set user preferences for receiving notifications."""
    # Load existing users
    with open('users.json', 'r') as file:
        users = json.load(file)

    # Find the user with the given email
    for user in users:
        if user['email'] == email:
            notify = input("Do you want to receive notifications about new movie releases? (yes/no): ").strip().lower()
            user['notifications'] = (notify == 'yes')

            with open('users.json', 'w') as file:
                json.dump(users, file)
            print("Notification preferences updated.")
            return True

    print("Email not found.")
    return False

def sign_in_user(email, password):
    """Sign in a user with the given email and password."""
    # Load existing users
    with open('users.json', 'r') as file:
        users = json.load(file)

    # Check if the email and password match any user
    for user in users:
        if user['email'] == email and user['password'] == password:
            print("Sign-in successful.")
            return True

    print("Invalid email or password.")
    return False

def reset_password(email, new_password):
    """Reset the password for the given email."""
    # Load existing users
    with open('users.json', 'r') as file:
        users = json.load(file)

    # Find the user with the given email
    for user in users:
        if user['email'] == email:
            user['password'] = new_password
            with open('users.json', 'w') as file:
                json.dump(users, file)
            print("Password reset successful.")
            return True

    print("Email not found.")
    return False
import os

def register_user(email, password):
    # Check if the users.json file exists, if not, create an empty list
    if not os.path.exists('users.json'):
        with open('users.json', 'w') as file:
            json.dump([], file)

    # Load existing users
    with open('users.json', 'r') as file:
        users = json.load(file)

    # Check if the email is already registered
    if any(user['email'] == email for user in users):
        print("Email is already registered.")
        return False

    # Add new user
    users.append({'email': email, 'password': password})

    # Save updated users list
    with open('users.json', 'w') as file:
        json.dump(users, file)

    print("User registered successfully.")
    return True

def create_main_window():
    window = tk.Tk()
    window.title("Weather-based Movie Recommendation System")
    window.geometry("400x300")
    return window

def register_user_gui(auth_frame, post_sign_in_frame):
    def register():
        email = email_entry.get().strip()
        password = password_entry.get().strip()
        if register_user(email, password):
            messagebox.showinfo("Success", "User registered successfully.")
            register_window.destroy()  # Close the register window
            auth_frame.pack()  # Show the auth frame
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

def sign_in_user_gui(auth_frame, post_sign_in_frame):
    sign_in_window = tk.Toplevel()
    sign_in_window.title("Sign In")

    def sign_in():
        email = email_entry.get().strip()
        password = password_entry.get().strip()
        if sign_in_user(email, password):
            messagebox.showinfo("Success", "Sign-in successful.")
            signed_in_email.set(email)
            sign_in_window.destroy()  # Close the sign-in window
            auth_frame.pack_forget()  # Hide the auth frame
            post_sign_in_frame.pack()  # Show the post-sign-in frame
        else:
            messagebox.showerror("Error", "Invalid email or password.")

    tk.Label(sign_in_window, text="Email:").pack()
    email_entry = tk.Entry(sign_in_window)
    email_entry.pack()

    tk.Label(sign_in_window, text="Password:").pack()
    password_entry = tk.Entry(sign_in_window, show="*")
    password_entry.pack()

    tk.Button(sign_in_window, text="Sign In", command=sign_in).pack()

def sign_out_user_gui(auth_frame, post_sign_in_frame):
    signed_in_email.set("")  # Clear the signed-in email
    messagebox.showinfo("Sign Out", "You have been signed out.")
    post_sign_in_frame.pack_forget()  # Hide the post-sign-in frame
    auth_frame.pack()  # Show the auth frame

def reset_password_gui():
    def reset():
        email = email_entry.get().strip()
        new_password = new_password_entry.get().strip()
        if reset_password(email, new_password):
            messagebox.showinfo("Success", "Password reset successful.")
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

def edit_profile_gui(auth_frame, post_sign_in_frame):
    def edit():
        email = signed_in_email.get()
        new_password = password_entry.get().strip()
        new_genres = genres_entry.get().strip()

        # Load existing users
        with open('users.json', 'r') as file:
            users = json.load(file)

        # Find the user with the given email
        for user in users:
            if user['email'] == email:
                if new_password:
                    user['password'] = new_password

                if new_genres:
                    user['genres'] = new_genres.split(',')

                with open('users.json', 'w') as file:
                    json.dump(users, file)
                messagebox.showinfo("Success", "Profile updated successfully.")
                return

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

def delete_account_gui(auth_frame, post_sign_in_frame):
    def delete():
        email = signed_in_email.get()
        if delete_account(email):
            messagebox.showinfo("Success", "Account deleted successfully.")
            signed_in_email.set("")  # Clear the signed-in email
            post_sign_in_frame.pack_forget()  # Hide the post-sign-in frame
            auth_frame.pack()  # Show the auth frame
        else:
            messagebox.showerror("Error", "Failed to delete account.")

    delete_window = tk.Toplevel()
    delete_window.title("Delete Account")

    tk.Label(delete_window, text="Are you sure you want to delete your account?").pack()
    tk.Button(delete_window, text="Delete Account", command=delete).pack()

def set_notifications_gui():
    def set_notifications():
        email = signed_in_email.get()
        notify = notify_var.get()
        if set_notifications(email):
            messagebox.showinfo("Success", "Notification preferences updated.")
        else:
            messagebox.showerror("Error", "Failed to update notification preferences.")

    notify_window = tk.Toplevel()
    notify_window.title("Set Notifications")

    notify_var = tk.BooleanVar()
    tk.Checkbutton(notify_window, text="Receive notifications about new movie releases", variable=notify_var).pack()

    tk.Button(notify_window, text="Update Preferences", command=set_notifications).pack()
    window = create_main_window()
    global signed_in_email, auth_frame, post_sign_in_frame
    signed_in_email = tk.StringVar()

    auth_frame = tk.Frame(window)
    auth_frame.pack()

    post_sign_in_frame = tk.Frame(window)

    tk.Button(auth_frame, text="Register", command=lambda: register_user_gui(auth_frame, post_sign_in_frame)).pack()
    tk.Button(auth_frame, text="Sign In", command=lambda: sign_in_user_gui(auth_frame, post_sign_in_frame)).pack()

    tk.Button(post_sign_in_frame, text="Sign Out", command=lambda: sign_out_user_gui(auth_frame, post_sign_in_frame)).pack()
    tk.Button(post_sign_in_frame, text="Edit Profile", command=lambda: edit_profile_gui(auth_frame, post_sign_in_frame)).pack()
    tk.Button(post_sign_in_frame, text="Delete Account", command=lambda: delete_account_gui(auth_frame, post_sign_in_frame)).pack()
    tk.Button(post_sign_in_frame, text="Set Notifications", command=set_notifications_gui).pack()

    window.mainloop()

def main_gui():
    window = create_main_window()
    global signed_in_email
    signed_in_email = tk.StringVar()

    # Frame for sign-in, register, and reset password options
    auth_frame = tk.Frame(window)
    auth_frame.pack()

    tk.Button(auth_frame, text="Register", command=lambda: register_user_gui(auth_frame, post_sign_in_frame)).pack()
    tk.Button(auth_frame, text="Sign In", command=lambda: sign_in_user_gui(auth_frame, post_sign_in_frame)).pack()

    tk.Button(auth_frame, text="Reset Password", command=reset_password_gui).pack()  # Moved here

    # Frame for post-sign-in options
    post_sign_in_frame = tk.Frame(window)

    tk.Button(post_sign_in_frame, text="Sign Out", command=lambda: sign_out_user_gui(auth_frame, post_sign_in_frame)).pack()
    tk.Button(post_sign_in_frame, text="Reset Password", command=reset_password_gui).pack()
    tk.Button(post_sign_in_frame, text="Edit Profile", command=lambda: edit_profile_gui(auth_frame, post_sign_in_frame)).pack()
    tk.Button(post_sign_in_frame, text="Delete Account", command=lambda: delete_account_gui(auth_frame, post_sign_in_frame)).pack()
    tk.Button(post_sign_in_frame, text="Set Notifications", command=set_notifications_gui).pack()

    window.mainloop()

def main():
    main_gui()

if __name__ == "__main__":
    main()
