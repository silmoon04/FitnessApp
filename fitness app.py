# Standard library imports
import copy
import json
import logging
import math
import os
import random
import re
import threading
import uuid
from datetime import datetime, timedelta
from functools import partial

# Third-party imports
import bcrypt
import mysql.connector
from mysql.connector import pooling
import numpy as np
import requests
from scipy.interpolate import UnivariateSpline
from dotenv import load_dotenv

# LangChain imports
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage

# Kivy imports
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel, LabelBase
from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.garden.graph import SmoothLinePlot
from kivy.graphics import Color, Ellipse, RoundedRectangle, StencilPop, StencilPush, StencilUnUse, StencilUse
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

# KivyMD imports
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.behaviors.elevation import CommonElevationBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard, MDCardSwipe
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import TwoLineAvatarListItem, TwoLineListItem
from kivymd.uix.screen import MDScreen

# Local imports
import characters_width_dict
from exercises import exercises
from exercise_guide import exercise_technique

# Load environment variables
load_dotenv()

class LoadingScreen(Screen):
   def __init__(self, **kwargs):
       super(LoadingScreen, self).__init__(**kwargs)
       self.name = 'loading'
       self.add_widget(MDLabel(text='Loading...', halign='center'))
class UserManager:
    _instance = None

    @classmethod
    def create_user(cls):
        if cls._instance is None:
            user_id = str(uuid.uuid4())
            db_manager = DatabaseManager(db_config)
            db_manager.insert_user_id(user_id)
            cls._instance = User(user_id=user_id)
        return cls._instance

    @classmethod
    def get_user(cls, user_id):
        if cls._instance is None or cls._instance.user_id != user_id:
            db_manager = DatabaseManager(db_config)
            user_data = db_manager.get_user(user_id=user_id)
            if user_data:
                cls._instance.load_from_db(user_data)
            else:
                raise ValueError(f"No user found with id {user_id}")
        return cls._instance
class User:
    def __init__(self, user_id, email=None, gender=None, age=None, height=None, weight=None, experience_level=None, bodyfat=None, activity_level=None, goal=None, calories=None, equipment=None, training_style=None, training_frequency=None, prioritized_muscle_groups=None):
        self.user_id = user_id
        self.preferences = {}
        self.email = email
        self.gender = gender
        self.age = age
        self.height = height
        self.weight = weight
        self.experience_level = experience_level
        self.bodyfat = bodyfat
        self.activity_level = activity_level
        self.goal = goal
        self.calories = calories
        self.equipment = equipment
        self.training_style = training_style
        self.training_frequency = training_frequency
        self.prioritized_muscle_groups = prioritized_muscle_groups

    def load_from_db(self, user_data):
        if user_data is not None:
            self.email = user_data[2]
            self.gender = user_data[4]
            self.age = user_data[5]
            self.height = float(user_data[6])
            self.weight = float(user_data[7])
            self.experience_level = user_data[8]
            self.bodyfat = float(user_data[9])
            self.activity_level = user_data[10]
            self.goal = user_data[11]
            self.calories = user_data[12]
            self.equipment = user_data[13]
            self.training_style = user_data[14]
            self.training_frequency = user_data[15]
            self.prioritized_muscle_groups = user_data[17]
        else:
            print("No data found")

    def update_email(self, email):
        self.email = email
        self.save()

    def update_gender(self, gender):
        self.gender = gender

    def update_age(self, age):
        self.age = age

    def update_height(self, height):
        self.height = height

    def update_weight(self, weight):
        self.weight = weight

    def update_experience_level(self, experience_level):
        self.experience_level = experience_level

    def update_bodyfat(self, bodyfat):
        self.bodyfat = bodyfat

    def update_activity_level(self, activity_level):
        self.activity_level = activity_level

    def update_goal(self, goal):
        self.goal = goal

    def update_calories(self, calories):
        self.calories = calories

    def update_equipment(self, equipment):
        self.equipment = equipment

    def update_training_style(self, training_style):
        self.training_style = training_style

    def update_training_frequency(self, training_frequency):
        self.training_frequency = training_frequency

    def update_prioritized_muscle_groups(self, prioritized_muscle_groups):
        self.prioritized_muscle_groups = prioritized_muscle_groups
        self.save()

    def save(self):
        try:
            db_manager = DatabaseManager(db_config)
            db_manager.update_user_profile(self)
        except Exception as e:
            logging.error("Error saving user: {}".format(e))
            raise
class DatabaseManager:
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection_pool = pooling.MySQLConnectionPool(pool_name="mypool",
                                                           pool_size=2,
                                                           **self.db_config)

    def start_transaction(self):
        self.transaction_connection = self.connection_pool.get_connection()
        self.transaction_connection.start_transaction()

    def commit_transaction(self):
        if self.transaction_connection:
            self.transaction_connection.commit()
            self.transaction_connection.close()
            self.transaction_connection = None

    def rollback_transaction(self):
        if self.transaction_connection:
            self.transaction_connection.rollback()
            self.transaction_connection.close()
            self.transaction_connection = None

    def execute_query(self, query, params=(), commit=False, fetch=None):
        connection = self.connection_pool.get_connection()
        result = None
        cursor_created = False
        try:
            cursor = connection.cursor()
            cursor_created = True
            cursor.execute(query, params)
            if commit:
                connection.commit()
            if fetch == 'one':
                result = cursor.fetchone()
            elif fetch == 'all':
                result = cursor.fetchall()
            if query.lower().startswith('insert'):
                result = cursor.lastrowid
        except mysql.connector.Error as e:
            logging.error(f'Database error: {e}')
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            if cursor_created:
                self._drain_cursor(cursor)
                cursor.close()
            connection.close()
        return result

    @staticmethod
    def _drain_cursor(cursor):
        try:
            while cursor.nextset():
                pass
        except mysql.connector.Error as e:
            logging.error(f'Error draining cursor: {e}')
            
    # nutrition database methods -----------------------------------------------------------------------------------------
    def update_user_profile(self, user):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """UPDATE userdata SET gender = %s, age = %s, height = %s, weight = %s,
        experience_level = %s, bodyfat = %s, activity_level = %s, goal = %s, calories = %s, equipment = %s,
        training_style = %s, training_frequency = %s, prioritized_muscle_groups = %s, timestamp= %s WHERE id = %s;"""
        params = (user.gender, user.age, user.height, user.weight, user.experience_level,
                    user.bodyfat, user.activity_level, user.goal, user.calories, user.equipment, user.training_style,
                    user.training_frequency, user.prioritized_muscle_groups, timestamp, user.user_id)
        self.execute_query(query, params=params, commit=True)

    def insert_user(self, username, email, password, user_id):
        if isinstance(password, str):
            password = password.encode('utf-8')
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        query = "UPDATE userdata SET username = %s, email = %s, password = %s WHERE id = %s;"
        self.execute_query(query, params=(username, email, hashed_password, user_id), commit=True)

    def insert_user_id(self, user_id):
        query = "INSERT INTO userdata (id) VALUES (%s)"
        self.execute_query(query, params=(user_id,), commit=True)
        
    def get_user(self, user_id):
        query = "SELECT * FROM userdata WHERE id = %s;"
        return self.execute_query(query, params=(user_id,), fetch='one')

    def get_user_by_username(self, username):
        query = "SELECT id, username, password FROM userdata WHERE username = %s;"
        return self.execute_query(query, params=(username,), fetch='one')

    def update_exercise_plan(self, user_id, plan_data):
        query = "SELECT plan_id FROM exercise_plans WHERE user_id = %s;"
        existing_plan = self.execute_query(query, params=(user_id,), fetch='one')
        
        if existing_plan:
            update_parts = [f"{day} = %s" for day in plan_data.keys()]
            update_query = f"UPDATE exercise_plans SET {', '.join(update_parts)} WHERE user_id = %s;"
            params = tuple(plan_data.values()) + (user_id,)
        else:
            columns = ', '.join(plan_data.keys())
            placeholders = ', '.join(['%s'] * len(plan_data))
            insert_query = f"INSERT INTO exercise_plans (user_id, {columns}) VALUES (%s, {placeholders});"
            params = (user_id,) + tuple(plan_data.values())

        return self.execute_query(update_query if existing_plan else insert_query, params=params, commit=True)
    
    def insert_chat(self, user_id, message, sender):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = "INSERT INTO chats (user_id, message, timestamp, sender) VALUES (%s, %s, %s, %s);"
        self.execute_query(query, params=(user_id, message, timestamp, sender), commit=True)


    def get_chats_by_user_id(self, user_id):
        query = "SELECT * FROM chats WHERE user_id = %s ORDER BY timestamp DESC;"
        return self.execute_query(query, params=(user_id,), fetch='all')

    def delete_chat(self, chat_id):
        query = "DELETE FROM chats WHERE chat_id = %s;"
        self.execute_query(query, params=(chat_id,), commit=True)
   
    def insert_logged_foods(self, user_id, label, kcal, protein, carbs, fats, fiber, portion_size, selected_weight, unit_sequence, date):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query1 = """
        INSERT INTO food_items (user_id, label, kcal, protein, carbs, fats, fiber, portion_size, weight, unit, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        self.execute_query(query1, params=(user_id, label, kcal, protein, carbs, fats, fiber, portion_size, selected_weight, unit_sequence, timestamp), commit=True)

        query2 = """
        REPLACE INTO daily_totals (user_id, total_calories, total_protein, total_fats, total_carbs, date)
        SELECT user_id, SUM(kcal), SUM(protein), SUM(fats), SUM(carbs), DATE(timestamp)
        FROM food_items
        WHERE user_id = %s AND DATE(timestamp) = %s
        GROUP BY user_id, DATE(timestamp);
        """
        self.execute_query(query2, params=(user_id, date), commit=True)
        
        
    def get_food_items(self, user_id, date):
        query = """
        SELECT user_id, label, kcal, protein, carbs, fats, fiber, portion_size, weight, unit, timestamp
        FROM food_items
        WHERE user_id = %s AND DATE(timestamp) = %s;
        """
        return self.execute_query(query, params=(user_id, date), fetch='all')
        
        
    def get_daily_values(self, user_id, date):
        query = """
        SELECT daily_target, total_calories, total_protein, total_fats, total_carbs FROM daily_totals
        WHERE user_id = %s AND DATE(date) = %s;
        """
        print(query)
        print(user_id)
        print(date)
        return self.execute_query(query, params=(user_id, date), fetch='all')
    
    # workout database methods -----------------------------------------------------------------------------------------
    
    def create_workout_plan(self, user_id, plan_name):
        query = "INSERT INTO workout_plans (user_id, plan_name) VALUES (%s, %s);"
        return self.execute_query(query, params=(user_id, plan_name), commit=True)

    def add_workout_day(self, plan_id, day_number):
        query = "INSERT INTO workout_days (plan_id, day_number) VALUES (%s, %s);"
        return self.execute_query(query, params=(plan_id, day_number), commit=True)

    def add_exercise_to_day(self, day_id, exerciseid, sets, reps):
        query = "INSERT INTO day_exercises (day_id, exerciseid, sets, reps) VALUES (%s, %s, %s, %s);"
        return self.execute_query(query, params=(day_id, exerciseid, sets, reps), commit=True)

    def get_or_create_exercise(self, exercise_name):
        query = "SELECT exerciseid FROM exercises WHERE name = %s;"
        result = self.execute_query(query, params=(exercise_name,), fetch='one')
        
        if result:
            return result[0]
        else:
            insert_query = "INSERT INTO exercises (name) VALUES (%s);"
            return self.execute_query(insert_query, params=(exercise_name,), commit=True)
        
    def check_and_override_plan(self, user_id, plan_name):
        # Check if the plan already exists
        plan_id_query = "SELECT plan_id FROM workout_plans WHERE user_id = %s AND plan_name = %s;"
        plan_id = self.execute_query(plan_id_query, params=(user_id, plan_name), fetch='one')

        if plan_id:
            # If the plan exists, delete it and its associated days and exercises
            delete_exercises_query = """
            DELETE de FROM day_exercises de
            JOIN workout_days wd ON de.day_id = wd.day_id
            WHERE wd.plan_id = %s;
            """
            self.execute_query(delete_exercises_query, params=(plan_id[0],), commit=True)

            delete_days_query = "DELETE FROM workout_days WHERE plan_id = %s;"
            self.execute_query(delete_days_query, params=(plan_id[0],), commit=True)

            delete_plan_query = "DELETE FROM workout_plans WHERE plan_id = %s;"
            self.execute_query(delete_plan_query, params=(plan_id[0],), commit=True)
            
    def save_complete_workout_plan(self, user_id, plan_name, workout_plan):
        self.start_transaction()
        try:
            # Check if the plan already exists and override it if necessary
            self.check_and_override_plan(user_id, plan_name)

            # Create the new plan
            plan_id = self.create_workout_plan(user_id, plan_name)

            for day_number, exercises in workout_plan.items():
                day_id = self.add_workout_day(plan_id, day_number)

                for exercise in exercises:
                    exerciseid = self.get_or_create_exercise(exercise['name'])
                    self.add_exercise_to_day(day_id, exerciseid, exercise['sets'], exercise['reps'])

            self.commit_transaction()
        except Exception as e:
            self.rollback_transaction()
            raise e

    def retrieve_workout_plan(self, user_id, plan_name):
        workout_plan = {}
        plan_id = self.get_plan_id(user_id, plan_name)

        if plan_id:
            days_query = "SELECT day_id, day_number FROM workout_days WHERE plan_id = %s ORDER BY day_number;"
            days = self.execute_query(days_query, params=(plan_id,), fetch='all')

            for day_id, day_number in days:
                workout_plan[day_number] = self.get_exercises_for_day(day_id)

        return workout_plan

    def get_exercises_for_day(self, day_id):
        ex_query = """
        SELECT e.name, de.sets, de.reps
        FROM day_exercises de
        JOIN exercises e ON de.exerciseid = e.exerciseid
        WHERE de.day_id = %s;
        """
        exercises = self.execute_query(ex_query, params=(day_id,), fetch='all')
        return [{'name': name, 'sets': sets, 'reps': reps} for name, sets, reps in exercises]

    def get_plan_id(self, user_id, plan_name):
        query = "SELECT plan_id FROM workout_plans WHERE user_id = %s AND plan_name = %s;"
        result = self.execute_query(query, params=(user_id, plan_name), fetch='one')
        return result[0] if result else None
         
    def get_plan_names(self, user_id):
        query = "SELECT plan_name FROM workout_plans WHERE user_id = %s;"
        result = self.execute_query(query, params=(user_id,), fetch='all')
        return [row[0] for row in result] if result else None         
with open('db_config.json', 'r') as json_file:
    db_config = json.load(json_file)
host = db_config['host']
user = db_config['user']
password = db_config['password']
database = db_config['database']
db_manager = DatabaseManager(db_config)
class WindowManager(ScreenManager):
    def __init__(self, **kwargs):
        super(WindowManager, self).__init__(**kwargs)
        self.add_widget(LoadingScreen(name='loading'))
        self.add_widget(InitialPage(name='iniialpage'))
        self.current_selection= []
class InitialPage(Screen):
    def on_enter(self, *args):
        # When entering the initial page, create a new user
        user = UserManager.create_user()
        self.user_id = user.user_id
class SignupPage(Screen):
    # Initialize successful_signup to False
    successful_signup = False

    def signup(self):
        # Get user input from the signup form
        username = self.ids.signup_username.text
        email = self.ids.signup_email.text
        password = self.ids.signup_password.text

        # Validate the user input
        if not (username and email and password):
            self.ids.signup_error.text = "Please fill in all fields."
            self.signup_success = False
            return

        # Check if the username already exists in the database
        db_manager = DatabaseManager(db_config)
        if db_manager.get_user_by_username(username):
            self.ids.signup_error.text = "Username already exists."
            self.signup_success = False
            return

        # Validate the email address format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.ids.signup_error.text = "Please enter a valid email address."
            self.successful_signup = False
            return

        # Validate the password complexity
        password_validation_result = self.validate_password_complexity(password)
        if password_validation_result is not True:
            self.ids.signup_error.text = password_validation_result
            self.successful_signup = False
            return

        # Attempt to create the user in the database
        try:
            self.successful_signup = True
            db_manager = DatabaseManager(db_config)
            user_id = self.manager.get_screen('initialpage').user_id
            user = UserManager.get_user(user_id)
            user.update_email(email)
            db_manager.insert_user(username, email, password, user_id)
            toast("Signup successful.")
            self.ids.signup_error.text = ""
        except Exception as e:
            self.ids.signup_error.text = str(e)
    def validate_password_complexity(self, password):
        # Validate the complexity of the password
        if len(password) < 8:
            return "Password must be at least 8 characters long."
        if not re.search(r"[A-Z]", password):
            return "Password must contain at least one uppercase letter."
        if not re.search(r"[a-z]", password):
            return "Password must contain at least one lowercase letter."
        if not re.search(r"[0-9]", password):
            return "Password must contain at least one number."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return "Password must contain at least one special character."
        return True

    def on_pre_enter(self, *args):
        # Reset the form fields and error messages when the signup page is about to be entered
        self.ids.signup_username.text = ""
        self.ids.signup_email.text = ""
        self.ids.signup_password.text = ""
        self.ids.signup_error.text = ""

    def on_enter(self, *args):
        # Set the focus to the username field when the signup page is entered
        Clock.schedule_once(lambda dt: self.ids.signup_username.focus == True)
        
    def change_screen(self):
        # Attempt to signup the user and navigate to the selectgender screen if signup is successful
        self.signup()
        if self.successful_signup == True:
            self.manager.current = "dashboard"
class LoginPage(Screen):
    def on_pre_enter(self, *args):
        # Reset the error message when the login page is about to be entered
        self.ids.error.text = ''

    def login(self):
        # Get user input from the login form
        username = self.ids.username.text
        password = self.ids.password.text

        # Validate the user input
        if not (username and password):
            self.ids.error.text = 'Please enter both username and password'
            return

        # Attempt to login the user
        try:
            db_manager = DatabaseManager(db_config)
            user_data = db_manager.get_user_by_username(username)
            if user_data:
                user_id, username, hashed_password = user_data
                # Check if the entered password matches the stored password
                if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                    # Get the user's preferences from the database
                    UserManager.get_user(user_id)
                    # Navigate to the dashboard screen
                    self.manager.current = 'dashboard'  
                    self.ids.error.text = ''    
                    toast("Login successful!")
                else:
                    # Show an error message if the login failed
                    self.ids.error.text = 'Incorrect username or password'
                    # Clear the password field for security reasons
                    self.ids.password.text = ''
        except Exception as e:
            # Show an error message if the login process failed
            self.ids.error.text = 'Login failed. Please try again.'
            logging.error("Error during login: {}".format(e))
class SelectGender(Screen):
    def set_gender(self, gender):
        # Retrieve the user_id from the 'initialpage' screen, get the user object using this id,
        # and update the user's gender in the database.
        user_id = self.manager.get_screen('initialpage').user_id
        user = UserManager.get_user(user_id)
        user.update_gender(gender) 
class InputAge(Screen):
    def validate_age(self, age):
        # Validate the age input by the user. If the age is a digit and within the valid range (10 to 100),
        # update it in the database, clear the validation message, and navigate to the next screen.
        # If the age is not valid, display a validation message.
        if age.isdigit() and 10 <= int(age) <= 100:
            self.update_age(age)
            self.ids.validage.text = ""
            self.manager.current = "inputheightweight"
        else:
            self.ids.validage.text = "Please enter a valid age between 10 and 100"
    
    def update_age(self, age):
        # Convert the input age to float, retrieve the user_id from the 'initialpage' screen,
        # get the user object using this id, and update the user's age in the database.
        self.age = float(age)
        user_id = self.manager.get_screen('initialpage').user_id
        user = UserManager.get_user(user_id)
        user.update_age(age)
class InputHeightWeight(Screen): #this will be displayed after the InputAge screen, and it takes the User's Height and Weight as input
    invalidhw = False  # Indicates whether the height and weight values are invalid
    height = None
    weight = None
    height_unit = StringProperty('m')
    weight_unit = StringProperty('kg')

    # Method to toggle height unit between meters and feet
    def toggle_height_unit(self):
        self.height_unit = 'ft' if self.height_unit == 'm' else 'm'

    # Method to toggle weight unit between kilograms and pounds
    def toggle_weight_unit(self):
        self.weight_unit = 'lbs' if self.weight_unit == 'kg' else 'kg'


    def convert_feet_to_meters(self, feet, inches):
        # Convert feet and inches to meters
        return round(feet * 0.3048 + inches * 0.0254, 2)

    def convert_pounds_to_kilograms(self, pounds):
        # Convert pounds to kilograms
        return round(pounds * 0.45359237,2)

    def validate_height(self, height):
        # Validate the height
        if 0.50 <= height <= 2.50:
            return True
        self.ids.validhw.text = "Please enter a valid height."
        self.ids.validhw.font_size = 16
        return False

    def validate_weight(self, weight):
        # Validate the weight
        if 15 <= weight <= 250:
            return True
        self.ids.validhw.text = "Please enter a valid weight."
        self.ids.validhw.font_size = 16
        return False

    def output(self, height_str, weight_str):
        self.invalidhw = False  # Reset the invalid flag

        # Check if both height and weight are empty.
        if not height_str or not weight_str:
            self.ids.validhw.text = "Please enter all the values for height and weight."
            self.ids.validhw.font_size = 12
            self.invalidhw = True
            return

        # Parse height and weight
        try:
            if self.height_unit == 'ft':
                feet, inches = map(int, height_str.split('.'))
                height = self.convert_feet_to_meters(feet, inches)
            else:
                height = float(height_str)

            weight = float(weight_str)
            if self.weight_unit == 'lbs':
                weight = self.convert_pounds_to_kilograms(weight)

        except ValueError:
            self.ids.validhw.text = "Invalid format for height or weight."
            self.invalidhw = True
            return

        # Validate height and weight
        if not self.validate_height(height) or not self.validate_weight(weight):
            self.invalidhw = True
            return

        # If validation passes, update the database
        self.height = height
        self.weight = weight
        
        user_id = self.manager.get_screen('initialpage').user_id
        user = UserManager.get_user(user_id)
        user.update_height(height)
        user.update_weight(weight)

        # If no errors, move to the next screen
        if not self.invalidhw:
            self.manager.current = "experiencelevel"
class ExperienceLevel(Screen):
    # Class representing the screen for selecting user's experience level
    rounded_btn2 = ObjectProperty(None)
    experience = ""
    invalidexp = False  

    def border_on_click(self, *args):
        # Create a list of tuples, where each tuple contains the experience level and center_y value
        experiences_and_center_ys = [
            ("novice", 0.72),
            ("beginner", 0.611),
            ("intermediate", 0.502),
            ("advanced", 0.393),
            ("elite", 0.284),
        ]

        # Use the zip function to loop over the list and the arguments at the same time
        for pressed, (experience, center_y) in zip(args, experiences_and_center_ys):
            # If the button is pressed, set the experience and pos_hint
            if pressed:
                self.experience = experience
                self.ids.border.pos_hint = {"center_x": 0.498, "center_y": center_y}
                break

    def on_continue(self):
        # Method to handle the continue action.
        # If an experience level is selected, it is updated in the database.
        # If not, a validation message is displayed.
        if self.experience != "":
            user_id = self.manager.get_screen('initialpage').user_id
            user = UserManager.get_user(user_id)
            user.update_experience_level(self.experience)
            self.invalidexp = False
        else:
            self.ids.validexp.text="Please select an experience"
            self.invalidexp = True
class InputBodyfat(Screen):
    # Class representing the screen for inputting user's bodyfat percentage
    invalidbf = False  
    bodyfat = ""

    def validbodyfat(self, bodyfat):
        # Method to validate the bodyfat input by the user
        # If the input is empty, a validation message is displayed
        if bodyfat == "":
            self.ids.validbf.text = "Please enter your bodyfat percentage"
            self.invalidbf = True
            self.bodyfat = ""
        else: 
            # If the input is not empty, it is converted to float and checked if it's within the valid range (4 to 50)
            # If it's not within the range, a validation message is displayed
            # If it's within the range, the bodyfat percentage is updated in the database
            bodyfat = float(bodyfat)
            if bodyfat > 50 or bodyfat < 4:
                self.ids.validbf.text = "Please enter a valid bodyfat percentage"
                self.invalidbf = True
            else:
                self.ids.validbf.text = ""
                self.invalidbf = False
                self.bodyfat = bodyfat
                
                #update the bodyfat in the user class 
                user_id = self.manager.get_screen('initialpage').user_id
                user = UserManager.get_user(user_id)
                user.update_bodyfat(bodyfat)
class CalculateBodyFat(Screen):
    # Class representing the screen for calculating user's bodyfat percentage
    invalidneck= False
    invalidwaist= False
    invalidhip= False
    no_measurement= False
    bodyfat=float()
    
    def calculatebf(self, pressed):
        # Method to calculate the bodyfat percentage based on the user's measurements
        # Retrieve the user's details from the database or user input
        user_id = self.manager.get_screen('initialpage').user_id
        user = UserManager.get_user(user_id)
        gender= user.gender
        height= user.height
        weight= user.weight
        age= int(user.age)
        neck= self.ids.neck.text
        waist= self.ids.waist.text
        hip= self.ids.hip.text
        if gender == "female":
            # If the user is female, modify the layout of the input bodyfat screen to include hip measurement
            # ... layout modification code ...
            self.ids.neckcircumference.pos_hint = {"center_x": .452, "center_y": 0.855}
            self.ids.neckinputrectangle.pos_hint = {"center_x": 0.348, "center_y": 0.78}
            self.ids.neckunitrectangle.pos_hint = {"center_x": 0.81, "center_y": 0.78}
            self.ids.neckunit.pos_hint= {"center_x": 0.81, "center_y": 0.78}
            self.ids.neck.pos_hint= {"center_x": 0.348, "center_y": 0.78}
            self.ids.waistcircumference.pos_hint = {"center_x": .452, "center_y": 0.709}
            self.ids.waistinputrectangle.pos_hint = {"center_x": 0.348, "center_y": 0.634}
            self.ids.waistunitrectangle.pos_hint = {"center_x": 0.81, "center_y": 0.634}
            self.ids.waistunit.pos_hint= {"center_x": 0.81, "center_y": 0.634}
            self.ids.waist.pos_hint= {"center_x": 0.348, "center_y": 0.634}
            self.ids.hipcircumference.pos_hint = {"center_x": .43, "center_y": 0.563}
            self.ids.hipinputrectangle.pos_hint = {"center_x": 0.348, "center_y": 0.488}
            self.ids.hipunitrectangle.pos_hint = {"center_x": 0.81, "center_y": 0.488}
            self.ids.hipunit.pos_hint= {"center_x": 0.81, "center_y": 0.488}
            self.ids.hip.pos_hint= {"center_x": 0.348, "center_y": 0.488}
            self.ids.calculaterectangle.pos_hint = {"center_x": 0.498, "center_y": 0.379}
            self.ids.no_measurement.pos_hint = {"center_y" : 0.31, "center_x" : 0.365}
            self.ids.validnhw.pos_hint = {"center_x": 0.5, "center_y": 0.324}
            self.ids.calculate.pos_hint = {"center_x": 0.498, "center_y": 0.379}
            self.ids.bf_rectangle.size_hint= .9,.1
            self.ids.bf_rectangle.pos_hint= {'center_x': 0.498,'center_y': 0.268}
            self.ids.estimate_text.pos_hint= {'center_x': 0.498,'center_y': 0.298}

            # If no measurements are provided, calculate bodyfat using BMI and age, less accurate but still useful
            if self.no_measurement == True:
                pressed= False
                BMI= round(weight / (height * height), 1)
                bodyfat= round((1.20 * BMI) + (0.23 * age) - 5.4, 1)
                self.bodyfat= bodyfat
                
                #update the bodyfat in the user class
                user_id = self.manager.get_screen('initialpage').user_id
                user = UserManager.get_user(user_id)
                user.update_bodyfat(bodyfat)
            # If measurements are provided, calculate bodyfat using the US Navy method after the calculte button is pressed
            if pressed== True: 
                if neck == "" and waist == "" and hip == "":
                    self.ids.validnhw.text = "Please enter your neck, waist and hip circumference"
                    self.ids.validnhw.font_size = 10
                    self.invalidneck = True
                    self.invalidwaist = True
                    self.invalidhip = True
                    return
                # If only one or two measurements are provided, display a validation message
                elif neck == "" or waist == "" or hip == "":
                    self.ids.validnhw.text = "Please enter all the values for neck, waist and hip circumference"
                    self.ids.validnhw.font_size = 10
                    self.invalidneck = True
                    self.invalidwaist = True
                    self.invalidhip = True
                    return
                else:
                    # If all measurements are provided, convert them to float and check if they are within the valid range
                    neck = float(neck)
                    waist = float(waist)
                    hip = float(hip)
                    if self.ids.neckunit.text == "in":
                        neck = round(neck * 2.54, 2)
                    if self.ids.waistunit.text == "in":
                        waist = round(waist * 2.54, 2)
                    if self.ids.hipunit.text == "in":
                        hip = round(hip * 2.54, 2)
                    
                    # Display a validation message if any of the measurements are not within the valid range
                    if neck < 20 or neck > 60:
                        self.ids.validnhw.text = "Please enter a valid neck circumference"
                        self.ids.validnhw.font_size = 10
                        self.invalidneck = True
                        return
                    if waist < 50 or waist > 150:
                        self.ids.validnhw.text = "Please enter a valid waist circumference"
                        self.ids.validnhw.font_size = 10
                        self.invalidwaist = True
                        return
                    if hip < 50 or hip > 150:
                        self.ids.validnhw.text = "Please enter a valid hip circumference"
                        self.ids.validnhw.font_size = 10
                        self.invalidhip = True
                        return
                    else:
                        self.invalidneck = False
                        self.invalidwaist = False
                        self.invalidhip = False
                        self.ids.validnhw.text = ""
                        # If all measurements are valid, display the bodyfat percentage and update it in the database
                        if self.invalidneck == False and self.invalidwaist == False and self.invalidhip == False:
                            self.ids.bf_rectangle.opacity= 1
                            self.ids.estimate_text.opacity= 1
                            self.ids.no_measurement.pos_hint = {"center_y" : 2, "center_x" : 0.365}
                            self.ids.estimate_text.font_size= 14
                            self.ids.bf_continue.pos_hint= {'center_x': 0.498,'center_y': 0.16}
                            self.ids.bf_continue_text.pos_hint= {'center_x': 0.498,'center_y': 0.16}
                            self.ids.bf_continue_text.opacity= 1
                            
                        # Calculate bodyfat percentage using the US Navy Body Fat Formula
                        bodyfat= round(495 / (1.29579 - 0.35004 * math.log10(waist + hip - neck) + 0.22100 * math.log10(height*100)) - 450, 1)
                        self.bodyfat= bodyfat
                        self.ids.bodyfat_percent.font_size= 45
                        self.ids.bodyfat_percent.pos_hint= {'center_x': 0.498,'center_y': 0.255}
                        self.ids.bodyfat_percent.text = f"{bodyfat}%"
                        
                        user_id = self.manager.get_screen('initialpage').user_id
                        user = UserManager.get_user(user_id)
                        user.update_bodyfat(bodyfat)
        else:
            # if the gender is male, modify the layout of the input bodyfat screen to exclude hip measurement
            if self.no_measurement == True:
                # If no measurements are provided, calculate bodyfat using BMI and age, less accurate but still useful, the formula is different for men and women
                BMI= round(weight / (height * height), 1)
                bodyfat= round((1.20 * BMI) + (0.23 * age) - 16.2, 1)
                self.bodyfat= bodyfat
                
                user_id = self.manager.get_screen('initialpage').user_id
                user = UserManager.get_user(user_id)
                user.update_bodyfat(bodyfat)
            
            # If measurements are provided, calculate bodyfat using the US Navy method after the calculte button is pressed
            if pressed== True:
                #validation for the measurements
                if neck == "" and waist == "":
                    self.ids.validnhw.text = "Please enter your neck and waist circumference"
                    self.ids.validnhw.font_size = 10
                    self.invalidneck = True
                    self.invalidwaist = True
                    return
                elif neck == "" or waist == "":
                    self.ids.validnhw.text = "Please enter all the values for neck and waist circumference"
                    self.ids.validnhw.font_size = 10
                    self.invalidneck = True
                    self.invalidwaist = True
                    return
                else:
                    # Convert the measurements to float and check if they are within the valid range
                    neck = float(neck)
                    waist = float(waist)
                    if self.ids.neckunit.text == "in":
                        neck = round(neck * 2.54, 2)
                    if self.ids.waistunit.text == "in":
                        waist = round(waist * 2.54, 2)
                    if neck < 20 or neck > 60:
                        self.ids.validnhw.text = "Please enter a valid neck circumference"
                        self.ids.validnhw.font_size = 10
                        self.invalidneck = True
                        return
                    if waist < 50 or waist > 150:
                        self.ids.validnhw.text = "Please enter a valid waist circumference"
                        self.ids.validnhw.font_size = 10
                        self.invalidwaist = True
                        return
                    else:
                        # If all measurements are valid, display the bodyfat percentage and update it in the database
                        self.invalidneck = False
                        self.invalidwaist = False
                        self.ids.validnhw.text = ""
                        if self.invalidneck == False and self.invalidwaist == False:
                            self.ids.bf_rectangle.opacity= 1
                            self.ids.no_measurement.pos_hint = {"center_y" : 2, "center_x" : 0.365}
                            self.ids.estimate_text.opacity= 1
                            self.ids.bf_continue.pos_hint= {'center_x': 0.498,'center_y': 0.14}
                            self.ids.bf_continue.opacity= 1
                            self.ids.bf_continue_text.opacity= 1
                            
                    # Calculate bodyfat percentage using the US Navy Body Fat Formula
                    bodyfat = round(495 / (1.0324 - 0.19077 * math.log10(waist - neck) + 0.15456 * math.log10(height*100)) - 450, 1)
                    self.ids.bodyfat_percent.text = f"{bodyfat}%"
                    self.bodyfat= bodyfat

                    user_id = self.manager.get_screen('initialpage').user_id
                    user = UserManager.get_user(user_id)
                    user.update_bodyfat(bodyfat)
class ActivityLevel(Screen):
    # Class representing the screen for selecting user's activity level
    activity = ""
    invalidact = False  

    def border_on_click(self, *args):
        # Create a list of tuples, where each tuple contains the activity level and center_y value
        activities_and_center_ys = [
            ("Sedentary", 0.7),
            ("Lightly Active, exercise 1-3 times/week", 0.6162),
            ("Moderately Active, exercise 4-5 times a week", 0.5324),
            ("Active, intense exercise 1-3 times a week or daily exercise", 0.4486),
            ("Very Active, intense exercise 6-7 times a week", 0.3648),
            ("Extra Active, very intense exercise daily, or physical job", 0.281),
        ]

        # Use the zip function to loop over the list and the arguments at the same time
        for pressed, (activity, center_y) in zip(args, activities_and_center_ys):
            # If the button is pressed, set the activity and pos_hint
            if pressed:
                self.activity = activity
                self.ids.border.pos_hint = {"center_x": 0.498, "center_y": center_y}
                break

    def on_continue(self):
        # Method to handle the continue action.
        # If an activity level is selected, it is updated in the database.
        # If not, a validation message is displayed.
        if self.activity != "":
            user_id = self.manager.get_screen('initialpage').user_id
            user = UserManager.get_user(user_id)
            user.update_activity_level(self.activity)
            self.manager.get_screen('inputgoal').set_recommendation()
            self.invalidact = False
            
        else:
            self.ids.validal.text="Please select an activity level"
            self.invalidact = True
class InputGoal(Screen):
    # Class representing the screen for inputting user's fitness goal
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user = None  # Initialize user as None

    def on_enter(self):
        # Method to handle the action when the screen is entered
        # It attempts to retrieve the user's details from the database and set the recommendation
        try:
            user_id = self.manager.get_screen('initialpage').user_id
            self.user = UserManager.get_user(user_id)
            self.set_recommendation()
        except AttributeError:
            pass
        except ValueError as e:
            # Handle the case where the user is not found in the UserManager
            print(e)

    
    goal = ""
    invalidgoal = False
    recommendation = ""
    recommendation_followed = False
    
    def border_on_click(self, pressed_loseweight, pressed_maintainweight, pressed_gainweight):
        # Method to handle the selection of fitness goal.
        # Depending on which button is pressed, the goal is set and the border position is updated.
        if pressed_loseweight:
            self.goal= "Lose Weight"
            self.ids.border.pos_hint = {"center_x": 0.498, "center_y": 0.662}
        elif pressed_maintainweight:
            self.goal= "Maintain Weight"
            self.ids.border.pos_hint = {"center_x": 0.498, "center_y": 0.537}
        elif pressed_gainweight:
            self.goal= "Gain Weight"
            self.ids.border.pos_hint = {"center_x": 0.498, "center_y": 0.412}

    def on_continue(self):
        # Method to handle the continue action.
        # If a goal is selected, it is updated in the database.
        # If not, a validation message is displayed.
        if self.goal == "":
            self.ids.validgoal.text = "Please select a goal"
            self.invalidgoal = True
        else:
            try:
                # Make sure user is initialized
                if self.user:
                    self.user.update_goal(self.goal)
                    self.invalidgoal = False
                    self.recommendation_followed = (self.goal[0] == self.recommendation[0])
                else:
                    raise ValueError("User instance is not initialized.")
            except ValueError as e:
                self.ids.validgoal.text = str(e)
                self.invalidgoal = True

    def set_recommendation(self):
        # Method to set the recommendation based on user's gender, body fat, and experience level.
        # If the user is not initialized, it does nothing.
        if not self.user:
            return

        gender = self.user.gender
        bodyfat = self.user.bodyfat
        experience = self.user.experience_level

        # Depending on the user's gender and body fat, the recommended action is determined.
        if (gender == "male" and bodyfat > 18) or (gender == "female" and bodyfat > 30):
            action = "Lose weight"
            rate = "0.25kg or 0.5kg per week" if experience in ["Beginner", "Novice"] else "0.5kg or 0.75kg per week"
        elif (gender == "male" and bodyfat < 14) or (gender == "female" and bodyfat < 20):
            action = "Gain weight"
            rate = "0.5kg or 0.75kg per week" if experience in ["Beginner", "Novice"] else "0.25kg per week"
        else:
            action = "Maintain weight"
            rate = ""

        # The recommendation is constructed and set for the UI.
        recommendation = f"{action}, {rate}" if rate else action
        self.recommendation = recommendation
        self.ids.recommendedgoal.text = f"{action} is recommended for you"

    def changescreen(self):
        # Method to handle the screen change action.
        # If a valid goal is selected, it navigates to the appropriate screen based on the goal.
        # If not, it stays on the current screen.
        if self.invalidgoal==False:
            if self.goal[0]== "M":
                self.manager.current= "displaycalories"
            else:
                self.manager.get_screen('weightlossorgainrate').recommendation()
                self.manager.get_screen('displaycalories').calories()
                self.manager.current= "weightlossorgainrate"
        else:
            self.manager.current= "inputgoal"         
class WeightLossOrGainRate(Screen):
    # Class representing the screen for inputting user's weight loss or gain rate
    invalidrate = False
    rate = "0"

    def border_on_click(self, *args):
        # Create a list of tuples, where each tuple contains the rate and center_y value
        rates_and_center_ys = [
            ("0.25", 0.662),
            ("0.5", 0.553),
            ("0.75", 0.444),
            ("1", 0.335),
        ]

        # Use the enumerate function to loop over the list and the arguments at the same time
        for pressed, (rate, center_y) in zip(args, rates_and_center_ys):
            # If the button is pressed, set the rate and pos_hint
            if pressed:
                self.rate = rate
                self.ids.border.pos_hint = {"center_x": 0.498, "center_y": center_y}
                break

    def on_continue(self):
        # Method to handle the continue action.
        # If a rate is selected, it is updated in the database.
        # If not, a validation message is displayed.
        if self.rate != "":
            self.invalidrate = False
        else:
            self.ids.validrate.text = "Please select an option"
            self.invalidrate = True

    def recommendation(self):
        # Method to handle the recommendation action.
        # It retrieves the recommendation from the 'inputgoal' screen and updates the UI accordingly.
        recommendation = self.manager.get_screen('inputgoal').recommendation
        followed = self.manager.get_screen('inputgoal').recommendation_followed
        goal = self.manager.get_screen('inputgoal').goal
        if goal[0] == "L":
            weight = "Losing"
        else:
            weight = "Gaining"
            self.ids.rate_of_loss_or_gain.text = "What rate of weight gain would you like to follow?"
        if followed == False:
            self.ids.recommendedrate.text = ""
            self.ids.continuebutton_rate.pos_hint = {"center_x": 0.498, "center_y": 0.225}
            self.ids.continue_rate.pos_hint = {"center_x": 0.498, "center_y": 0.225}
            self.ids.validrate.pos_hint = {"center_x": 0.498, "center_y": 0.165}
        else:
            self.ids.recommendedrate.text = f"{weight} {recommendation[11:]} is recommended for you"
            self.ids.recommendedrate.font_size = 12
class DisplayCalories(Screen):
    # Class representing the screen for displaying user's daily calorie intake

    def calories(self):
        # Method to calculate and display the user's daily calorie intake

        # Retrieve user details from the database and other screens
        user_id = self.manager.get_screen('initialpage').user_id
        user = UserManager.get_user(user_id)
        gender = user.gender
        height = user.height
        weight = user.weight
        age = int(user.age)
        activity = self.manager.get_screen('activitylevel').activity
        goal = self.manager.get_screen('inputgoal').goal
        rate = self.manager.get_screen('weightlossorgainrate').rate

        # Define the activity level multipliers
        multiplier = {"S": 1.2, "L": 1.375, "M": 1.55, "A": 1.65, "V": 1.75, "E": 1.95}

        # Calculate the Basal Metabolic Rate (BMR) based on the user's gender
        if gender == "male":
            BMR = round(10 * weight + 625 * height - 5 * age + 5, 0)
        else:
            BMR = round(10 * weight + 625 * height - 5 * age - 161, 0)

        # Calculate the maintenance calories based on the user's activity level
        maintenance = round(multiplier.get(activity[0]) * BMR, 0)

        # Calculate the daily calorie intake based on the user's goal
        if goal[0] == "M":
            calories = int(maintenance)
        elif goal[0] == "L":
            calories = int(maintenance - 1000 * float(rate))
        else:
            calories = int(maintenance + 1000 * float(rate))

        # Display the daily calorie intake on the screen
        print(calories)
        self.ids.calories.text = f"{calories}"

        # Update the user's daily calorie intake in the database
        user.update_calories(calories)
class InputEquipment(Screen):
    # Class representing the screen for inputting user's available equipment
    invalidequipment = False
    equipment = ""

    def border_on_click(self, pressed_minimalequipment, pressed_gym):
        # Method to handle the selection of available equipment.
        # Depending on which button is pressed, the equipment is set and the border position is updated.
        if pressed_minimalequipment:
            self.equipment = "Minimal Equipment, mainly calisthenics"
            self.ids.border.pos_hint = {"center_x": 0.498, "center_y": 0.63}
        elif pressed_gym:
            self.equipment = "Gym, mainly weights and machines"
            self.ids.border.pos_hint = {"center_x": 0.498, "center_y": 0.44}

    def on_continue(self):
        # Method to handle the continue action.
        # If an equipment option is selected, it is updated in the database.
        # If not, a validation message is displayed.
        if self.equipment != "":
            user_id = self.manager.get_screen('initialpage').user_id
            user = UserManager.get_user(user_id)
            user.update_equipment(self.equipment)
            self.invalidequipment = False
        else:
            self.ids.validequipment.text="Please select an option"
            self.invalidequipment = True

    def changescreen(self):
        # Method to handle the screen change action.
        # If a valid equipment option is selected, it navigates to the appropriate screen based on the equipment.
        # If not, it stays on the current screen.
        if self.invalidequipment==False:
            if self.equipment[0]== "G":
                self.manager.current= "signup_page"
            else:
                self.manager.current= "signup_page"
        else:
            self.manager.current= "inputequipment"
class Dashboard(Screen): 
    #this will be displayed after the InputTrainingDays screen, and it is the main screen that the User will see
    #this class provides methods to update the UI based on the user's progress and input, and to navigate to other screens.
    def __init__(self, **kwargs):
        super(Dashboard, self).__init__(**kwargs)
        self.exercise_completed = 3
        self.total_exercises = 6
        
        
    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.get_calories_from_database
        self.on_workout_to_log()
        
    def get_calories_from_database(self, dt):
        # get calories from database
        daily_totals= MDApp.get_running_app().root.get_screen('food_search').get_daily_calories()
        print(f"Daily totals: {daily_totals}")
        total_calories= daily_totals[0]
        total_protein = daily_totals[1]
        total_carbs = daily_totals[2]
        total_fats = daily_totals[3]
        calories_consumed= daily_totals[4]
        protein_consumed= daily_totals[5]
        carbs_consumed= daily_totals[6]
        fats_consumed= daily_totals[7]
        if total_calories:
            self.ids.calorie_circular_bar.value = round((calories_consumed/total_calories)*100)
            self.ids.protein_circular_bar.value = round((protein_consumed/total_protein)*100)
            self.ids.carbs_circular_bar.value = round((carbs_consumed/total_carbs)*100)
            self.ids.fats_circular_bar.value = round((fats_consumed/total_fats)*100)
            self.ids.calories_remaining.text = f"{round(total_calories - calories_consumed)}"
            self.ids.calories_target.text = f"{round(total_calories)}"
            self.ids.calories_consumed.text = f"{round(calories_consumed)}"
            self.ids.calorie_bar.value= round((calories_consumed/total_calories)*100)
            self.ids.protein_bar.value= round((protein_consumed/total_protein)*100)
            self.ids.carbs_bar.value= round((carbs_consumed/total_carbs)*100)
            self.ids.fats_bar.value= round((fats_consumed/total_fats)*100)
            
    def change_color(self, homepressed, nutritionpressed, chartpressed, profilepressed):
        # Create a dictionary that maps the ids to the buttons
        buttons = {
            'home': homepressed,
            'nutrition': nutritionpressed,
            'chart': chartpressed,
            'profile': profilepressed
        }

        # Loop over the dictionary
        for button_id, pressed in buttons.items():
            # If the button is pressed, set the color to white
            if pressed:
                self.ids[button_id].icon_color = 1, 1, 1, 1
            # If the button is not pressed, set the color to gray
            else:
                self.ids[button_id].icon_color = 146/255, 155/255, 157/255, 1
    
    def generate_button_clicked(self, clicked):
        if clicked == True:
            self.ids.generate_button.pos_hint= {"center_x": 0.5, "center_y": 2}
            self.ids.dashboard_image.pos_hint= {"center_x": 0.5, "center_y": 2}
            self.ids.box.pos_hint= {"center_x": 0.5, "center_y": 2} #TODO finish the logic here
            
    def on_workout_to_log(self):
        self.ids.big_text.text = "Start\nWorkout"
        #self.ids.big_text.font_size= 30
        #self.ids.big_text.padding = "25dp", 24, 0, 0
        self.ids.completed.text = f"" 
        #self.ids.workout_image.pos_hint = {"center_x": 2.5, "center_y": 0.5}
        #self.ids.completed.text = f"{self.exercise_completed}/{self.total_exercises} Completed" 
        #self.ids.workout_progress_bar.value = (self.exercise_completed/self.total_exercises)*100
        self.ids.workout_progress_bar.pos_hint = {"center_x": 2.5, "center_y": 0.5}
    
    def generate_plan(self, trainingfrequency= None,experiencelevel= None,prioritizemusclegroups= None):
        
        self.manager.current = "inputtrainingdays" 
class ExerciseList(Screen):
    # Class representing the screen for displaying a list of exercises
    search_delay = 0.3
    list_type = 'list'

    def __init__(self, **kwargs):
        # Initialize the screen and create a trigger for performing search with a delay
        super().__init__(**kwargs)
        self.search_trigger = Clock.create_trigger(self.perform_search, self.search_delay)
        self.item_clicked = False
        self.add_button_clicked = False
        self.selected_exercises = []
        self.guide= False
        self.pass_to_logworkout= False

    def on_kv_post(self, *args):
        # Populate the exercise list when entering the screen
        self.populate_exercises()
        self.on_list_type()

    def on_list_type(self, *args):
        # Adjust the UI based on the list type
        if self.list_type == 'list':
            self.ids.back_btn.text = 'Back'
            self.ids.add_exercises_layout.pos_hint = {'center_x': 2, 'center_y': 2}

    def populate_exercises(self, dt=None):        
        # Populate the exercise list with data from the 'exercises' dictionary
        self.ids.rv.data = [{
            'text': f"[size=20][font=Poppins-Bold.ttf][color=#FFFFFF]{exercise['name']}[/color][/font][/size]",
            'secondary_text': f"[size=15][font=Poppins-Regular.ttf][color=#FFFFFF]{exercise['type']}[/color][/font][/size]",
            'image_source': exercise['icon'],
            'is_checked': False,  # Add this line
        } for exercise in exercises]

    def perform_search(self, *args):
        # Perform a search in the exercise list based on the query from the search field
        query = self.ids.search_field.text
        filtered_exercises = [{
            'image_source': exercise['icon'],
            'text': f"[size=20][font=Poppins-Bold.ttf][color=#FFFFFF]{exercise['name']}[/color][/font][/size]",
            'secondary_text': f"[size=15][font=Poppins-Regular.ttf][color=#FFFFFF]{exercise['type']}[/color][/font][/size]",
            'is_checked': False,  # Add this line
        } for exercise in exercises if query.lower() in exercise['name'].lower()]
        self.ids.rv.data = filtered_exercises

    def search_query(self, query):
        # Reset the countdown for the search trigger and adjust the opacity of the search label based on whether the search field is empty
        if self.ids.search_field.text:
            self.search_trigger.cancel()
            self.ids.search_label.opacity=0
        else :
            self.ids.search_label.opacity=.3
        self.search_trigger.cancel()
        self.search_trigger()

    def on_back_btn(self):
        # Reset the UI to the initial state when the back button is clicked
        self.item_clicked = False
        self.ids.exercise_label.text = "Exercises"
        self.ids.exercise_guide_box.pos_hint = {'center_x': 2, 'center_y': 0.45}
        self.ids.rvcard.pos_hint = {'center_x': .5, 'center_y': 0.5}
        self.ids.search_btn.pos_hint= {'center_x': 0.5, 'center_y': 0.8}
        self.ids.search_box.pos_hint= {'center_x': 0.54, 'center_y': 0.803}
        self.ids.search_field.pos_hint= {'center_x': 0.5, 'center_y': 0.8}
        self.ids.exercise_count.pos_hint= {"center_x": 0.18, "top": .745}

    def show_exercise_guide(self, selected_exercise): 
        # Display the exercise guide when the user clicks on the name of an exercise in the log workout screen
        self.list_type = 'list'
        self.on_list_type()
        self.on_item_click(selected_exercise)
        self.guide= True

    def on_item_click(self, clicked_exercise):
        # Update the UI to show the exercise guide when an exercise is clicked
        self.item_clicked= True
        self.ids.exercise_label.text = clicked_exercise
        self.ids.exercise_guide_text.text = exercise_technique[clicked_exercise]
        self.ids.exercise_guide_box.pos_hint = {'center_x': 0.5, 'center_y': 0.45}
        self.ids.rvcard.pos_hint = {'center_x': 2, 'center_y': 0.5}
        self.ids.search_btn.pos_hint = {'center_x': 0.5, 'center_y': 2}
        self.ids.search_box.pos_hint = {'center_x': 0.54, 'center_y': 2}
        self.ids.search_field.pos_hint = {'center_x': 0.5, 'center_y': 2}
        self.ids.exercise_count.pos_hint = {"center_x": 0.18, "top": 2}

    def empty_list(self):
        # Uncheck all the exercises in the list
        for instance in ExerciseItemPlan.instances:
            if isinstance(instance, ExerciseItemPlan):  # Check if the instance is of the ExercisePlanItem class
                instance.empty_plan = True
                instance.on_checkbox_active(instance, value=False)

    def on_checkbox_clicked(self, added_exercises):
        # Update the selected exercises and the add exercises button text when a checkbox is clicked
        self.selected_exercises = added_exercises
        self.ids.add_exercises_btn.text = f"Add ({len(self.selected_exercises)})"

    def on_exit_screen(self):
        # Uncheck all the exercises and clear the selected exercises when exiting the screen
        for item in MDApp.get_running_app().root.get_screen('exercise_list').ids.rv.data:
            item['is_checked'] = False
        for instance in ExerciseItemPlan.instances:
            instance.uncheck()
        self.empty_list()
        self.selected_exercises = []   
        self.on_checkbox_clicked(added_exercises= [])

    def pass_exercises_to_logworkout(self):
        # Pass the selected exercises to the log workout screen
        if self.pass_to_logworkout:
            log_workout_screen = MDApp.get_running_app().root.get_screen('logworkout')
            log_workout_screen.add_exercise(self.selected_exercises)
            self.manager.current = "logworkout"
            self.pass_to_logworkout = False
            self.on_exit_screen() 
        else:
            self.pass_to_logworkout = True

    def on_button_clicked(self):
        # Pass the selected exercises to the log workout screen or the empty plan screen when the button is clicked
        if self.pass_to_logworkout:
            self.pass_exercises_to_logworkout()
            return
        empty_plan_screen= MDApp.get_running_app().root.get_screen('empty_plan')
        empty_plan_screen.added_exercises_to_plan(self.selected_exercises)
        self.manager.current = "empty_plan"
        self.on_exit_screen() 

    def change_screen(self):
        # Change the screen based on the current state
        if self.item_clicked:
            self.on_back_btn()
            if self.guide:
                self.manager.current = "logworkout"
        elif self.list_type == 'list':
            self.manager.current = "dashboard"
        else:
            self.manager.current= "empty_plan"
            self.on_exit_screen()   
class FoodSearch(Screen):
    # Class representing the screen for displaying a list of food items
    search_delay = 0.3

    def __init__(self, **kwargs):
        # Initialize the screen and create a trigger for performing search with a delay
        super().__init__(**kwargs)
        self.current_unpacked_data = {}  # Stores the current unpacked data from the food database
        self.logged_foodlist=[]  # List of food items that have been logged by the user
        self.search_trigger = Clock.create_trigger(self.perform_search, self.search_delay)  # Trigger for performing search with a delay
        self.serving = 1  # Default serving size
        self.editing_index = None  # Index of the food item being edited, if any
        self.total_calories = 0  # Total calories consumed by the user
        self.total_protein = 0  # Total protein consumed by the user
        self.total_fats = 0  # Total fats consumed by the user
        self.total_carbs = 0  # Total carbs consumed by the user
        self.saved_unit_sequence = None  # Saved unit sequence for the food item
        self.unit_to_sequence = {  # Mapping of units to sequences
            'serving': (True, False, False, False, False, False),
            'oz': (False, True, False, False, False, False),
            'g': (False, False, True, False, False, False),
            'hg': (False, False, False, True, False, False),
            'lb': (False, False, False, False, True, False),
            'cup': (False, False, False, False, False, True),
        }

    def on_kv_post(self, base_widget):
        # Method called after the kv file has been loaded
        super().on_kv_post(base_widget)
        self.rebuild_food_list()  # Rebuild the food list
        self.get_daily_calories()  # Get the daily calories consumed by the user
        
    def get_daily_calories(self):
        # Method to get the daily calories consumed by the user
        try:
            user_id = self.manager.get_screen('initialpage').user_id
        except AttributeError:
            user_id= '262efaa4-1a2d-484e-8de8-32966c8a6a82'
        result = db_manager.get_daily_values(user_id, datetime.now().strftime("%Y-%m-%d"))
        print(result)
        try:
            daily_target = result[0][0]
            if daily_target is None:
                daily_target = '2000, 150, 200, 50'  # Default value
            daily_target = daily_target.split(', ')
            print(daily_target)
            self.daily_calories = int(daily_target[0])
            self.daily_protein = int(daily_target[1])
            self.daily_carbs = int(daily_target[2])
            self.daily_fats = int(daily_target[3])
            self.total_calories = result[0][1]
            self.total_protein = result[0][2]
            self.total_fats = result[0][3]
            self.total_carbs = result[0][4]
        except (IndexError, ValueError, AttributeError):
            # Handle the case when the result is empty or invalid
            self.daily_calories = 2800
            self.daily_protein = 150
            self.daily_carbs = 180
            self.daily_fats = 100
            self.total_calories = 0
            self.total_protein = 76
            self.total_fats = 53
            self.total_carbs = 14

        self.ids.calories_consumed.text = f"{self.total_calories}/{self.daily_calories}"
        #TODO add gui changes to calories when you enter the app

        return self.daily_calories, self.daily_protein, self.daily_carbs, self.daily_fats, self.total_calories, self.total_protein, self.total_carbs, self.total_fats
        
    def calculate_nutrients(self, food_data,):
        # This function calculates the nutrients for a given food item based on its portion size.
        # It takes a dictionary of food data as input, which includes the portion size and the original macros.
        # It returns a dictionary with the calculated values for kcal, protein, carbs, and fats.
        portion_factor = round(float(food_data['portion_size']) * food_data.get('selected_weight', 100) / 100, 2)
        return {
            'kcal': round((food_data['original_macros']['calories'])*portion_factor),
            'protein': round((food_data['original_macros']['protein'])*portion_factor),
            'carbs': round((food_data['original_macros']['carbs'])*portion_factor),
            'fats': round((food_data['original_macros']['fats'])*portion_factor)
        }

    def create_food_text(self, food, nutrients):
        # This function creates the text to be displayed for a food item in the list.
        # It takes a dictionary of food data and a dictionary of nutrients as input.
        # It returns a dictionary with the text and secondary text to be displayed, along with the original food data.
        food_text = f"[size=18][font=Poppins-SemiBold.ttf][color=#FFFFFF]{food['label']}[/color][/font][/size]"
        weight = round((food['selected_weight']))
        secondary_text = f"[size=13][font=Poppins-Regular.ttf][color=#FFFFFF]{nutrients['kcal']}kcal {nutrients['protein']}P {nutrients['carbs']}C {nutrients['fats']}F • {weight}g[/color][/font][/size]"
        return {'text': food_text, 'secondary_text': secondary_text, 'original_data': food}

    def calculate_totals(self, food_list):
        for new_food in food_list:
            selected_weight = new_food.get('selected_weight', 1)
            portion_factor = round(float(selected_weight) / 100, 2) * float(new_food['portion_size'])
            total_calories += new_food['original_macros']['calories'] * portion_factor
            total_protein += new_food['original_macros']['protein'] * portion_factor
            total_fats += new_food['original_macros']['fats'] * portion_factor
            total_carbs += new_food['original_macros']['carbs'] * portion_factor
        print(food_list)
        print(self.total_calories, self.total_protein, self.total_fats, self.total_carbs)
        return self.total_calories
    def log_food(self):
        try:
            user_id = self.manager.get_screen('initialpage').user_id
        except AttributeError:
            user_id= '262efaa4-1a2d-484e-8de8-32966c8a6a82'
        date = datetime.now().strftime("%Y-%m-%d")  # Current date

        for food in self.logged_foodlist:
            # Prepare data for database insertion
            label = food['label']
            kcal = food['calories']
            protein = food['protein']
            carbs = food['carbs']
            fats = food['fats']
            fiber = food['fiber']
            portion_size = food['portion_size']
            selected_weight = food.get('selected_weight', 1)
            unit = food['unit']


            db_manager.insert_logged_foods(user_id, label, kcal, protein, carbs, fats, fiber, portion_size, selected_weight, unit, date)
        self.logged_foodlist.clear()

    def rebuild_food_list(self):
        try:
            user_id = self.manager.get_screen('initialpage').user_id
        except AttributeError:
            user_id= '262efaa4-1a2d-484e-8de8-32966c8a6a82'
        date = datetime.now().strftime("%Y-%m-%d")  # Current date

        # Get the food data from the database
        food_items = db_manager.get_food_items(user_id, date)
        for index, item in enumerate(food_items):
            # Unpack the tuple
            user_id, label, kcal, protein, carbs, fats, fiber, portion_size, selected_weight, unit, timestamp = item

            # Convert the values to the correct types and calculate the macros per 100g so that it can display them and use them for calculations properly
            portion_size = float(portion_size)
            selected_weight = float(selected_weight)

            kcal = float(kcal)
            protein = float(protein)
            carbs = float(carbs)
            fats = float(fats)
            fiber = float(fiber)

            unit_sequence = self.unit_to_sequence[unit]

            food_data = {
                'index': index,
                'label': label,
                'calories': kcal,
                'protein': protein,
                'carbs': carbs,
                'fats': fats,
                'fiber': fiber,
                'portion_size': portion_size,
                'selected_weight': selected_weight,
                'unit': unit,
                'unit_sequence': unit_sequence,
                'original_macros': {
                    'calories': round(kcal/ portion_size / selected_weight * 100, 2),
                    'protein': round(protein/ portion_size / selected_weight * 100, 2),
                    'carbs': round(carbs/ portion_size / selected_weight * 100, 2),
                    'fats': round(fats/ portion_size / selected_weight * 100, 2)
                }
            }

            self.logged_foodlist.append(food_data)
            food_data['index'] = index

        # Recalculate the totals        
        self.ids.added_food_rv.data = [self.create_food_text(food, self.calculate_nutrients(food)) for food in self.logged_foodlist]
        self.total_calories = self.calculate_totals(self.logged_foodlist)
   
    def saved_foods(self):
        food_data = copy.deepcopy(self.current_unpacked_data)
        print(food_data)
        print(self.logged_foodlist)
        # Update or add the food item
        if self.editing_index is None: 
            food_data['index'] = len(self.logged_foodlist)
            self.logged_foodlist.append(food_data)
        else:
            self.logged_foodlist[self.editing_index] = food_data
            self.editing_index = None

        # Update the RecycleView data and total calories
        self.ids.added_food_rv.data = [self.create_food_text(food, self.calculate_nutrients(food)) for food in self.logged_foodlist]
        self.total_calories = self.calculate_totals(self.logged_foodlist)

        # Update UI elements
        self.update_ui_elements()

    def remove_food(self, original_data):
        index = next((i for i, food in enumerate(self.logged_foodlist) if food['index'] == original_data['index']), None)
        if index is not None:
            self.logged_foodlist.pop(index)
        for i, food in enumerate(self.logged_foodlist):
            food['index'] = i

        self.ids.added_food_rv.data = [self.create_food_text(food, self.calculate_nutrients(food)) for food in self.logged_foodlist]
        self.total_calories = self.calculate_totals(self.logged_foodlist)

        # Update UI elements
        self.update_ui_elements()

    def update_ui_elements(self):
        self.ids.calories_consumed.text = f"{round(self.total_calories)}/{self.daily_calories}"
        self.ids.daily_calories_consumed.progress = round((self.total_calories / self.daily_calories) * 100) if self.daily_calories else 0

    def quick_actions(self, barcode, search, quickadd):
        states = {
            'barcode': (0, ('scan', 1), ('search', .3), ('quick_add', .3)),
            'search': (150, ('scan', .3), ('search', 1), ('quick_add', .3)),
            'quickadd': (300, ('scan', .3), ('search', .3), ('quick_add', 1))
        }

        state = 'barcode' if barcode else 'search' if search else 'quickadd'
        bar_position, *opacities = states[state]

        self.ids.horizontal_bar.bar_position = bar_position

        for name, opacity in opacities:
            getattr(self.ids, f'{name}_icon').opacity = opacity
            getattr(self.ids, f'{name}_text').opacity = opacity
            
    def get_food_data(self, query):
        app_id = os.getenv("EDAMAM_APP_ID")
        app_key = os.getenv("EDAMAM_APP_KEY")
        url = f'https://api.edamam.com/api/food-database/v2/parser?app_id={app_id}&app_key={app_key}&ingr={query}&nutrition-type=logging'

        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Error: Unable to fetch data, status code {response.status_code}"

    def unpack_food_data(self, original_data):
        nutrients = original_data['food']['nutrients']
        measures = original_data.get('measures', [])
        serving_size = next((measure for measure in measures if measure.get('label') == 'Serving'), 100)
        unpacked_data = {
            'label': original_data['food']['label'],
            'calories': round(nutrients.get('ENERC_KCAL', 0),2),
            'carbs': round(nutrients.get('CHOCDF', 0),2),
            'protein': round(nutrients.get('PROCNT', 0),2),
            'fats': round(nutrients.get('FAT', 0),2),
            'fiber': round(nutrients.get('FIBTG', 0),2),  # Include fiber
            'portion_size': 1,  # Initialize portion_size with a default value
            'unit': 'serving',  # Save the unit name instead of the boolean sequence
            'unit_sequence': (True, False, False, False, False, False),  # Initialize unit_sequence with a default value (serving
            'selected_weight': int(serving_size['weight']) 
        }
        original_macros = {
            'calories': unpacked_data['calories'],
            'protein': unpacked_data['protein'],
            'carbs': unpacked_data['carbs'],
            'fats': unpacked_data['fats']
        }
        unpacked_data['original_macros']=original_macros
        return unpacked_data
    
    def unit_to_sequence_func(self, unit):
        return self.unit_to_sequence.get(unit, (True, False, False, False, False, False))

    def perform_search(self, *args):
        try:
            query = self.ids.search_field.text
            data = self.get_food_data(query)
            filtered_foods = []
            if isinstance(data.get('hints'), list):
                for hint in data['hints']:
                    if isinstance(hint.get('food'), dict) and query.lower() in hint['food'].get('label', '').lower():
                        unpacked_data = self.unpack_food_data(hint)
                        food_text = f"[size=18][font=Poppins-SemiBold.ttf][color=#FFFFFF]{unpacked_data['label']}[/color][/font][/size]"
                        
                        weight = unpacked_data['selected_weight']
                        
                        # Calculate the portion factor
                        portion_factor = weight / 100 if weight != 'N/A' else 1
                        
                        # Calculate the kcal and other macros for the serving size
                        kcal = round(unpacked_data['calories'] * portion_factor)
                        protein = round(unpacked_data['protein'] * portion_factor)
                        carbs = round(unpacked_data['carbs'] * portion_factor)
                        fats = round(unpacked_data['fats'] * portion_factor)
                        
                        secondary_text = f"[size=13][font=Poppins-Regular.ttf][color=#FFFFFF]{kcal}kcal {protein}P {carbs}C {fats}F • {weight}g[/color][/font][/size]"
                        filtered_foods.append({'text': food_text, 'secondary_text': secondary_text, 'original_data': unpacked_data})

            self.ids.rv.data = filtered_foods
        except Exception as e:
            print(f"An error occurred: {e}")

    def search_query(self, query):
        # Reset the countdown for the search trigger and adjust the opacity of the search label based on whether the search field is empty
        if self.ids.search_field.text:
            self.search_trigger.cancel()
            self.ids.search_label.opacity=0
        else :
            self.ids.search_label.opacity=.3
        self.search_trigger.cancel()
        self.search_trigger()  

    def change_screen(self, *args, screen_name):
        self.ids.food_screen_manager.current = screen_name

    def food_details(self, unpacked_data, index):
        self.editing_index = index
        Clock.schedule_once(lambda dt: self.change_screen(screen_name='food_details_screen'), 0.5)  
        # unpack the data
        self.kcal = unpacked_data['calories']
        self.carbs = unpacked_data['carbs']
        self.protein = unpacked_data['protein']
        self.fats = unpacked_data['fats']
        
        fiber = unpacked_data['fiber']
        self.serving = unpacked_data['selected_weight']

        # update the portion size, unit, and macros based on the portion size
        self.current_unpacked_data = copy.deepcopy(unpacked_data)  # Update current_unpacked_data

        self.portion_size = unpacked_data['portion_size']
        self.ids.portion_size.text = str(self.portion_size)

        self.kcal *= self.portion_size
        self.protein *= self.portion_size
        self.carbs *= self.portion_size
        self.fats *= self.portion_size

        protein_ratio = self.protein * 4.1 / self.kcal
        fat_ratio = self.fats * 8.8 / self.kcal
        carbs_ratio = ((self.carbs - fiber) * 4.1 + fiber * 1.9) / self.kcal
        total_ratio = protein_ratio + fat_ratio + carbs_ratio

        self.ids.protein_percentage.text = f"[size=15][font=Poppins-Medium.ttf]{round(protein_ratio/total_ratio*100)}%[/font][/size]"
        self.ids.fats_percentage.text = f"[size=15][font=Poppins-Medium.ttf]{round(fat_ratio/total_ratio*100)}%[/font][/size]"
        self.ids.carbs_percentage.text = f"[size=15][font=Poppins-Medium.ttf]{round(carbs_ratio/total_ratio*100)}%[/font][/size]"
        self.ids.food_details_label.text = unpacked_data['label']
        
        self.selected_unit(*self.unit_to_sequence_func(unpacked_data['unit']),)
        self.update_unpacked_data()
    
    def update_unpacked_data(self):
        # Get the current portion size and unit sequence
        try:
            portion_size = float(self.ids.portion_size.text)
        except ValueError:
            portion_size = 1  # default to 1 if the input is not a valid float

        # Update the current_unpacked_data
        self.current_unpacked_data['portion_size'] = portion_size
        
    def update_portion_values(self):
        print(self.current_unpacked_data)
        try:
            amount = round(float(self.ids.portion_size.text)* self.current_unpacked_data['selected_weight']/ 100, 2)
        except ValueError:
            amount = 1
        values = {key: round(self.current_unpacked_data['original_macros'][key] * amount, 2) for key in self.current_unpacked_data['original_macros']}
        self.current_unpacked_data.update(values)
        
        original_font_sizes = {
            'calories': 34,
            'protein': 22,
            'fats': 22,
            'carbs': 22
        }

        daily_values = {
            'calories': self.daily_calories,
            'protein': self.daily_protein,
            'fats': self.daily_fats,
            'carbs': self.daily_carbs
        }

        for key, value in values.items():
            if key == 'calories':
                text = str(round(value))
            else:
                text = str(round(value, 1))
            self.ids[f'{key}_amount'].text = text

            # Calculate the percentage of the nutrient over the daily amount
            percentage = round((value / daily_values[key]) * 100)
            self.ids[f'{key}_bar'].custom_text = f"{percentage}%"
            self.ids[f'{key}_bar'].value = percentage
            
            self.ids.calories_consumed.text = f"{round(self.total_calories)}/{self.daily_calories}"
            if self.daily_calories != 0:
                self.ids.daily_calories_consumed.progress = round((self.total_calories ) / self.daily_calories * 100)
            else:
                self.ids.daily_calories_consumed.progress = 0  # or whatever value makes sense in this case
                
            if len(text) > 4:
                if key == 'calories':
                    self.ids[f'{key}_amount'].font_size = original_font_sizes[key] - (len(text) - 4) * 5.5
                else:
                    self.ids[f'{key}_amount'].font_size = original_font_sizes[key] - (len(text) - 4) * 2
            else:
                self.ids[f'{key}_amount'].font_size = original_font_sizes[key]
                
    def selected_unit(self, serving, oz, g, hg, lb, cup):
        white = [1, 1, 1, 1]
        black = [0, 0, 0, 1]
        original_color = [35/255, 35/255, 35/255, 1]  

        units = {
            'serving': {'condition': serving, 'weight': self.serving},
            'oz': {'condition': oz, 'weight': 28.3},
            'g': {'condition': g, 'weight': 1},
            'hg': {'condition': hg, 'weight': 100},
            'lb': {'condition': lb, 'weight': 453.6},
            'cup': {'condition': cup, 'weight': 200},
        }

        # Determine the selected unit
        self.current_unpacked_data['unit'] = next(unit for unit, details in units.items() if details['condition'])

        # Reset color of all buttons
        for unit_name in units:
            button = self.ids[f'portion_unit_{unit_name}']
            button.btn_color = button.btn_color_down = original_color
            button.color = white  # Reset text color to white

        # Set color and text of the selected button
        for unit_name, details in units.items():
            if details['condition']:
                button = self.ids[f'portion_unit_{unit_name}']
                button.btn_color = button.btn_color_down = white
                button.color = black
                self.ids.portion_hint_text.text = f"{unit_name} • {round(details['weight'])}g"
                self.portion_size = round(float(self.serving)/100* details['weight'], 2)
                self.current_unpacked_data['selected_weight'] = details['weight']
                break
        self.update_unpacked_data()
        self.update_portion_values()
class SelectWorkout(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.workout_plans = {}  # Dictionary to store workout plans
        self.workout_name= None  # Variable to store the name of the selected workout
        self.opened= False  # Flag to check if a workout plan details are opened
        self.plan= {}  # Dictionary to store the details of a workout plan
        self.generated_plan = None  # Variable to store the generated plan
    def on_kv_post(self, base_widget):
        # This method is called after all the KV rules for this widget have been processed.
        # The base_widget parameter is the root widget of the KV rules tree, i.e. the widget that was created with the Builder.load*() call.
        self.populate_workout()  # Populate the workout plans
        self.ids.selected_workout.text = "Select Workout"  # Set the initial text of the selected_workout label
        return super().on_kv_post(base_widget)  # Call the parent's on_kv_post method
    
    def get_plans_from_database(self):
        # This function retrieves workout plans from the database for a specific user.
        try:
            user_id = self.manager.get_screen('initialpage').user_id
        except AttributeError:
            user_id= '262efaa4-1a2d-484e-8de8-32966c8a6a82'
        plans = db_manager.get_plan_names(user_id)  # Fetch the plan names from the database
        return plans  # Return the fetched plans

    def populate_workout(self):
        # This function populates the workout plans in the RecycleView.
        user_plans = self.get_plans_from_database()  # Get the user's workout plans from the database
        plans = []  # Initialize an empty list to store the plans
        # Predefined workout names and icons
        workout_name = ['Single Workout']
        plan_icons = ['lightning-bolt']
        # Extend the workout names and icons with user's plans and random icons
        if user_plans:
            workout_name.append('Generated Plan')
            plan_icons.append('creation')
            workout_name.extend(user_plans)
            random_icons = ['dumbbell', 'weight-lifter', 'weight']
            [plan_icons.append(random.choice(random_icons)) for _ in range(len(workout_name) - 1)]
        # Create a dictionary for each workout plan and add it to the plans list
        for x in range(len(workout_name)):
            item = {'text': f"[size=24][font=Poppins-SemiBold.ttf][color=#FFFFFF]{workout_name[x]}[/color][/font][/size]", 'icon': plan_icons[x]}
            plans.append(item)
        # Update the workout_plans attribute and the data of the RecycleView
        self.workout_plans = plans
        self.ids.workout_view.data = self.workout_plans

    def edit_item(self, text):
        # This function is called when a workout plan is selected for editing.
        try:
            user_id = self.manager.get_screen('initialpage').user_id
        except AttributeError:
            user_id= '262efaa4-1a2d-484e-8de8-32966c8a6a82'
        # Extract the workout name from the text
        workout_name = re.search(r'\[color=#FFFFFF](.*?)\[/color]', text).group(1)
        # Fetch the workout plan from the database
        plan = db_manager.retrieve_workout_plan(user_id, workout_name)
        if plan:
            # If the plan exists, update the empty_plan screen with the plan and switch to it
            empty_plan_screen = self.manager.get_screen('empty_plan')
            empty_plan_screen.update_plan(plan)
            self.manager.current = "empty_plan"
            
    def choose_plan_panel(self, text):
        # This function is called when a user selects a workout plan from the list.
        # If the panel is not opened, return
        if self.opened== False:
            self.ids.behind_panel_rec.pos_hint= {'center_x': 2,'center_y': 2}
            return
        # Extract the workout name from the selected item
        workout_name = re.search(r'\[color=#FFFFFF](.*?)\[/color]', text).group(1)
        # If the name is 'Single Workout', switch to the logworkout screen and start a single workout
        if workout_name == 'Single Workout':
            self.ids.behind_panel_rec.pos_hint= {'center_x': 2,'center_y': 2}
            self.manager.current = "logworkout"
            MDApp.get_running_app().root.get_screen('logworkout').on_single_workout()
            return

        try:
            user_id = self.manager.get_screen('initialpage').user_id
        except AttributeError:
            user_id= '262efaa4-1a2d-484e-8de8-32966c8a6a82'
        if workout_name == 'Generated Plan':
        # If the name is 'Generated Plan', check if a generated plan already exists
            self.ids.behind_panel_rec.pos_hint= {'center_x': 2,'center_y': 2}
            if self.generated_plan:
                self.on_generate_plan(generated_plan= None)
            else:
                # If no generated plan exists, switch to the input training frequency screen to generate a plan
                self.manager.current = "inputtrainingfrequency" #switch to the input training frequency screen to generate a plan
                return
        # If the name is different from the previously selected workout, fetch the workout plan from the database and update the self.plan attribute
        elif workout_name!= self.workout_name :
            self.plan= db_manager.retrieve_workout_plan(user_id, workout_name)
        # Update the self.workout_name attribute
        self.workout_name= workout_name
        # Get the number of days in the plan
        day_number = [i for i in range(1,len(self.plan)+1)]
        # Access the BoxLayout within AnchorLayout
        items_box = self.ids.items_box  
        # Clear the BoxLayout
        items_box.clear_widgets()  
        # For each day in the plan, create a SavePlanItem and add it to the BoxLayout
        for day in day_number:
            save_plan_item = SavePlanItem(day=day,selected_exercises= self.plan, clickable=True)
            items_box.height= dp(35)*len(day_number)
            items_box.add_widget(save_plan_item)  
        # Update the position of the behind_panel_rec widget and toggle the choose_plan_panel
        self.ids.behind_panel_rec.pos_hint= {'center_x': 0.5,'center_y': 0.5}
        self.ids.choose_plan_panel.toggle()
        # Toggle the self.opened flag
        self.opened= not self.opened   
        
    def on_generate_plan(self, generated_plan= None): 
        # This function is called from the GeneratePlan class after a plan is generated.
        if self.generated_plan:
            # If a generated plan already exists, update the existing plan with the new exercises
            for day, data in self.generated_plan.items():
                day_number = int(day.split('_')[1])  # Extract the day number from the string
                exercises = data['exercises']
                new_exercises = []
                for exercise in exercises:
                    new_exercise = {
                        'name': exercise['name'],
                        'sets': 3,
                        'reps': 10
                    }
                    new_exercises.append(new_exercise)
                self.plan[day_number] = new_exercises
            return
        else:
            # If no generated plan exists, assign the generated plan to the self.generated_plan attribute
            self.generated_plan = generated_plan
                    
    def on_log_workout(self, day): 
        # This function is called to switch to the log workout screen and pass the plan to it.
        day_number = day[-1]  # Extract the day number from the day argument
        plan = self.plan.get(int(day_number))  # Retrieve the corresponding plan
        # Assign the plan to the plan attribute of the logworkout screen
        MDApp.get_running_app().root.get_screen('logworkout').plan= plan
        # Initialize the workout on the logworkout screen
        MDApp.get_running_app().root.get_screen('logworkout').initialize_workout()
        # Switch to the logworkout screen
        self.manager.current = "logworkout"
class EmptyPlan(Screen):
    """
    A screen in a fitness app that represents an empty workout plan.
    Allows the user to navigate between different days of the plan, add exercises to the plan,
    and display the workout details for each day.
    """
    def __init__(self, **kw):
        super().__init__(**kw)
        self.training_days = 5
        self.workout_plans_by_day = {day: [] for day in range(1, self.training_days + 1)}
        self.added_exercises = [False for _ in range(self.training_days)]
        self.current_day = 1
        self.workout_plans = []
        self.add_exercise_button_new= "add_exercises_post_1"
        self.opened= False
        
    def update_plan(self, plan):
        self.workout_plans_by_day = plan
        self.training_days = len(plan)
        self.added_exercises = [False for _ in range(self.training_days)]
        self.added_exercises = [True if plan[day] else False for day in plan]
        self.ids.days_in_plan.clear_widgets()
        self.ids.invisible_rect.clear_widgets() 
        self.add_days_to_boxlayout()
        self.select_day(1)    
        self.populate_workout()
        self.added_exercises_to_plan(plan[1])
        
    def on_kv_post(self, base_widget):
        """
        Called after the widget has been added to the widget tree.
        Adds the days of the workout plan to the layout, selects the first day, and populates the workout details.
        """
        self.add_days_to_boxlayout()
        self.select_day(1)
        self.populate_workout()
        return super().on_kv_post(base_widget)

    def add_days_to_boxlayout(self):
        """
        Adds the days of the workout plan to the layout as labels and invisible rectangles for navigation.
        """
        for day in range(1, self.training_days + 1):
            label = Label(
                text=f"Day {day}",
                color=(1, 1, 1, 1),
                font_name="Poppins-SemiBold",
                font_size=15,
                halign='center'
            )
            invisible_rect = RoundedRectangle2(
                size_hint=(1, .5),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                opacity=0,
                on_release=partial(self.change_screen, day)
            )
            self.ids.days_in_plan.add_widget(label)
            self.ids.invisible_rect.add_widget(invisible_rect)

    def select_day(self, day, *args):
        """
        Updates the selected day and highlights it on the layout.
        """
        self.current_day = day
        self.ids.selected_day_rec.size_hint = (1 / self.training_days - .01, .5)
        base_center_x = (2 * day - 1) / (2 * self.training_days)
        adjusted_center_x = base_center_x
        self.ids.selected_day_rec.pos_hint = {'center_x': adjusted_center_x, 'center_y': 0.5}
        self.change_items()


    def change_screen(self, day, *args):
        exercise_plan_id=f"exercises_plan_{self.current_page}"
        self.ids[exercise_plan_id].data= [] #clear the data
        self.workout_plans= [] #clear the data
        """
        Changes the screen to the next or previous day of the workout plan based on the selected day.
        """
        if self.ids.empty_plan_scr.current == "empty_plan_day_1":
            self.ids.empty_plan_scr.current = "empty_plan_day_2"
        else:
            self.ids.empty_plan_scr.current = "empty_plan_day_1"
        if day > self.current_day:
            self.ids.empty_plan_scr.transition.direction = 'left'
        else:
            self.ids.empty_plan_scr.transition.direction = 'right'
        self.select_day(day, *args)

    def change_items(self):
        """
        Updates the title and subtitle of the current day's workout details.
        """
        self.current_page = self.ids.empty_plan_scr.current[-1]
        self.add_exercises_id = f"add_exercise_btn_{self.current_page}"
        self.exercise_list= f"exercises_list_{self.current_page}"
        title_id = f"title_{self.current_page}"
        subtitle_id = f"subtitle_{self.current_page}"
        self.ids[title_id].text = f"Day {self.current_day}"
        self.ids[subtitle_id].text = f"Day {self.current_day}"

        if self.added_exercises[self.current_day - 1]:
            self.added_exercises_to_plan(self.workout_plans_by_day[self.current_day])
        else:
            self.ids[self.add_exercise_button_new].pos_hint={"center_x": .18, "center_y": 2}
            self.ids[self.add_exercises_id].pos_hint= {'center_x': .5,'center_y': .5}
            self.ids[self.exercise_list].pos_hint= {'center_x': 2, 'center_y': 2}

    def added_exercises_to_plan(self, added_exercises):
        self.add_exercise_button_new= f"add_exercises_post_{self.current_page}"

        if len(added_exercises) > 5:
            y_coord= 0.105
        elif len(added_exercises) == 5:
            y_coord= 0.145
        elif len(added_exercises) == 4:
            y_coord= 0.26
        elif len(added_exercises) == 3:
            y_coord= 0.375
        elif len(added_exercises) == 2:
            y_coord= 0.51
        else:
            y_coord= 0.63

        if added_exercises:
            self.added_exercises[self.current_day - 1] = True
            self.ids[self.add_exercise_button_new].pos_hint={"center_x": .18, "center_y": y_coord}
            self.ids[self.add_exercises_id].pos_hint= {'center_x': 2, 'center_y': 2}
            self.ids[self.exercise_list].pos_hint= {'center_x': .5, 'center_y': 0.45}
            self.workout_plans_by_day[self.current_day] = copy.deepcopy(added_exercises)
            # Check if the exercises are already in the desired dictionary format
            if added_exercises and (not isinstance(added_exercises[0], dict)):
                # Convert list of exercise names to list of dictionaries only if they are not already dictionaries
                self.workout_plans_by_day[self.current_day] = [
                    {'name': exercise, 'sets': 3, 'reps': 12} for exercise in added_exercises
                ]
            else:
                # If they are already dictionaries, use them as is
                self.workout_plans_by_day[self.current_day] = copy.deepcopy(added_exercises)

            self.populate_workout()
    
    def populate_workout(self):
        """
        Populates the workout plan with exercise details.
        """
        if self.added_exercises[self.current_day - 1]:
            self.workout_plans.clear()  # Clear the list to repopulate it

            for exercise_dict in self.workout_plans_by_day[self.current_day]:
                exercise_name = exercise_dict['name']
                sets = exercise_dict['sets']
                reps = exercise_dict['reps']

                # Find the exercise in the exercises dictionary
                exercise = next((e for e in exercises if e['name'] == exercise_name), None)
                if exercise is not None:
                    item = {
                        'image_source': exercise['icon'],
                        'text': f"[size=17][font=Poppins-Bold.ttf][color=#FFFFFF]{exercise_name}[/color][/font][/size]",
                        'sets_text': f"{sets} SETS",
                        'reps_text': f"{reps} REPS",
                    }
                    self.workout_plans.append(item)

            exercise_plan_id = f"exercises_plan_{self.current_page}"
            self.ids[exercise_plan_id].data = self.workout_plans

    def find_exercise_index(self, ex_name):
        for i, exercise in enumerate(self.workout_plans_by_day[self.current_day]):
            if exercise['name'] == ex_name:
                return i

    def update_sets_and_reps(self, ex_name, sets_text, reps_text, move_value):
        ex_name = re.search(r'\[color=#FFFFFF](.*?)\[/color]', ex_name).group(1)
        sets = int(sets_text.split()[0])  # Extract sets number
        reps = int(reps_text.split()[0])  # Extract reps number

        i = self.find_exercise_index(ex_name)
        if move_value is None:
            # Update the exercise in the workout plan for the current day
            self.workout_plans_by_day[self.current_day][i]['sets'] = sets
            self.workout_plans_by_day[self.current_day][i]['reps'] = reps
        else:
            # Change order of the exercises
            exercise = self.workout_plans_by_day[self.current_day].pop(i)
            if move_value == -1:  # Move the current exercise one position up
                self.workout_plans_by_day[self.current_day].insert(i - 1, exercise)
            else:  # Move the current exercise one position down
                self.workout_plans_by_day[self.current_day].insert(i + 1, exercise)
  
        # Debug print to check the structure after the update

    def toggle_save_panel(self):
        self.opened= not self.opened 
        if self.opened:
            self.ids.behind_panel_rec.pos_hint= {'center_x': 0.5,'center_y': 0.5}
        else:
            self.ids.behind_panel_rec.pos_hint= {'center_x': 2,'center_y': 2}
            return
        day_number = [i for i in range(1,len(self.workout_plans_by_day)+1)]
        items_box = self.ids.items_box  # Access the BoxLayout within AnchorLayout
        items_box.clear_widgets()  # Clear the BoxLayout
        for day in day_number:
            save_plan_item = SavePlanItem(day=day,selected_exercises= self.workout_plans_by_day)
            items_box.height= dp(35)*len(day_number)
            items_box.add_widget(save_plan_item)  # Add SavePlanItem to the BoxLayout

    def save_plan(self):
        try:
            user_id = self.manager.get_screen('initialpage').user_id
        except AttributeError:
            user_id= '262efaa4-1a2d-484e-8de8-32966c8a6a82'
        plan_name= self.ids.plan_name.text
        workout_plan=self.workout_plans_by_day
        db_manager.save_complete_workout_plan(user_id, plan_name, workout_plan)
class LogWorkout(Screen):
    def __init__(self, **kwargs):
        super(LogWorkout, self).__init__(**kwargs)
        self.last_clicked_item = None  # Stores the last clicked item in the workout plan
        self.type = None  # Stores the type of the selected row (either "reps" or "weight")
        self.workout_rows = []  # Stores the rows of the current workout
        self.current_row = {}  # Stores the index of the current row in the workout
        self.selected_row = []  # Stores the index of the selected row in the workout
        self.sets= None  # Stores the number of sets for the current exercise
        self.current_item_id = 0  # Stores the id of the current item in the workout plan
        self.current_page = 1  # Stores the current page number in the workout plan
        self.plan= []  # Stores the workout plan
        self.workout_rows_instances = {}  # Stores the instances of WorkoutRow for each exercise in the plan
        self.workout_data = {}  # Stores the weight, reps, and tenrm for each set of each exercise

    def initialize_workout(self):
        # Initialize the workout_rows_instances dictionary with an empty list for each exercise in the plan
        self.current_row= {exercise : 0 for exercise in range(len(self.plan)+1)}
        # Initialize the workout_rows_instances dictionary with an empty list for each exercise in the plan
        self.workout_rows_instances= {exercise : [] for exercise in range(len(self.plan)+1)}
        # For each exercise in the plan, create a WorkoutImage and add it to the layout
        for i in range(len(self.plan)):
            item = WorkoutImage(source_image=((self.plan[i]['name']).lower().replace(" ", "")+".png"), item_id=i)
            self.ids.bl.add_widget(item)
        # Set the opacity of the first image for the exercise to 1 since all the other images are set to 0.5
        self.set_opacity(self.ids.bl.children[-1])  
        self.add_plus_icon() 
        # Set the type of the first workout row to "current" and update its icon
        self.workout_rows[0].type = "current"
        self.workout_rows[0].update_icon()
        # Store the current page number
        self.current_page= self.ids.logworkout_sm.current[-1]
        # Set the text of the exercise_name_1 label to the name of the first exercise in the plan
        self.ids.exercise_name_1.text = self.plan[0]['name']
        self.update_sets()
        
    def add_plus_icon(self):
        # Add a plus icon to the layout to allow the user to add new exercises to the plan
        item = WorkoutImage(source_image="plus_bg.png", item_id=len(self.plan), opacity=1)
        self.ids.bl.add_widget(item)
        
    def add_set(self):
        # Create a new instance of WorkoutRow
        new_row = WorkoutRow(
            pos_hint={'center_x': 0.5, 'center_y': 0.71 - 0.05 * self.plan[self.current_item_id]['sets']},  # Position of the row
            set=str(self.plan[self.current_item_id]['sets'] + 1),  # Set number
        )
        # Add the new row to self.workout_rows
        self.workout_rows.append(new_row)
        # Add the new row to self.workout_rows_instances
        self.workout_rows_instances[self.current_item_id].append(new_row)
        # Add the new row to the appropriate layout in the UI
        log_sets_layout = f"log_sets_layout_{self.current_page}"
        self.ids[log_sets_layout].add_widget(new_row)
        # If the new set is the current set, update self.current_row and set the type of the new row to "current"
        if self.current_row[self.current_item_id]+1 == self.plan[self.current_item_id]['sets'] and self.workout_rows[self.current_row[self.current_item_id]].type == "done":
            print("current row", self.current_row[self.current_item_id])
            self.current_row[self.current_item_id] += 1
            new_row.type = "current"
            new_row.update_icon()
        # Update self.plan to reflect the new number of sets
        self.plan[self.current_item_id]['sets'] += 1
        self.update_sets()
        
    def remove_set(self):
        # Check if there are more than one sets
        if len(self.workout_rows) > 1:
            # Remove the last row from self.workout_rows
            last_row = self.workout_rows.pop()
            # Remove the last row from self.workout_rows_instances
            if last_row in self.workout_rows_instances[self.current_item_id]:
                self.workout_rows_instances[self.current_item_id].remove(last_row)
            # Remove the last row from the appropriate layout in the UI
            log_sets_layout = f"log_sets_layout_{self.current_page}"
            self.ids[log_sets_layout].remove_widget(last_row)
            # Update self.plan to reflect the new number of sets
            self.plan[self.current_item_id]['sets'] -= 1
            # If the removed set was the current set, update self.current_row and set the type of the new last row to "current"
            if self.current_row[self.current_item_id] == len(self.workout_rows):
                self.current_row[self.current_item_id] -= 1
                self.workout_rows[-1].type = "current"
                self.workout_rows[-1].update_icon()
            # Update self.workout_data to remove the data for the removed set
            if self.current_item_id in self.workout_data and len(self.workout_rows) in self.workout_data[self.current_item_id]:
                del self.workout_data[self.current_item_id][len(self.workout_rows)]    
            self.update_sets()
            
    def update_sets(self):
        self.ids.set_label.text = str(self.plan[0]['sets'])
        
    def generate_rows(self):
        y = 0.71  # Initial y position for the first row
        log_sets_layout = f"log_sets_layout_{self.current_page}"  # Get a reference to log_sets_layout
        for i in range(1,(self.plan[self.current_item_id]['sets'])+1):  # For each set in the current exercise
            workout_row = WorkoutRow(
                pos_hint={'center_x': 0.5, 'center_y': y},  # Position of the row
                set=str(i),  # Set number
            )
            self.ids[log_sets_layout].add_widget(workout_row)  # Add the row to log_sets_layout
            self.workout_rows.append(workout_row)  # Add the row to the list of workout rows
            y -= 0.05  # Decrease the y position for the next row
        self.workout_rows[0].reps= str(self.plan[self.current_item_id]['reps'])  # Set the reps for the first row
        
    def add_exercise(self, exercise_names):
        # Remove the plus icon from the box layout
        if self.ids.bl.children: 
            self.ids.bl.remove_widget(self.ids.bl.children[0])

        # Loop through the list of exercise names and create a new WorkoutImage for each exercise
        for i in range(len(exercise_names)):
            # The item_id is the current length of the plan plus the index of the exercise
            item = WorkoutImage(source_image=((exercise_names[i]).lower().replace(" ", "")+".png"), item_id=(len(self.plan)+i))
            self.ids.bl.add_widget(item)
            
        self.add_plus_icon() # Add the plus icon back to the box layout
        # Loop through the list of exercise names again
        for exercise in exercise_names:
            # Add a new exercise to the plan with the default sets and reps
            self.plan.append({'name': exercise, 'sets': 3, 'reps': 10})
            # Set the current row for the new exercise to 0
            self.current_row[len(self.plan)-1] = 0
            # Initialize the workout rows instances for the new exercise to an empty list
            self.workout_rows_instances[len(self.plan)-1] = []
            
        # Add a new entry for the exercise in current_row and workout_rows_instances
        new_index = len(self.plan) - 1
        self.current_row[new_index] = 0
        self.workout_rows_instances[new_index] = []
        
        # Set the opacity of the first added image to 1 and change the screen to that
        self.set_opacity(self.ids.bl.children[(-(len(self.plan)-len(exercise_names)+1))])
        
        
    def remove_exercise(self):
        exercise_index = self.current_item_id
             
        # Remove the exercise from the plan, current_row, and workout_rows_instances
        del self.plan[exercise_index]
        del self.current_row[exercise_index]
        self.workout_rows.clear()
        if self.workout_rows_instances[exercise_index] != []:
            del self.workout_rows_instances[exercise_index]

        # Remove the exercise from workout_data
        if exercise_index in self.workout_data:
            del self.workout_data[exercise_index]
  
        # Re-index the remaining exercises
        for i in range(exercise_index, len(self.plan)):
            self.current_row[i] = self.current_row.pop(i + 1)
            self.workout_rows_instances[i] = self.workout_rows_instances.pop(i + 1)
            if i + 1 in self.workout_data:
                self.workout_data[i] = self.workout_data.pop(i + 1)

        # Update the UI
        self.ids.bl.clear_widgets()
        for i in range(len(self.plan)):
            item = WorkoutImage(source_image=((self.plan[i]['name']).lower().replace(" ", "")+".png"), item_id=i)
            self.ids.bl.add_widget(item)
        self.add_plus_icon()
        
        if self.current_item_id < len(self.plan) - 1:
            self.set_opacity(self.ids.bl.children[(-(exercise_index+1))])
        else:
            self.set_opacity(self.ids.bl.children[-1])

        
    def change_screen(self, item_id):
        print("screen changed")
        # Determine the direction of the transition based on the item_id
        if item_id > self.current_item_id:
            self.ids.logworkout_sm.transition.direction = 'left'
        elif item_id < self.current_item_id:
            self.ids.logworkout_sm.transition.direction = 'right'
        elif item_id == len(self.plan):
            return
        # Switch between the two pages to give the illusion of multiple pages
        if self.ids.logworkout_sm.current == "logworkout_scr_1":
            self.ids.logworkout_sm.current = "logworkout_scr_2"
        else:
            self.ids.logworkout_sm.current = "logworkout_scr_1"
        # Update the current page number
        self.current_page = self.ids.logworkout_sm.current[-1]
        # Store the current workout rows
        self.workout_rows_instances[self.current_item_id] = self.workout_rows
        # Update the current item id
        self.current_item_id = item_id
        # Update the exercise name label
        exercise_name_id = f"exercise_name_{self.current_page}"
        self.ids[exercise_name_id].text = self.plan[self.current_item_id]['name']
        #update position of the three dots icon
        dots_rec_id = f"dots_rec_{self.current_page}"
        dots_id= f"dots_{self.current_page}"
        #find the width of the exercise name based on a dictionary of character widths that i made
        characters = characters_width_dict.get_text_width(self.plan[self.current_item_id]['name'])
        #use a formula that i found through trial and error to calculate the distance the icon should move
        distance = round((characters - 31.8)*0.0113,2) 
        self.ids[dots_rec_id].pos_hint= {'center_x': 0.48+distance,'center_y': 0.82}
        self.ids[dots_id].pos_hint = {'center_x': 0.48+distance,'center_y': 0.82}
        # Clear the current sets layout
        log_sets_layout = f"log_sets_layout_{self.current_page}"
        self.ids[log_sets_layout].clear_widgets()
        # If there are no workout rows for the current item, generate new rows
        if self.workout_rows_instances[self.current_item_id] == []:
            self.workout_rows = []
            self.generate_rows()
            self.workout_rows[0].type = "current"
            self.workout_rows[0].update_icon()
            
        else:
            # Otherwise, load the existing workout rows
            self.workout_rows = []
            self.workout_rows = self.workout_rows_instances[self.current_item_id]
            for i in range(len(self.workout_rows)):
                widget = self.workout_rows[i]
                if widget.parent:
                    widget.parent.remove_widget(widget)
                self.ids[log_sets_layout].add_widget(widget)
                
    def set_opacity(self, selected_item):
        # Set the opacity of the last clicked image for the exercise to 0.5
        if self.last_clicked_item:
            self.last_clicked_item.opacity = 0.5
        selected_item.opacity = 1 # Set the opacity of the selected image for the exercise to 1
        self.last_clicked_item = selected_item
        
        if selected_item.item_id == len(self.plan):
            self.manager.transition= NoTransition()
            MDApp.get_running_app().root.get_screen('exercise_list').pass_exercises_to_logworkout()
            self.manager.current = "exercise_list"
            return
        self.change_screen(selected_item.item_id)  # Change the screen to the selected exercise
        
    def on_cancel(self):
        #method to move the choose_item widget off the screen
        self.ids.choose_item.pos_hint = {'center_x': 2.5,'center_y': 0.5}
    
    def choose_item(self, row, type):        
        # Store the index of the selected row
        self.selected_row = int(row) -1
        # Check if the selected row is a row that is not marked as done or current, if so, exit the method
        if self.workout_rows[self.selected_row].type == "todo":
            return
        # Move the choose_item widget to the center of the screen
        self.ids.choose_item.pos_hint = {'center_x': 0.5,'center_y': 0.5}
        # Store the type of the selected row (either "reps" or "weight")
        self.type= type
        # Depending on the type, populate the recycleview with the appropriate data
        if type == "reps":
            self.ids.choose_item.ids.choose_item_rv.data = [{'text': f'{i}  rep'} if i== 1 else {'text': f'{i}  reps'} for i in range(1, 100)] 
        elif type == "weight":
            self.ids.choose_item.ids.choose_item_rv.data = [{'text': f'{i/2}  kgs'} for i in range(1, 300)] 

    def chosen_item(self, number):
        # Depending on the type, set the reps or kg of the selected row to the chosen number
        if self.type == "reps":
            self.workout_rows[self.selected_row].reps = number
        elif self.type == "weight":
            self.workout_rows[self.selected_row].kg = number
        # Move the choose_item widget off the screen
        self.ids.choose_item.pos_hint = {'center_x': 2.5,'center_y': 0.5}
        # if an item is changed and it was previously marked as done, update the workout data
        if self.workout_rows[self.selected_row].type == "done":
            if self.current_item_id not in self.workout_data:
                self.workout_data[self.current_item_id] = {}
            self.workout_data[self.current_item_id][self.selected_row[self.current_item_id]] = {
                'weight': self.workout_rows[self.selected_row[self.current_item_id]].kg,
                'reps': self.workout_rows[self.selected_row[self.current_item_id]].reps,
                'tenrm': self.workout_rows[self.selected_row[self.current_item_id]].tenrm,
            }
        # Update the icon of the selected row            
        self.workout_rows[self.selected_row].update_icon()
        # Calculate the 10 rep max for the selected row
        self.calculate10RM()

    def next_row(self):
        # Check if the current row is not empty
        if self.workout_rows[self.current_row[self.current_item_id]].type == "current" and self.workout_rows[self.current_row[self.current_item_id]].reps != "-" and self.workout_rows[self.current_row[self.current_item_id]].kg != "-":
            # Mark the current row as done
            self.workout_rows[self.current_row[self.current_item_id]].type = "done"
            # Update the icon of the current row
            self.workout_rows[self.current_row[self.current_item_id]].update_icon()
            # Update the workout data for the current row
            if self.current_item_id not in self.workout_data:
                self.workout_data[self.current_item_id] = {}
            self.workout_data[self.current_item_id][self.current_row[self.current_item_id] + 1] = {
                'weight': self.workout_rows[self.current_row[self.current_item_id]].kg,
                'reps': self.workout_rows[self.current_row[self.current_item_id]].reps,
                'tenrm': self.workout_rows[self.current_row[self.current_item_id]].tenrm,
            }
            # If there are more sets in the current exercise, move to the next row
            if self.current_row[self.current_item_id] < self.plan[self.current_item_id]['sets'] - 1:
                completed_row = self.workout_rows[self.current_row[self.current_item_id]]
                next_row = self.workout_rows[self.current_row[self.current_item_id] + 1]

                next_row.reps = completed_row.reps
                next_row.kg = completed_row.kg
                next_row.tenrm = completed_row.tenrm  

                # Move to the next row and mark it as the current row
                self.current_row[self.current_item_id] += 1
                self.workout_rows[self.current_row[self.current_item_id]].type = "current"
                self.workout_rows[self.current_row[self.current_item_id]].update_icon()
            else:
                def check_and_switch():
                    for i in range(len(self.plan)):
                        if i not in self.workout_data or len(self.workout_data[i]) != self.plan[i]['sets']:
                            self.set_opacity(self.ids.bl.children[-(i+1)])
                            return

                # Check if the current exercise is the last one in the plan
                if self.current_item_id == len(self.plan) - 1:
                    # Check if all exercises are done
                    if len(self.workout_data) == len(self.plan):
                        check_and_switch() 
                        self.ids.save_workout_panel.toggle()
                        self.ids.behind_panel_rec3.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                                                       
                    else:
                        # If not all exercises are done check which ones are not done and switch to that screen
                        for i in range(len(self.plan)):
                            if i not in self.workout_data:
                                self.set_opacity(self.ids.bl.children[-(i+1)])
                                break
                else:
                    # Check if all sets in the next exercises are done
                    if self.current_item_id + 1 in self.workout_data and len(self.workout_data[self.current_item_id + 1]) == self.plan[self.current_item_id + 1]['sets']:
                        print("All sets in the next exercise are done")
                        check_and_switch()
                        self.ids.save_workout_panel.toggle()
                        self.ids.behind_panel_rec3.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                    else:    
                        # If there are no more sets in the current exercise, move to the next exercise
                        self.set_opacity(self.ids.bl.children[-(self.current_item_id +2)])
                        return

                # If all exercises are done, print the workout data
                if self.current_item_id == len(self.plan)-1:
                    self.ids.save_workout_panel.toggle()
                    self.ids.behind_panel_rec3.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                else:
                    # Otherwise, update the opacity of the next exercise image
                    self.set_opacity(self.ids.bl.children[-(self.current_item_id)-1])
        else:
            # If the current row is empty, shake the row
            self.workout_rows[self.current_row[self.current_item_id]].shake_animation()
            
    def calculate10RM(self):
        # Check if the selected row has valid kg and reps values
        if self.workout_rows[self.selected_row].kg != "-" and self.workout_rows[self.selected_row].reps != "-":
            # Get the weight and reps from the selected row
            weight = self.workout_rows[self.selected_row].kg
            reps = self.workout_rows[self.selected_row].reps       
            # Calculate the one rep max using the Epley formula
            onerm= float(weight) * (1 + (0.0333 * (float(reps))))
            # Calculate the ten rep max as 75% of the one rep max
            tenrm = round(onerm * 0.75,1)
            # Store the ten rep max in the selected row
            self.workout_rows[self.selected_row].tenrm = str(tenrm)
    
    def save_workout(self):
        named_workout_data = {}
        for i, exercise in enumerate(self.plan):
            if i in self.workout_data:
                named_workout_data[exercise['name']] = self.workout_data[i]
        
    def on_back(self):
        exercises_completed = 0
        #store the exercise as 1 if all the sets are done and 0 if not
        for i in range(len(self.plan)):
            if i in self.workout_data and len(self.workout_data[i]) == self.plan[i]['sets']:
                exercises_completed += 1
        MDApp.get_running_app().root.get_screen('dashboard').exercise_completed= exercises_completed

    def on_single_workout(self):
        #method that is called when the user wants to directly start a workout without selecting a plan
        self.plan=[] #clear the plan
        #get the exercises from the exercise list screen which passes to the add_exercise method
        self.manager.transition= NoTransition()
        MDApp.get_running_app().root.get_screen('exercise_list').pass_exercises_to_logworkout()
        self.manager.current = "exercise_list"
class GeneratePlan(Screen):
    # Class representing the screen for generating a workout plan

    def get_user_details(self):
        # Method to retrieve user details from the database
        try:
            user_id = self.manager.get_screen('initialpage').user_id
        except AttributeError:
            user_id= '262efaa4-1a2d-484e-8de8-32966c8a6a82'
        user = UserManager.get_user(user_id)
        trainingfrequency = int(user.training_frequency[0])
        experiencelevel = user.experience_level
        prioritizemusclegroups = user.prioritized_muscle_groups
        gender = user.gender
        self.trainingfrequency = trainingfrequency 
        return trainingfrequency, experiencelevel, gender, prioritizemusclegroups

    muscle_divisions = {
        # Dictionary to divide muscles into their respective groups
        "chest": ["upper chest", "middle chest", "lower chest"],
        "upper back": ["rhomboids", "mid traps", "upper traps"],
        "lats": ["upper lats", "lumbar lats", "lower lats"],
        "shoulders": ["front delts", "side delts", "rear delts"],
        "quads": ["vastus medialis and lateralis", "rectus femoris"],
        "hamstrings": ["bicep femoris"],
        "glutes": ["gluteus medius", "gluteus maximus"],
        "calves": ["soleus", "gastroc"],
        "abs": ["upper abs", "lower abs"],
        "triceps": ["long head", "side and medial head"],
        "biceps": ["bicep brachii", "brachialis"],
        "forearms": ["brachioradialis", "wrist extensor", "wrist flexors"],
        "adductors": ["adductor magnus"]
    }

    @staticmethod
    def divide_muscles_to_prioritize(prioritizemusclegroups):
        # Static method to divide prioritized muscle groups into individual muscles
        muscles_to_prioritize = []
        for group in prioritizemusclegroups.split(','):
            group = group.strip()
            if group == 'shoulders':
                muscles_to_prioritize.extend(['front delts', 'side delts', 'rear delts'])
            else:
                muscles_to_prioritize.append(group)
        return muscles_to_prioritize

    
    @staticmethod
    def create_split():
        # Static method to create a list of workout splits
        # Each index in the list corresponds to a different workout plan
        # Each split is a tuple, where each element is a string representing a workout day
        split=[None]*15
        split[0]= ('full body') # 1 day split
        split[1]= ('upper body', 'lower body') # 2 day split 
        split[2]= ('push', 'pull', 'legs') # 3 day split 
        split[3]= ('chest', 'back', 'shoulders', 'arms', 'legs') # 5 day split
        split[4]=('biceps, chest, shoulders', 'triceps, back, core', 'quads, hamstrings, glutes, calves') # 3 day split 
        split[5]=('chest, shoulders, core', 'quads, calves, adductors', 'back, core', 'arms, forearms', 'posterior chain, calves, core',) # 5 day split, chest, back or arms focus
        split[6]= ('chest, forearms', 'quads, glutes, calves', 'shoulders, arms', 'hamstrings, glutes, core', 'back,core, forearms', 'quads, adductors, calves') # 6 day split, chest, leg focus
        split[7]=('full body', 'triceps, back', ' hamstrings, glutes', 'biceps, chest', 'back, shoulders', 'quads, glutes', 'calves, core' ) # 7 day split, leg focus
        split[8]= ('chest, tricpes', 'back, biceps', 'legs, core', 'shoulders', 'chest, back', 'biceps, tricpes', 'legs, core') # 6 day split, powerlifting focus, or powerbuilding
        split[9]= ('chest, shoulders, triceps', 'back, biceps, hamstrings', 'quads, glutes, calves, core' ) # 3 day split, powerlifting focus, or powerbuilding
        split[10]=('upper body', 'lower body', 'upper body', 'lower body') # 4 day split
        split[11]=('chest, shoulders', 'back, core', 'arms, calves', 'quads, hamstrings, glutes') # 4 day split, powerlifting focus, or powerbuilding
        split[12]=('biceps, chest, shoulders', 'triceps, back, core', 'quads, hamstrings, glutes, calves','biceps, chest, shoulders', 'triceps, back, core', 'quads, hamstrings, glutes, calves') # 6 day split, powerlifting focus, or powerbuilding
        split[13]= ('push', 'pull', 'legs', 'push', 'pull', 'legs') # 6 day split, push/pull/legs
        split[14]=('chest, triceps, forearms', 'shoulders, hamstrings, core', 'back, biceps, calves', 'quads, glutes, adductors, core') # 4 day split, muscle group focus
        return split
    
    @staticmethod
    def create_plan(trainingfrequency, muscles_to_prioritize, experiencelevel, gender, split):
        # Static method to create a workout plan based on the user's training frequency, prioritized muscles, and experience level
        # The method uses the provided split to determine the workout plan
        # The plan and detailed plan are returned as a tuple

        # If the user trains once a week, only type of workout is possible
        if trainingfrequency== 1:
            plan = split[0]
            detailed_plan={'day_1': 'chest, chest, quads, upper back, hamstrings, lats, glutes, side delts, calves, triceps, biceps, abs'}

        # If the user trains twice a week
        elif trainingfrequency== 2:
            plan = split[1]
            detailed_plan={'day_1': 'chest, upper back, chest, lats, side delts, tricpes, biceps', 'day_2': 'quads, hamstrings, glutes, quads, glutes, calves, abs'}

        # If the user trains three times a week
        elif trainingfrequency== 3:
            if any(m in muscles_to_prioritize for m in ['triceps', 'biceps']) or experiencelevel in ['advanced', 'elite', 'intermediate']:
                plan= split[4]
                detailed_plan={'day_1': 'biceps, biceps, chest, chest, front delts, side delts', 'day_2': 'triceps, tricpes, upper back, lats, lats, rear delts', 'day_3': 'quads, hamstrings, glutes, quads, glutes, calves, abs'}
            else:
                plan = split[2]
                detailed_plan={'day_1': 'chest, chest, front delts, side delts, triceps, triceps', 'day_2': 'upper back, lats, lats, biceps, biceps', 'day_3': 'quads, hamstrings, glutes, quads, glutes, calves, abs'}

        # If the user trains four times a week, there are three possible plans, based on the user's experience level and prioritized muscles
        elif trainingfrequency== 4:
            if any(m in muscles_to_prioritize for m in ['triceps', 'biceps', 'chest', 'upper back', 'lats', 'calves']) or experiencelevel in ['advanced', 'elite', 'intermediate']:
                plan= split[11]
                detailed_plan={'day_1': 'chest, chest, chest, front delts, side delts', 'day_2': 'upper back, lats, lats, rear delts, abs, abs', 'day_3': 'calves, triceps, biceps, triceps, biceps, forearms', 'day_4': 'quads, hamstrings, glutes, quads, glutes, adductors'}
            elif any(m in muscles_to_prioritize for m in ['front delts', 'side delts', 'quads']):
                plan=split[14]
                detailed_plan={'day_1': 'chest, chest, chest, triceps, triceps, foreamrs, foreamrs', 'day_2': 'side delts, front delts, hamstrings, front delts, hamstrings, side delts'}
            else:
                plan = split[10]
                detailed_plan={'day_1': 'chest, upper back, chest, lats, side delts, tricpes, biceps', 'day_2': 'quads, hamstrings, glutes, quads, adductors, calves, abs', 'day_3': 'lats, chest, upper back, chest, side delts, biceps, triceps', 'day_4': 'hamstrings, glutes, quads, hamstrings, glutes, calves, abs'} 
       
        # If the user trains five times a week, two possible plans are available, based on the user's experience level and prioritized muscles
        elif trainingfrequency== 5:
            if any(m in muscles_to_prioritize for m in ['triceps', 'biceps', 'chest', 'upper back', 'lats', 'front delts', 'side delts', 'rear delts']) or gender=='male':
                plan= split[3]
                detailed_plan={'day_1': 'chest, chest, chest, front delts, side delts', 'day_2': 'upper back, lats, lats, abs, abs', 'day_3': 'rear delts, front delts, side delts, rear delts, side delts, front delts', 'day_4': 'triceps, biceps, triceps. biceps, forearms, forearms', 'day_4': 'quads, hamstrings, glutes, quads, glutes, adductors', 'day_5': 'quads, hamstrings, glutes, quads, hamstrings, glutes, calves'}
            else:
                plan = split[5]
                detailed_plan={'day_1': 'chest, chest, front delts, side delts, abs, abs', 'day_2': 'quads, adductors, calves, quads, calves, glutes', 'day_3': 'upper back, lats, lats, forearms, abs, abs', 'day_4': 'triceps, biceps, triceps, biceps, forearms, forearms', 'day_5': 'hamstrings, glutes, hamstrings, glutes, calves, abs'}
        
        # If the user trains six times a week, there are three possible plans, based on the user's experience level and prioritized muscles
        elif trainingfrequency== 6:
            if any(m in muscles_to_prioritize for m in ['triceps', 'biceps']) or experiencelevel=='intermediate':
                plan= split[12]
                detailed_plan={'day_1': 'biceps, biceps, chest, chest, front delts, side delts', 'day_2': 'triceps, tricpes, upper back, lats, lats, rear delts', 'day_3': 'quads, hamstrings, glutes, quads, glutes, calves, abs','day_4': 'biceps, biceps, chest, chest, side delts, side delts', 'day_5': 'triceps, tricpes, upper back, upper back, lats, rear delts', 'day_6': 'hamstrings, quads, glutes, quads, glutes, calves, abs'}
            elif experiencelevel in ['beginner', 'novice'] or any(m in muscles_to_prioritize for m in ['lats', 'upper back', 'chest']):
                plan = split[13]
                detailed_plan={'day_1': 'chest, chest, front delts, side delts, triceps, triceps', 'day_2': 'upper back, lats, lats, biceps, biceps', 'day_3': 'quads, hamstrings, glutes, quads, glutes, calves, abs', 'day_4': 'chest, chest, side delts, side delts, triceps, triceps', 'day_5': 'upper back, lats, upper back, biceps, biceps', 'day_6': 'hamstrings, quads, glutes, quads, hamstrings, calves, abs'}
            else:
                plan = split[6] 
                detailed_plan={'day_1': 'chest, chest, chest, forearms, forearms','day_2':'quads, glutes, quads,glutes, calves', 'day_3': 'side delts, triceps, biceps, rear delts, triceps, biceps, front delts', 'day_4': 'hamstrings, glutes, hamstrings, glutes, calves, abs', 'day_5': 'upper back, lats, lats, abs, abs, forearms', 'day_6': 'quads, adductors, calves, quads, adductors, glutes'}
        
        # If the user trains seven times a week, one possible plan is available, based on the user's experience level and prioritized muscles
        elif trainingfrequency== 7:
            plan = split[7] 
            detailed_plan={'day_1': 'chest, quads, biceps, glutes, side delts, forearms', 'day_2':'triceps, triceps, upper back, lats, lats, rear delts', 'day_3':'hamstrings, glutes, hamstrings, glutes, abs', 'day_4':'biceps, biceps, chest, chest, chest', 'day_5':'upper back, lats, front delts, side delts, lats, rear delts', 'day_6':'quads, glutes, quads, gutes, glutes', 'day_7':'calves, calves, abs, abs'}
        return plan, detailed_plan
        
    @staticmethod
    def extract_muscles_from_detailed_plan(detailed_plan, training_frequency):
        # Static method to extract the muscles to be trained from the detailed plan
        # The method iterates over the days in the plan, splits the muscles for each day, and appends them to a list
        # The list of muscles to be trained is returned
        muscles_to_train = []
        for day in range(1, training_frequency + 1):
            muscles_for_day = detailed_plan[f'day_{day}'].split(', ')
            muscles_to_train.append(muscles_for_day)
        return muscles_to_train
      
    def reorder_plan_based_on_priority(self, detailed_plan, muscles_to_prioritize, muscles_to_train):
        # Method to reorder the workout plan based on the user's prioritized muscles
        reordered_plan = {}
        for day, muscles in detailed_plan.items():
            daily_muscles = muscles.split(', ')
            # Custom comparison function for prioritizing muscles
            compare_func = lambda x, y: (x in muscles_to_prioritize) and (y not in muscles_to_prioritize)
            prioritized_muscles = self.merge_sort(daily_muscles, compare=compare_func)
            reordered_plan[day] = ', '.join(prioritized_muscles)
        return reordered_plan

    from flattened_tree import tree

    def parse_tree_to_exercises(self, tree):
        # Method to parse a tree of exercises into a dictionary
        # The dictionary is structured as {muscle_group: {division: [(exercise_name, rating), ...], ...}, ...}
        # The tree is assumed to have a specific structure, with muscle groups at level 3, divisions at level 4, exercises at level 5, and ratings at level 6

        exercise_map = {}
        muscle_group, division = None, None

        for node in tree:
            # Skip certain nodes
            if node['name'] in ['progression program', 'Pushups', 'Pull ups', 'Squats', 'Leg Raises', 'Bridges', 'Skills']:
                continue

            # Handle muscle group nodes
            if node['level'] == 3:
                muscle_group = node['name']
                exercise_map[muscle_group] = {}

            # Handle division nodes
            elif node['level'] == 4 and muscle_group:
                division = node['name']
                exercise_map[muscle_group][division] = []

            # Handle exercise nodes
            elif node['level'] == 5 and muscle_group and division:
                exercise_name = node['name']

            # Handle rating nodes
            elif node['level'] == 6 and muscle_group and division and exercise_name:
                try:
                    rating = float(node['name'])
                    exercise_map[muscle_group][division].append((exercise_name, rating))
                except ValueError:
                    # Skip if rating is not a valid number
                    continue
        return exercise_map


    def generate_workout_plan(self, detailed_plan, exercise_map):
        # Method to generate a workout plan based on a detailed plan and an exercise map
        # The workout plan is a dictionary where each key is a day and each value is a list of exercises for that day
        # The method also keeps track of used exercises to avoid repetition

        # Initialize the workout plan and used exercises
        workout_plan = {}
        used_exercises = {category: [] for category in exercise_map.keys()}

        # Iterate over each day in the detailed plan
        for day, muscle_groups in detailed_plan.items():
            day_plan = []
            # Iterate over each muscle group for the day
            for muscle_group in muscle_groups.split(', '):
                highest_rated_exercise = None
                highest_rating = -1
                # Iterate over each category and subgroup in the exercise map
                for category, subgroups in exercise_map.items():
                    for subgroup, exercises in subgroups.items():
                        # If the muscle group is in the subgroup and there are exercises
                        if muscle_group in subgroup and exercises:
                            # Iterate over each exercise and its rating
                            for exercise, rating in exercises:
                                # If the rating is higher than the current highest rating and the exercise has not been used
                                if rating > highest_rating and exercise not in used_exercises[category]:
                                    # Update the highest rated exercise and its rating
                                    highest_rated_exercise = exercise
                                    highest_rating = rating
                # If a highest rated exercise was found
                if highest_rated_exercise:
                    # Add the exercise to the day plan and mark it as used
                    day_plan.append(highest_rated_exercise)
                    for category, subgroups in exercise_map.items():
                        if muscle_group in subgroups:
                            used_exercises[category].append(highest_rated_exercise)
                            break
            
            # Add the day plan to the workout plan
            workout_plan[f'{day}'] = day_plan

        # Return the workout plan
        return workout_plan


    def find_muscle_and_division(self, exercise_name):
        # Method to find the muscle group and division for a given exercise
        # The method iterates over the exercise map and returns the muscle group and division if the exercise is found
        # If the exercise is not found, the method returns None for both the muscle group and division
        for muscle_group, divisions in self.exercise_map.items():
            for division, exercises in divisions.items():
                for ex_name, _ in exercises:
                    if ex_name == exercise_name:
                        return muscle_group, division
        return None, None

    def map_muscle_groups_to_divisions(self, detailed_plan, muscle_divisions):
        # Method to map muscle groups to divisions in a detailed plan
        # The method iterates over the detailed plan and replaces each muscle group with a specific division from the muscle divisions
        # The method uses a division tracker to ensure that divisions are used evenly for each muscle group
        # The updated plan is returned
        updated_plan = {}
        for day, muscle_groups in detailed_plan.items():
            updated_muscle_groups = []
            division_tracker = {}  

            for muscle_group in muscle_groups.split(', '):
                if muscle_group in muscle_divisions:
                    if muscle_group not in division_tracker:
                        division_tracker[muscle_group] = 0
                    
                    division_index = division_tracker[muscle_group] % len(muscle_divisions[muscle_group])
                    division_tracker[muscle_group] += 1

                    specific_division = muscle_divisions[muscle_group][division_index]
                    updated_muscle_groups.append(specific_division)
                else:
                    updated_muscle_groups.append(muscle_group)

            updated_plan[day] = ', '.join(updated_muscle_groups)
        return updated_plan
    
    plan=[]

    def map_exercise_details(self, exercise_name):
        # Method to map exercise details for a given exercise name
        # The method iterates over the list of exercises and checks if the name matches the given exercise name
        # If a match is found, a dictionary with the exercise details is created and appended to the plan
        # The dictionary is also returned
        # If no match is found, the method returns None

        for exercise in exercises:
            if exercise['name'] == exercise_name:
                result = {
                    'icon': exercise['icon'],
                    'text': f"[size=20][font=Poppins-Bold.ttf][color=#FFFFFF]{exercise['name']}[/color][/font][/size]",
                    'secondary_text': f"[size=15][font=Poppins-Regular.ttf][color=#FFFFFF]{exercise['type']}[/color][/font][/size]",
                    'image_source': exercise['icon']
                }
                self.plan=list(self.plan)
                self.plan.append(result)
                return result
        return None
    
    def rewrite_workout_plan(self, workout_plan):
        # Method to rewrite a workout plan with detailed exercise information
        # The method iterates over each day in the workout plan and maps each exercise to its details
        # The detailed exercises are then added to the generated plan for the corresponding day
        # The generated plan is returned
        generated_plan = {}
        for day, plan_exercises in workout_plan.items():
            detailed_exercises = [self.map_exercise_details(exercise) for exercise in plan_exercises]
            generated_plan[day] = detailed_exercises
        return generated_plan
    
    
    formatted_plan = {}

    def format_workout_plan(self, workout_plan):
        # Method to format a workout plan with detailed exercise information
        # The method iterates over each day in the workout plan and extracts the list of exercises
        # For each exercise, the method finds the exercise details and adds them to the day's exercises
        # The method also keeps track of the muscles worked on each day
        # The formatted plan is returned

        formatted_plan = {}
        for day in range(1, self.trainingfrequency + 1):
            day_key = f'day_{day}'
            if day_key in workout_plan:
                exercises_list = workout_plan[day_key]
                day_exercises = []
                muscles_worked = set()

                for name in exercises_list:
                    exercise_detail = next((ex for ex in exercises if ex['name'] == name), None)
                    if exercise_detail:
                        day_exercises.append({
                            'name': name,
                            'type': exercise_detail['type'],
                            'icon': exercise_detail['icon']
                        })
                        muscles = exercise_detail['primary_muscle'].split(',') + exercise_detail.get('secondary_muscles', '').split(',')
                        muscles_worked.update(muscle.strip() for muscle in muscles if muscle)

                formatted_plan[day_key] = {
                    'muscles': list(muscles_worked),
                    'exercises': day_exercises
                }

        self.formatted_plan = formatted_plan
        return formatted_plan

    def generate_plan(self):
        # Method to generate a workout plan based on user details and preferences
        # The method follows several steps to create a personalized workout plan

        # Step 1: Get user details
        trainingfrequency, experiencelevel, gender, prioritizemusclegroups = self.get_user_details()

        # Step 2: Divide prioritized muscle groups
        self.muscles_to_prioritize = self.divide_muscles_to_prioritize(prioritizemusclegroups)

        # Step 3: Create a workout split based on the user's training frequency
        split = self.create_split()

        # Step 4: Create a detailed plan based on the user's training frequency, prioritized muscles, experience level, and workout split
        self.plan, self.detailed_plan = self.create_plan(trainingfrequency, self.muscles_to_prioritize, experiencelevel,gender, split)

        # Step 5: Extract the muscles to be trained from the detailed plan
        self.muscles_to_train = self.extract_muscles_from_detailed_plan(self.detailed_plan, trainingfrequency)

        # Step 6: Reorder the plan based on the user's prioritized muscles
        self.reordered_plan = self.reorder_plan_based_on_priority(self.detailed_plan, self.muscles_to_prioritize, trainingfrequency)

        # Step 7: Map muscle groups to divisions in the detailed plan
        self.detailed_plan = self.map_muscle_groups_to_divisions(self.detailed_plan, self.muscle_divisions)

        # Step 8: Parse the exercise tree to create an exercise map
        self.exercise_map = self.parse_tree_to_exercises(self.tree)

        # Step 9: Generate a workout plan based on the detailed plan and exercise map
        self.workout_plan = self.generate_workout_plan(self.detailed_plan, self.exercise_map)

        # Step 10: Format the workout plan for display
        self.formatted_plan = self.format_workout_plan(self.workout_plan)

        # Step 11: Rewrite the workout plan with detailed exercise information
        self.generated_plan = self.rewrite_workout_plan(self.workout_plan)
        
        self.populate_all_exercises()
        print(self.formatted_plan)
    def on_enter(self, *args):
        # Method that is called when the screen is entered
        # It generates a workout plan and populates the exercises for the day

        self.generate_plan()
        self.populate_exercises()
        
    def remove_item_handler(self, instance, value):
        # Method to handle the removal of an item from the exercise list
        # It removes the item from the list widget and updates the exercises_per_day dictionary

        # Find the index of the item to remove
        index_to_remove = None
        for i, item in enumerate(self.ids.exercise_list.data):
            if item['text'] == value['text']:  # Adjust this condition based on your data structure
                index_to_remove = i
                break        
        # Remove the item from the RecycleView data
        if index_to_remove is not None:
            self.ids.exercise_list.data.pop(index_to_remove)

        if self.day in self.exercises_per_day:
            if value in self.exercises_per_day[self.day]:
                self.exercises_per_day[self.day].remove(value)   

    day = 1
    exercises_per_day = {}
    def populate_exercises(self, _=None):
        # Method to update the exercise list widget for the current day
        self.ids.day_plan.text = f"DAY {self.day}"
        self.ids.exercise_list.data = []  # Clear the RecycleView data
        if self.day in self.exercises_per_day:
            for item in self.exercises_per_day[self.day]:
                # Add the item to the RecycleView data
                self.ids.exercise_list.data.append(item)


    def populate_all_exercises(self):
        # Method to populate exercises for each day in the plan
        for day in range(1, self.trainingfrequency + 1):
            self.populate_exercises_for_day(day, self.formatted_plan[f'day_{day}']['exercises'])
            
    def populate_exercises_for_day(self, day, exercises):
        # Method to create SwipeToDeleteItem for each exercise and add it to exercises_per_day
        exercise_items = []
        for exercise in exercises:
            item = {
                'text': f"[size=18][font=Poppins-Bold.ttf][color=#FFFFFF]{exercise['name']}[/color][/font][/size]",
                'secondary_text': f"[size=12][font=Poppins-Regular.ttf][color=#FFFFFF]2-3 sets | 6-12 reps [/color][/font][/size]",
                'image_source': exercise['icon'],
                # Add any other properties you need
            }
            exercise_items.append(item)
        self.exercises_per_day[day] = exercise_items
    already_selected_exercises = set()
    # Merge sort function
    def merge_sort(self, arr, compare=lambda x, y: x < y):
        # Custom merge sort that uses a comparison function
        if len(arr) > 1:
            mid = len(arr) // 2
            L = arr[:mid]
            R = arr[mid:]

            self.merge_sort(L, compare)
            self.merge_sort(R, compare)

            i = j = k = 0

            while i < len(L) and j < len(R):
                if compare(L[i], R[j]):
                    arr[k] = L[i]
                    i += 1
                else:
                    arr[k] = R[j]
                    j += 1
                k += 1

            while i < len(L):
                arr[k] = L[i]
                i += 1
                k += 1

            while j < len(R):
                arr[k] = R[j]
                j += 1
                k += 1

        return arr


    # Function to handle switching exercises
    def switch_exercise_handler(self, item):
        # Extract the exercise name from the markup text
        current_exercise = re.search(r'\[color=#FFFFFF](.*?)\[/color]', item.text).group(1)

        # Find the muscle group and division of the current exercise
        muscle_group, division = self.find_muscle_and_division(current_exercise)

        if division:
            # Get the exercises for the current muscle group and division
            division_exercises = self.exercise_map[muscle_group][division]
            # Sort the exercises by rating in descending order
            sorted_exercises = self.merge_sort(division_exercises, compare=lambda x, y: x[1] > y[1])

            # If all exercises have been selected once, clear the set
            if len(self.already_selected_exercises) == len(sorted_exercises):
                self.already_selected_exercises.clear()

            # Find the next highest-rated exercise that is not the current exercise and has not been selected before
            for next_exercise in sorted_exercises:
                if next_exercise[0] != current_exercise and next_exercise[0] not in self.already_selected_exercises:
                    new_exercise = next_exercise[0]
                    # Add the new exercise to the set of selected exercises
                    self.already_selected_exercises.add(new_exercise)
                    # Get the details of the new exercise
                    new_exercise_details = self.map_exercise_details(new_exercise)

                    # Update the UI with the new exercise details
                    item.text = new_exercise_details['text']
                    item.secondary_text = new_exercise_details['secondary_text']
                    item.image_source = new_exercise_details['icon']
                    return


    def save_plan(self):
        MDApp.get_running_app().root.get_screen('select_workout').on_generate_plan(generated_plan=self.formatted_plan)
      
    def switch_days_left(self):
        # Method to switch to the previous day in the workout plan
        # If the current day is the first day, the method disables the left arrow button
        # Otherwise, the method enables the left arrow button and decreases the day by 1
        # The method then populates the exercises for the new day
        
        self.ids.arrow_right.opacity = 1
        self.ids.arrow_right.disabled = False

        if self.day == 1:
            self.ids.arrow_left.opacity = 0.3
            self.ids.arrow_left.disabled = True
        else:
            self.ids.arrow_left.opacity = 1
            self.ids.arrow_left.disabled = False
            self.day -= 1
        self.populate_exercises()

    def switch_days_right(self):
        # Method to switch to the next day in the workout plan
        # If the current day is the last day, the method disables the right arrow button
        # Otherwise, the method enables the right arrow button and increases the day by 1
        # The method then populates the exercises for the new day

        self.ids.arrow_left.opacity = 1
        self.ids.arrow_left.disabled = False

        if self.day == self.trainingfrequency:
            self.ids.arrow_right.opacity = 0.3
            self.ids.arrow_right.disabled = True
        else:
            self.ids.arrow_right.opacity = 1
            self.ids.arrow_right.disabled = False
            self.day += 1
        self.populate_exercises()
class InputTrainingStyle(Screen):
    # Class representing the screen for inputting user's training style
    invalidtrainingstyle = False
    trainingstyle = ""

    def border_on_click(self, pressed_hypertrophy, pressed_powerlifting, pressed_powerbuilding):
        # Method to handle the selection of training style.
        # Depending on which button is pressed, the training style is set and the border position is updated.
        if pressed_hypertrophy:
            self.trainingstyle = "Hypertrophy"
            self.ids.border.pos_hint = {"center_x": 0.498, "center_y": 0.68}
        elif pressed_powerlifting:
            self.trainingstyle = "Powerlifting"
            self.ids.border.pos_hint = {"center_x": 0.498, "center_y": 0.53}
        elif pressed_powerbuilding:
            self.trainingstyle = "Powerbuilding"
            self.ids.border.pos_hint = {"center_x": 0.498, "center_y": 0.38}

    def on_continue(self):
        # Method to handle the continue action.
        # If a training style is selected, it is updated in the database.
        # If not, a validation message is displayed.
        if self.trainingstyle != "":
            user_id=self.manager.get_screen('initialpage').user_id
            user = UserManager.get_user(user_id)
            user.update_training_style(self.trainingstyle)
            self.invalidtrainingstyle = False
        else:
            self.ids.validtrainingstyle.text="Please select an option"
            self.invalidtrainingstyle = True
class InputTrainingFrequency(Screen):
    # Class representing the screen for inputting user's training frequency
    invalidtrainingfrequency = False
    trainingfrequency = ""

    def border_on_click(self, *args):
        # Create a list of tuples, where each tuple contains the frequency and center_y value
        frequencies_and_center_ys = [
            ("1x week", 0.68),
            ("2x week", 0.61),
            ("3x week", 0.54),
            ("4x week", 0.47),
            ("5x week", 0.4),
            ("6x week", 0.33),
            ("7x week", 0.26),
        ]

        # Use the enumerate function to loop over the list and the arguments at the same time
        for pressed, (frequency, center_y) in zip(args, frequencies_and_center_ys):
            # If the button is pressed, set the trainingfrequency and pos_hint
            if pressed:
                self.trainingfrequency = frequency
                self.ids.border.pos_hint = {"center_x": 0.498, "center_y": center_y}
                break
            
    def on_continue(self):
        # Method to handle the continue action.
        # If a training frequency is selected, it is updated in the database.
        # If not, a validation message is displayed.
        if self.trainingfrequency != "":
            self.invalidtrainingfrequency = False
            try:
                user_id = self.manager.get_screen('initialpage').user_id
            except AttributeError:
                user_id= '262efaa4-1a2d-484e-8de8-32966c8a6a82'
            user = UserManager.get_user(user_id)
            user.update_training_frequency(self.trainingfrequency)
        else:
            self.ids.validtrainingfrequency.text="Please select an option"
            self.invalidtrainingfrequency = True
class PrioritizeMuscleGroups(Screen): #this will be displayed after the InputTrainingFrequency screen, and it takes the User's Prioritized Muscle Groups as input
    def __init__(self, **kwargs):
        super(PrioritizeMuscleGroups, self).__init__(**kwargs)
        self.rectangles = []
    
    rect_id= ['rectangle_chest', 'rectangle_shoulders', 'rectangle_upperback', 'rectangle_lats', 'rectangle_triceps', 'rectangle_biceps', 'rectangle_quads', 'rectangle_glutes', 'rectangle_hamstrings', 'rectangle_calves', 'rectangle_abs', 'rectangle_forearms']
    general_clicked = False
    selected_rectangles = []
    invalidmusclegroups= False
    def update_borders(self):
        # Determine the selected rectangles
        self.selected_rectangles = [rect for rect in self.rectangles if rect.selected]
        
        # Position the borders based on the selected rectangles
        for index, border_id in enumerate(['border_1', 'border_2', 'border_3']):
            if index < len(self.selected_rectangles):
                self.ids[border_id].pos_hint = self.selected_rectangles[index].pos_hint
            else:
                self.ids[border_id].pos_hint = {"center_x": 0.27, "center_y": 2}  # Off-screen

    def border_on_click(self, rectangle, is_general_option=False):
        if is_general_option:
            # The general option was clicked
            self.general_clicked = True
            # Deselect all muscle groups and clear borders
            for rect in self.rectangles:
                rect.selected = False
                rect.state = 'normal'
            for border_id in ['border_1', 'border_2', 'border_3']:
                self.ids[border_id].pos_hint = {"center_x": 0.27, "center_y": 2}
                
            # Set the border around the general option
            self.ids.border_general.pos_hint = {"center_x": 0.5, "center_y": 0.26}
            self.invalidmusclegroups= False
        else:
            # A specific muscle group was clicked
            self.general_clicked = False
            # Normal muscle group selection handling
            self.ids.border_general.pos_hint = {"center_x": 0.5, "center_y": 2}
            if rectangle.selected:
                # If the rectangle is already selected, just deselect it
                rectangle.selected = False
                rectangle.state = 'normal'
                self.update_borders()
                return
            
            # Get all selected rectangles
            self.selected_rectangles = [rect for rect in self.rectangles if rect.selected]

            # If there are already 3 selected rectangles, deselect the earliest one
            if len(self.selected_rectangles) >= 3:
                earliest_selected = self.selected_rectangles[0]
                earliest_selected.state = 'normal'  # This will automatically update its 'selected' property
                earliest_selected.selected = False

            # Select the clicked rectangle
            rectangle.selected = True
            rectangle.state = 'down'  # This line may not be needed if 'selected' property is bound to the state

            # Update borders
            self.update_borders()
            
    def on_enter(self):
        # Keep a reference to all SelectableRectangles
        self.rectangles = [self.ids[rect_id] for rect_id in self.rect_id ] 
        self.update_borders()
        
    def output_selected_muscle_groups(self):
        try:
            user_id = self.manager.get_screen('initialpage').user_id
        except AttributeError:
            user_id= '262efaa4-1a2d-484e-8de8-32966c8a6a82'
        user = UserManager.get_user(user_id)
        
        if self.general_clicked:
            selected_muscle_groups=("The user has selected to not prioritize any muscle groups.")
        else:
            # Extract the names of the selected muscle groups by removing 'rectangle_' from the IDs
            selected_muscle_groups = [rect_id.split('rectangle_')[1] for rect_id in self.rect_id if self.ids[rect_id].selected]
            
        if len(self.selected_rectangles) == 0 and self.general_clicked == False:
            self.ids.validmusclegroups.text="Please select at least one muscle group"
        else:
            if self.general_clicked:
                user.update_prioritized_muscle_groups(selected_muscle_groups)
            else:
                muscle_groups_str = ','.join(selected_muscle_groups)  # Joins list into a comma-separated string
                user.update_prioritized_muscle_groups(muscle_groups_str)
        
    def changescreen(self):
        self.output_selected_muscle_groups()
        if self.invalidmusclegroups==False:
            self.manager.current= "generate_plan"
        else:
            self.manager.current= "prioritizemusclegroups"    
class ChatBotScreen(Screen):
    def __init__ (self, **kwargs):
        super(ChatBotScreen, self).__init__(**kwargs)
    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.initial_prompt()

    def initial_prompt(self):
        # Initialize the chatbot with the OpenAI API key and other parameters
        # Initialize the chat history and the initial prompt
        # Get the initial response from the chatbot and add it to the chat UI

        self.chat = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            streaming=False,  
            temperature=0.5
        )
        self.chat_history = []
        self.initial_prompt ="Your role is to be a personal Fitness Coach, ready to support me on my health and fitness journey. As an expert in nutrition and exercise, you're here to offer me the best advice on creating a balanced diet, mastering exercise techniques, and maintaining a healthy lifestyle. Whether you need guidance on meal planning, tips for staying motivated, or assistance with workout routines. You need to act enthusiastic, supportive and as a friend, and you need to be able to answer any questions I have. This is my data:'gender: male, age: 18, height: 1.75, weight: 65.00, experience_level: Beginner, 6 months to 1.5 years of lifting, bodyfat: 13.40, activity_level: Moderately Active, exercise 4-5 times a week, goal: Gain Weight, calories: 2566' Answer this with just 'Hello! I'm your personal Fitness Coach. How can I help you today?' and nothing else, and then I will ask you other questions."
        self.memory = ConversationBufferMemory()
        self.memory.chat_memory.add_user_message(self.initial_prompt)
        initial_response = self.get_response(self.initial_prompt)
        
        self.ids.chat_list.add_widget(Response(text=initial_response, size_hint_x=.75))
        return 
    def get_response(self, user_input):
        # Load the chat history
        # Add the user input to the chat memory
        # Get the response from the chatbot and add it to the chat memory
        # Return the full response
        history = self.memory.load_memory_variables({})['history']
        full_input = user_input
        self.memory.chat_memory.add_user_message(user_input)
        full_response = ""
        for response in self.chat.stream([HumanMessage(content=history), HumanMessage(content=full_input)]):
            full_response += response.content.replace('\n', ' ')
        self.memory.chat_memory.add_ai_message(full_response)
        return full_response

    def get_response_thread(self, user_input):
        # Get the full response from the chatbot
        # Add the response to the chat history
        # Schedule the UI update to be run on the main thread
        full_response = self.get_response(user_input)
        self.chat_history.append(('e87601ef-eda4-4e3e-bca5-b6bb32bc483f', full_response, 'AI'))
        Clock.schedule_once(lambda dt: self.update_chat_ui(full_response))
        # Save to database here if desired, or after certain intervals/conditions

    def send(self):
        # Check if the text input is not empty
        if self.ids.text_input != "":
            # Get the text from the input field
            self.value = self.ids.text_input.text
            # Define a mapping of message length to size
            size_map = {range(0, 3): .15, range(3, 6): .22, range(6, 9): .28, range(9, 12): .34,
                        range(12, 15): .40, range(15, 18): .46, range(18, 21): .52, range(21, 24): .58,
                        range(24, 27): .64, range(27, 30): .70, range(30, 1000000): .77}
            # Determine the size of the message based on its length
            self.size = (next((size for range_, size in size_map.items() if len(self.value) in range_), .77), self.size[1])            
            # Determine the alignment of the message based on its length
            self.halign = "center" if len(self.value) < 30 else "left"
            # Get the status label
            self.status_label = self.ids.status
            # Add the message to the chat UI
            self.ids.chat_list.add_widget(Command(text=self.value, size_hint_x=self.size[0], halign=self.halign))
            # Update the status label to "Typing..."
            self.status_label.text = "Typing..." 
            # Start a new thread to get the response from the chatbot
            threading.Thread(target=self.get_response_thread, args=(self.value,)).start()
            # Clear the text input
            self.ids.text_input.text = ""
            # Add the message to the chat history
            self.chat_history.append(('e87601ef-eda4-4e3e-bca5-b6bb32bc483f', self.value, 'Human'))

    def rebuild_chat_history(self):
        # Get the user ID
        user_id = 'e87601ef-eda4-4e3e-bca5-b6bb32bc483f'  # Or dynamically set this
        # Get the chat messages from the database
        chat_messages = db_manager.get_chats_by_user_id(user_id)
        # Iterate over the chat messages
        for message_tuple in chat_messages:  # Iterate in the original order
            # Unpack the tuple
            chat_id, user_id, text, timestamp, sender = message_tuple
            # Depending on the sender, use different UI elements
            if sender == 'AI':
                # Display the message as an AI response
                self.ids.chat_list.add_widget(Response(text=text, size_hint_x=.75))
            else:
                # Display the message as a user command
                self.ids.chat_list.add_widget(Command(text=text, size_hint_x=.75))

    def update_chat_ui(self, response_content):
        # Add the response to the chat UI
        self.ids.chat_list.add_widget(Response(text=response_content, size_hint_x=.75))
        # Update the status back to "Online"
        self.status_label.text = "Online"  

    def save_to_database(self):
        # Iterate over the chat history
        for message in self.chat_history:
            # Unpack the message
            user_id, text, sender = message

            # Save the message to the database
            db_manager.insert_chat(user_id=user_id, message=text, sender=sender)

        # Clear the history after saving
        self.chat_history.clear()  
#------------------------------------------------------------------------------------------------------------------------------------------   
class NavBar(CommonElevationBehavior, MDFloatLayout):
    pass
class SavedFoodListItem(TwoLineListItem):
    rv_card_x: 0.5
    _right_container = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize and add the right container here
        self._right_container = MDBoxLayout(adaptive_size=True, pos_hint={'center_y': 0.5})
        self.add_widget(self._right_container)
        self._txt_left_pad = dp(16)  # Left padding
        self._txt_top_pad = dp(120)    # Top padding
        self._txt_bot_pad = dp(8)    # Bottom padding
        self._txt_right_pad = dp(48)
        self.bind(on_release=self.item_clicked)

    def item_clicked(self, instance):
        # This method will be called when an item is clicked
        original_data = instance.original_data
        index = original_data['index']  # Get the index of the clicked item
        MDApp.get_running_app().root.get_screen('food_search').food_details(original_data, index)
        
    def on_touch_down(self, touch):
        if self.ids.deleteiconright.collide_point(*touch.pos):
            MDApp.get_running_app().root.get_screen('food_search').remove_food(self.original_data)
            return self.ids.deleteiconright.on_touch_down(touch)
        return super().on_touch_down(touch) 
class RoundedRectProgressBar(Widget):
    progress = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_graphics, size=self.update_graphics, progress=self.update_graphics)

        self.label = Label(text="2300/4522", font_size=15, font_name="Poppins-Bold", color=(1, 1, 1, 1))
        self.add_widget(self.label)
        self.update_graphics()

    def update_graphics(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.26, 0.26, 0.26, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[(20, 20)])

        self.canvas.after.clear()
        with self.canvas.after:
            # Begin stencil operation
            StencilPush()
            # PHASE 1: Draw the mask (progress part)
            Color(0, 0, 0, 0)  # Invisible color, but still affects stencil buffer
            RoundedRectangle(pos=self.pos, size=(self.width * self.progress / 100, self.height), radius=[(20, 20)])

            StencilUse()
            # PHASE 2: Draw the actual progress bar within the mask
            Color(108/255,140/255,194/255, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[(20, 20)])
            
            StencilUnUse()
            # PHASE 3: Redraw the mask
            RoundedRectangle(pos=self.pos, size=(self.width * self.progress / 100, self.height), radius=[(20, 20)])
            StencilPop()

        # Positioning the label
        self.label.pos = self.pos
        self.label.size = self.size
class SwipeToDeleteItem(MDCardSwipe, EventDispatcher):
    text = StringProperty()
    secondary_text = StringProperty()
    image_source = StringProperty()

    def __init__(self, **kwargs):
        super(SwipeToDeleteItem, self).__init__(**kwargs)
        self.register_event_type('on_switch_exercise')
        self.register_event_type('on_remove_item')
    def on_touch_down(self, touch):
        return super(MDCardSwipe, self).on_touch_down(touch)

    def remove_item(self):
        # Dispatch the on_remove_item event with the current instance
        self.dispatch('on_remove_item', self)

    def on_remove_item(self, instance):
        pass  # Actual handling will be done in the method bound to this event

    def switch_exercise(self):
        self.close_card() 
        self.dispatch('on_switch_exercise', self)

    def on_switch_exercise(self, instance):
        pass  # The actual handling will be done in the method bound to this event.class SwipeToDeleteItem(MDCardSwipe, EventDispatcher):
class DraggableArea(FloatLayout):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.parent.dragging = True
            return True
        return super(DraggableArea, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.parent.dragging:
            return self.parent.on_touch_move(touch)
        return super(DraggableArea, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.parent.dragging:
            self.parent.dragging = False
            return self.parent.on_touch_up(touch)
        return super(DraggableArea, self).on_touch_up(touch)
class DraggablePanel(FloatLayout):
    panel_height = NumericProperty(Window.height)  # Panel height
    panel_top = NumericProperty(Window.height*0.2)  # Starting position (hidden)
    open_position = NumericProperty(Window.height*0.12)
    closed_position = NumericProperty(Window.height)
    dragging = BooleanProperty(False)
    start_hidden = BooleanProperty()
    def __init__(self, **kwargs):
        super(DraggablePanel, self).__init__(**kwargs)
        self.bind(pos=self.update_child_pos)
        # Set the initial position
        if not self.start_hidden:
            self.y = self.open_position - self.height
        else:
            self.y = -500
    def update_child_pos(self, instance, value):
        for child in self.children:
            child.pos = self.pos
    def on_parent(self, widget, parent):
        if self.start_hidden == False:
            self.y = self.open_position - self.height
        else:
            self.y = -500
    def toggle(self):
        target_position = self.open_position - self.height if self.y != self.open_position - self.height else self.closed_position - self.height
        anim = Animation(y=target_position, d=0.3)
        
        def on_complete(animation, widget):
            # Snap to the nearest expected position
            self.y = round(self.y)
            if abs(self.y - (self.open_position - self.height)) < abs(self.y - (self.closed_position - self.height)):
                self.y = self.open_position - self.height
            else:
                self.y = self.closed_position - self.height
        
        anim.bind(on_complete=on_complete)
        anim.start(self)
    def on_touch_move(self, touch):
        if self.dragging:
            # Calculate the difference between the current touch y-position and the previous one
            dy = touch.dy
            new_y = self.y + dy
            if self.open_position - self.height <= new_y <= self.closed_position - self.height:
                self.y = new_y
            return True
        return super(DraggablePanel, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.dragging:
            self.dragging = False
            if self.y < (self.open_position + self.closed_position) / 2 - self.height:
                Animation(y=self.open_position - self.height, d=0.3).start(self)
            else:
                Animation(y=self.closed_position - self.height, d=0.3).start(self)
            return True
        return super(DraggablePanel, self).on_touch_up(touch)
class RoundedRectangle2(Button):
    btn_color = ListProperty([1, 1, 1, 1])  # Default color
    btn_color_down = ListProperty([0.5, 0.5, 0.5, 1])  # Default color when pressed
    radius = ListProperty([15,])  # Default radius for rounded cornersf
class CircularProgressBar(AnchorLayout):
    set_value = NumericProperty(0)
    value = NumericProperty(45)
    bar_color = ListProperty([ .95,.95,.95])
    before_bar_color = ListProperty([.95, .95, .95, .45])
    bar_width = NumericProperty(7)
    active_text=BooleanProperty(True)
    text=StringProperty("0%")
    custom_text = StringProperty("")
    duration = NumericProperty(1)
    counter= 0
    
    def __init__(self, **kwargs):
        super(CircularProgressBar, self).__init__(**kwargs)
        self.start_animation()
    def on_value(self, instance, value):
        Clock.unschedule(self.percent_counter)
        self.start_animation()
    def start_animation(self):
        self.counter = 0
        Clock.unschedule(self.animate)
        Clock.schedule_once(self.animate, 0)
    def animate(self, *args):
        if self.value != 0:
            Clock.schedule_interval(self.percent_counter, self.duration/self.value)
        else:
            self.value = 1
            Clock.schedule_once(self.percent_counter, self.duration)
            
    def percent_counter(self, *args):
        if self.counter < self.value:
            self.counter += 1
            if self.active_text:
                if self.counter != 1:
                    self.text = f"{self.counter}%" 
                else:
                    self.text="0%"
            else:
                self.text = ""
            self.set_value = self.counter
        else:
            Clock.unschedule(self.percent_counter)
class HorizontalProgressBar(BoxLayout):
    value = NumericProperty(0)
    max_value = NumericProperty(100)
    bar_color = ListProperty([.95, .95, .95, 1])
    bar_height = NumericProperty(20)
    label_width = NumericProperty(100)
    text = StringProperty("0g")
    name = StringProperty("")

    def __init__(self, **kwargs):
        super(HorizontalProgressBar, self).__init__(**kwargs)
class ProfileCard(MDFloatLayout, CommonElevationBehavior):
    pass     
class CalendarWidget(BoxLayout):

    def __init__(self, **kwargs):
        super(CalendarWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.top_bar = GridLayout(cols=11, size_hint_y=None, height=50)
        self.add_widget(self.top_bar)
        self.create_top_bar()
        self.calendar_view = ScrollView(size_hint=(1, None), size=(Window.width, Window.height - 50))
        self.add_widget(self.calendar_view)

    def create_top_bar(self):
        # Get the last 10 dates
        today = datetime.now()
        last_11_days = [today - timedelta(days=i) for i in range(11)]
        workout_dates = self.get_workout_dates()  # Retrieve workout dates from storage
        last_11_days.reverse()

        # Create the top bar
        for date in last_11_days:
            date_layout = BoxLayout(orientation='vertical', size_hint=(None, None), size=(38, 50))
            date_label = Label(text=date.strftime(' %d\n%a '), font_name='Poppins-SemiBold.ttf', font_size='10', color=[1, 1, 1, .4], width=self.width, halign='center')
            date_layout.add_widget(date_label)
            # If the date was a workout day, add a dot below the text
            if date.date() in workout_dates:
                with date_layout.canvas.after:
                    Color(1,1,1, .5 )  # Red color for the dot
                    # Place the Ellipse below the text
                    ellipse = Ellipse(size=(5, 5))
                    # Update ellipse reference in layout for access in the callback
                    date_layout.ellipse = ellipse

                # Bind the layout's `pos` and `size` to update the ellipse position
                date_layout.bind(pos=self.update_ellipse_position)
                date_layout.bind(size=self.update_ellipse_position)

            self.top_bar.add_widget(date_layout)

    def update_ellipse_position(self, instance, value):
            # This method updates the position of the Ellipse
            ellipse = instance.ellipse
            ellipse.pos = (instance.x + instance.width / 2 - ellipse.size[0] / 2, instance.y)

    def get_workout_dates(self):
        # Hard-coded workout dates for demonstration purposes
        # In a real app, you would retrieve these from persistent storage
        return {
            datetime.now() - timedelta(days=1),  # Yesterday
            datetime.now() - timedelta(days=3),  # Three days ago
            datetime.now() - timedelta(days=5),  # Five days ago
            datetime.now() - timedelta(days=7)   # A week ago
        }

    # Add more methods to handle calendar view and interactions
class BodyweightGraph(BoxLayout):
    highest_weight= NumericProperty(0)
    lowest_weight= NumericProperty(0)
    elements= NumericProperty(0)
    weight_data = [70, 70.2, 73, 72.5, 71, 74, 71.6,]
    highest_weight= max(weight_data)
    lowest_weight= min(weight_data)
    elements= len(weight_data)
    
    def __init__(self, **kwargs):
        super(BodyweightGraph, self).__init__(**kwargs)
        
    def on_kv_post(self, base_widget):
        self.update_graph(self.ids.weight_graph, self.weight_data )
        return super(BodyweightGraph, self).on_kv_post(base_widget)

    def update_graph(self, graph, weight_data):
        graph.background_color = [0, 0, 0, 0]  
        self.ids.weight_graph.ymin = min(self.weight_data) 
        self.ids.weight_graph.ymax = max(self.weight_data) + .5
        if max(self.weight_data) - min(self.weight_data) < 4:
            self.ids.weight_graph.y_ticks_major = .5
        elif max(self.weight_data) - min(self.weight_data) < 8:
            self.ids.weight_graph.y_ticks_major = 2
        # Interpolating using a spline
        x = np.arange(len(weight_data))
        y = np.array(weight_data)
        spline = UnivariateSpline(x, y, s=1)
        x_smooth = np.linspace(0, len(weight_data) - 1, 300)
        y_smooth = spline(x_smooth)
        
        plot = SmoothLinePlot(color=[182/255, 181/255, 1, 1]) #smooth line plot
        plot.points = [(i, weight) for i, weight in zip(x_smooth, y_smooth)]
        graph.add_plot(plot)       
class BottomNavExampleScreen(MDScreen):
    pass
class HorizontalBar(MDBoxLayout):
    bar_position = NumericProperty(150)
class RoundedButton(Button):
    btn_color = ListProperty([27/255, 24/255, 43/255, 1])  #
    btn_color_down = ListProperty([27/255, 24/255, 43/255, 1])  # Default color when pressed
    radius = ListProperty([15,])  # Default radius for rounded corners
class SelectableRectangle(RoundedButton):
    selected = BooleanProperty(False) 
    # This will keep track of whether the rectangle is selected
class LimitTextInput(TextInput): #class for limiting the number of characters in the text input, beacuse there is no max_length property in kivy
    auto_insert_dot = BooleanProperty(False)
    def keyboard_on_key_up(self, keycode, text):
        if self.readonly and text[1] == "backspace":
            self.readonly = False
            self.do_backspace()

    def insert_dot(self):
        # Only insert a dot if there's more than one character and no dot present
        if len(self.text) > 1 and '.' not in self.text:
            self.text = self.text[:1] + '.' + self.text[1:]
            # Update cursor position immediately
            self.cursor = (self.cursor[0] + 1, self.cursor[1])

    def on_text(self, instance, value):
        # Use Clock to schedule the dot insertion to avoid issues with text property update
        if self.auto_insert_dot:
            Clock.schedule_once(lambda dt: self.insert_dot(), -1)
        # Set read-only state based on length of the text
        self.readonly = len(self.text.strip()) >= 4
class LimitTextInput2(TextInput): #class for limiting the number of characters in the text input, beacuse there is no max_length property in kivy
    def keyboard_on_key_up(self, keycode, text):
        if self.readonly and text[1] == "backspace":
            self.readonly = False
            self.do_backspace()
    def on_text(self, instance, value):
        # Set read-only state based on length of the text
        self.readonly = len(self.text.strip()) >= 12
class FoodListItem(TwoLineListItem):
    rv_card_x: 0.5
    _right_container = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize and add the right container here
        self._right_container = MDBoxLayout(adaptive_size=True, pos_hint={'center_y': 0.5})
        self.add_widget(self._right_container)
        self._txt_left_pad = dp(16)  # Left padding
        self._txt_top_pad = dp(120)    # Top padding
        self._txt_bot_pad = dp(8)    # Bottom padding
        self._txt_right_pad = dp(48)
        self.bind(on_release=self.item_clicked)

    def item_clicked(self, instance):
        # This method will be called when an item is clicked
        original_data = instance.original_data
        MDApp.get_running_app().root.get_screen('food_search').food_details(original_data, index=None)
    def on_touch_down(self, touch):
        if self.ids.plusiconright.collide_point(*touch.pos):
            food_search_screen = MDApp.get_running_app().root.get_screen('food_search')
            food_search_screen.current_unpacked_data = self.original_data
            food_search_screen.saved_foods()
            return self.ids.plusiconright.on_touch_down(touch)
        return super().on_touch_down(touch)
class ListCard(MDCard):
    text = StringProperty()
    icon = StringProperty()
    editable = BooleanProperty(True)
    log= BooleanProperty(True)
    def __init__(self, **kwargs):
        super(ListCard, self).__init__(**kwargs)

    def edit_item(self):
        select_workout_screen= MDApp.get_running_app().root.get_screen('select_workout')
        select_workout_screen.edit_item(self.text)
class ExerciseItemPlan(RecycleDataViewBehavior, TwoLineAvatarListItem):
    icon = StringProperty()
    text = StringProperty()
    secondary_text = StringProperty()
    image_source = StringProperty('')
    exercise_list = []
    instances = []
    current_selection = []
    
    def uncheck(self):
        """Uncheck the checkbox without triggering the on_checkbox_active method."""
        self.ids.cb.unbind(active=self.on_checkbox_active)  # Unbind the method
        self.ids.cb.active = False  # Uncheck the checkbox
        self.ids.cb.bind(active=self.on_checkbox_active)  # Rebind the method

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.empty_plan = False
        self.ids._left_container.clear_widgets()
        self.image_widget = RoundedImage(source=self.image_source)
        self.ids._left_container.add_widget(self.image_widget)
        self.ids.cb.bind(on_release=self.on_checkbox_release)
        self.bind(image_source=self.image_widget.setter('source'))
        self._txt_left_pad = dp(90)  
        self._txt_bot_pad = dp(11)
        self._txt_right_pad = dp(48)
        self.ids.cb.bind(active=self.on_checkbox_active)
        self.image_widget.pos_hint = {'center_x': 0.15, 'center_y': 0.5}
        self.instances.append(self) 

    def set_empty_plan(self):
        self.empty_plan = True

    def refresh_view_attrs(self, rv, index, data):
        """ Catch and handle the view changes """
        self.index = index
        match = re.search(r'\[color=#FFFFFF](.*?)\[/color]', self.text)
        if match is not None:
            exercise_name = match.group(1)
            self.ids.cb.active = data.get('is_checked', False)
        return super(ExerciseItemPlan, self).refresh_view_attrs(rv, index, data)

    def update_image_source(self, instance, value):
        if os.path.isfile(value):
            self.image_source = value
        else:
            self.image_source = 'bardip.png'  # Placeholder image
            Logger.error(f'ExerciseItem: Image file not found at {value}')

    def on_checkbox_release( self, instance, value):
        print("empty plan on_checkbox_release", self.empty_plan)
        return True
    def on_enter(self, *args):
        self.ids.cb.active = self.parent.parent.data[self.index]['is_checked']
        exercise_name = (re.search(r'\[color=#FFFFFF](.*?)\[/color]', self.text)).group(1)
        self.ids.cb.active = exercise_name in MDApp.get_running_app().root.current_selection

    #function to make so that the user can click on the list item to check the checkbox
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.ids.cb.active = not self.ids.cb.active  # Toggle the checkbox
            self.checkbox_clicked = True  # Add this line
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        self.checkbox_clicked = False  
        return super().on_touch_up(touch)

    def on_checkbox_active(self, instance, value):

        # Extract the exercise name from the text
        exercise_name = (re.search(r'\[color=#FFFFFF](.*?)\[/color]', self.text)).group(1)

        # Check if the parent exists and if the exercise name is in the current selection
        if self.parent and self.parent.parent and exercise_name in self.current_selection:
            # If the checkbox is unchecked, remove the exercise name from the current selection
            # and update the 'is_checked' status in the data
            if not value:
                self.current_selection.remove(exercise_name)
                self.parent.parent.data[self.index]['is_checked'] = False
        # If the checkbox is checked and the exercise name is not in the current selection
        elif value and exercise_name not in self.current_selection:
            # Add the exercise name to the current selection
            # and update the 'is_checked' status in the data
            self.current_selection.append(exercise_name)
            if self.parent and self.parent.parent:
                self.parent.parent.data[self.index]['is_checked'] = True
        if self.empty_plan:
            self.current_selection.clear()
            MDApp.get_running_app().root.get_screen('exercise_list').on_checkbox_clicked(added_exercises=[])
            self.empty_plan = False
        else:
            MDApp.get_running_app().root.get_screen('exercise_list').on_checkbox_clicked(self.current_selection)
            # Update the checkbox clicked status in the 'exercise_list' screen"
class RoundedImage(ButtonBehavior, Image):
    def on_error(self, *args):
        self.source = 'bardip.png'  # replace with your actual placeholder image path
        Logger.error('Image: cannot load image at {}'.format(self.source))
class ExerciseItem(TwoLineAvatarListItem):
    icon = StringProperty()
    text = StringProperty()
    secondary_text = StringProperty()
    image_source = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_widget = Image(source=self.image_source)
        self.ids._left_container.clear_widgets()
        self.ids._left_container.add_widget(self.image_widget)
        self.bind(image_source=self.image_widget.setter('source'))
        self._txt_left_pad = dp(100)
        self._txt_bot_pad = dp(7.7)
        self.image_widget.size_hint= (.245,.81)
        self.image_widget.pos_hint = {'center_x': 0.15, 'center_y': 0.5}
        self.bind(on_release=self.item_clicked)

    def update_image_source(self, instance, value):
        if os.path.isfile(value):
            self.image_widget.source = value
        else:
            self.image_widget.source = 'bardip.png'  # Placeholder image
            Logger.error(f'ExerciseItem: Image file not found at {value}')
    def item_clicked(self, instance):
        exercise_name = (re.search(r'\[color=#FFFFFF](.*?)\[/color]', instance.text)).group(1)
        MDApp.get_running_app().root.get_screen('exercise_list').on_item_click(exercise_name)
class SmallerTouchIconButton(MDIconButton):
    touch_scale = NumericProperty(0.5)

    def collide_point(self, x, y):
        # Get the center of the button
        center_x, center_y = self.center_x, self.center_y
        # Calculate the scaled width and height
        width = self.width * self.touch_scale
        height = self.height * self.touch_scale
        # Return whether the point is within the scaled area
        return center_x - width / 3 <= x <= center_x + width / 3 and center_y - height / 3 <= y <= center_y + height / 3
class SetExercisePlan(MDCard, EventDispatcher):
    text = StringProperty()
    image_source = StringProperty()
    sets_text = StringProperty("2 SETS")  # new property for sets text
    reps_text = StringProperty("10 REPS")  
   
    def __init__(self, **kwargs):
        super(SetExercisePlan, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        return super(MDCard, self).on_touch_down(touch)
    
    def change_sets(self, increment=True):
        # Extract the current number of sets
        current_sets = int(self.sets_text.split()[0])
        # Increment or decrement the number of sets based on the icon clicked
        new_sets = current_sets + 1 if increment else max(current_sets - 1, 1)
        # Update the sets_text property
        self.sets_text = f"{new_sets} SETS"
        self.update_reps_and_sets()
    def change_reps(self, increment=True):
        # Extract the current number of reps
        current_reps = int(self.reps_text.split()[0])
        # Increment or decrement the number of reps based on the icon clicked
        new_reps = current_reps + 1 if increment else max(current_reps - 1, 1)
        # Update the reps_text property
        self.reps_text = f"{new_reps} REPS"
        self.update_reps_and_sets()
        
    def update_reps_and_sets(self, move_value=None):
        empty_plan_screen= MDApp.get_running_app().root.get_screen('empty_plan')
        empty_plan_screen.update_sets_and_reps(self.text, self.sets_text, self.reps_text, move_value)

    def move_up(self):
        # Get the parent list
        parent_list = self.parent.parent.data
        # Get the index of the current item
        index = next((i for i, item in enumerate(parent_list) if item['text'] == self.text), None)
        # If the item is not already at the top
        if index is not None and index > 0:
            # Swap the item with the one above it
            parent_list[index], parent_list[index - 1] = parent_list[index - 1], parent_list[index]
            # Update the data in the RecycleView
            self.parent.parent.data = parent_list
            self.update_reps_and_sets(-1)

    def move_down(self):
        # Get the parent list
        parent_list = self.parent.parent.data
        # Get the index of the current item
        index = next((i for i, item in enumerate(parent_list) if item['text'] == self.text), None)
        # If the item is not already at the bottom
        if index is not None and index < len(parent_list) - 1:
            # Swap the item with the one below it
            parent_list[index], parent_list[index + 1] = parent_list[index + 1], parent_list[index]
            # Update the data in the RecycleView
            self.parent.parent.data = parent_list
            self.update_reps_and_sets(1)
class SavePlanItem(MDFloatLayout):
    exercise_images = ListProperty()
    count_number = StringProperty("")
    day_number = StringProperty("Day 1")
    clickable = BooleanProperty(False)
    def __init__(self, selected_exercises=None, day=None, **kwargs):
        super(SavePlanItem, self).__init__(**kwargs)
        self.generate_exercise_images(selected_exercises, day)
        self.day_number = f"Day {day}"
    def generate_exercise_images(self, selected_exercises, day):
        count= len(selected_exercises[day])
        images = []
        if count > 5:
            images = [next(exercise['icon'] for exercise in exercises if exercise['name'] == ex['name']) for ex in selected_exercises[day][:4]]
            images.append("number_rec.png") # Last image is a number
            self.count_number = f"+{count - 5}"
        elif count == 5:
            images = [next(exercise['icon'] for exercise in exercises if exercise['name'] == ex['name']) for ex in selected_exercises[day]] 
        else:
            images = ["invisiblerec.png"] * (5 - count) 
            images_extra=[next(exercise['icon'] for exercise in exercises if exercise['name'] == ex['name']) for ex in selected_exercises[day]]
            images += images_extra
        self.exercise_images = images
class ImageButton(ButtonBehavior, Image):
    pass
class WorkoutImage(ImageButton):
    opacity = NumericProperty(0.5)
    source_image = StringProperty()
    item_id = NumericProperty()
class WorkoutRow(MDGridLayout):
    btn_color= ListProperty([46/255, 46/255, 46/255, 0])
    btn_color_down= ListProperty([36/255, 36/255, 36/255, 0])
    opacity = NumericProperty(0.5)
    set= StringProperty("1")
    kg= StringProperty("-")
    reps= StringProperty("-")
    tenrm= StringProperty("-")
    type= StringProperty("todo")
    icon= StringProperty("invisiblerec.png")
    icon_opacity= NumericProperty(1)

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_icon()    
        
    def update_icon(self):
        if self.type == "todo":
            self.icon = "invisiblerec.png"
            self.btn_color= [0, 0, 0, 0]
            self.btn_color_down= [0, 0, 0, 0]
        elif self.type == "done":
            self.icon = "check.png"
            self.icon_opacity = 0.5
            self.btn_color= [0, 0, 0, 0]
            self.btn_color_down= [0, 0, 0, 0]
            anim = Animation(opacity=0.8, duration=0.2) + Animation(opacity=1, duration=0.2)
            anim.start(self)
        else:
            self.icon = "check_bg.png"
            self.opacity = 1
            self.btn_color= [46/255, 46/255, 46/255, 1]
            self.btn_color_down= [36/255, 36/255, 36/255, 1]
            
    def shake_animation(self):
        anim = Animation(pos_hint={'center_x': self.pos_hint['center_x'] + 0.01}, duration=0.05) + \
            Animation(pos_hint={'center_x': self.pos_hint['center_x'] - 0.02}, duration=0.05) + \
            Animation(pos_hint={'center_x': self.pos_hint['center_x']}, duration=0.05)
        anim.start(self)           
class SetNumber(RoundedRectangle2):
    def on_release(self):
        number = self.text.split(" ")[0]
        MDApp.get_running_app().root.get_screen('logworkout').chosen_item(number)
class ChooseItem(MDFloatLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)    
class Command(MDLabel):
    text = StringProperty()
    size_hint_x = NumericProperty()
    halign = StringProperty()
    font_name = "Poppins"
    font_size = 17
class Response(MDLabel):
    text = StringProperty()
    size_hint_x = NumericProperty()
    halign = StringProperty()
    font_name = "Poppins"
    font_size = 17

#--------------------------------------------------------------------------------------------------------------------------------------------
class FitnessApp(MDApp):
   def build(self):
       sm = WindowManager()
       self.theme_cls.theme_style = "Dark"
       self.theme_cls.primary_palette = "Blue"
       sm.current = 'loading' # Set the initial screen to the loading screen
       return Builder.load_file("try.kv")

   def on_start(self, *args):
       Window.size = (360 , 640)
       # Load your resources here
       # Once resources are loaded, switch to the main screen
       self.root.current = 'initialpage' # Switch to the main screen
if __name__ == "__main__":
    FitnessApp().run()
