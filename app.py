import random
import time
import json
import tkinter as tk
from tkinter import messagebox
from owlready2 import *

# Load the ontology
onto = get_ontology("aos.owl").load()

# Global variables
student_id = "student_001"  # Example student ID
shapes = ["square", "triangle", "rectangle"]
current_shape = None
current_problem = None
current_answer = None
attempts_left = 3
time_limit = 30
start_time = None

# Global variable to track consecutive correct answers for each shape
correct_answers_in_row = {
    "square": 0,
    "triangle": 0,
    "rectangle": 0
}

# Function to query the ontology for the shape's area formula
def get_shape_from_ontology(shape_name):
    try:
        shape = onto.search_one(iri=f"*{shape_name}AreaConcept")
        if not shape:
            raise ValueError(f"Shape '{shape_name}' not found in ontology.")
        return shape
    except Exception as e:
        messagebox.showerror("Error", f"Error while accessing the ontology: {e}")
        return None

# Function to adjust difficulty based on performance
def adjust_difficulty():
    global correct_answers_in_row
    shape_name = current_shape

    # If the student answered 3 consecutive questions correctly for this shape
    if correct_answers_in_row[shape_name] >= 3:
        # Increase difficulty by using larger numbers or more complex shapes
        if shape_name == "square":
            max_side_length = 20  # Increase max side length for square
        elif shape_name == "triangle":
            max_base_height = 20  # Increase max base/height for triangle
        elif shape_name == "rectangle":
            max_base_height = 20  # Increase max base/height for rectangle
        
        # After increasing the difficulty, reset the streak for this shape
        correct_answers_in_row[shape_name] = 0
        return True  # Indicating that the difficulty was increased
    return False  # No difficulty increase

# Function to generate problems dynamically based on shape and adjusted difficulty
def generate_problem(shape_name):
    global current_shape, current_problem, current_answer, attempts_left, start_time
    # Reset variables for each new problem
    attempts_left = 3
    start_time = time.time()
    base = height = side_length = None
    formula_text = ""
    
    # Get shape-specific details from ontology
    shape = get_shape_from_ontology(shape_name)
    if shape:
        formula_text = shape.hasFormulaText[0] if hasattr(shape, "hasFormulaText") else "No formula available."
        
        # Adjust difficulty based on performance
        difficulty_increased = adjust_difficulty()

        # Generate dimensions based on shape type and difficulty
        if shape_name == "square":
            max_side_length = 10 if not difficulty_increased else 20  # Increase range if difficulty is increased
            side_length = random.randint(1, max_side_length)  # Random side length for square
            current_answer = side_length ** 2
            current_problem = f"Calculate the area of a square with side length {side_length} cm."
        elif shape_name == "triangle":
            max_base_height = 10 if not difficulty_increased else 20
            base = random.randint(1, max_base_height)
            height = random.randint(1, max_base_height)
            current_answer = 0.5 * base * height
            current_problem = f"Calculate the area of a triangle with base {base} cm and height {height} cm."
        elif shape_name == "rectangle":
            max_base_height = 10 if not difficulty_increased else 20
            base = random.randint(1, max_base_height)
            height = random.randint(1, max_base_height)
            current_answer = base * height
            current_problem = f"Calculate the area of a rectangle with base {base} cm and height {height} cm."
        
        problem_text = f"Problem: {current_problem}\nUse the formula: {formula_text}"
        display_problem(problem_text)
        update_timer()  # Start the timer for this problem
    else:
        messagebox.showerror("Error", f"No information available for {shape_name}. Please check your ontology.")

# Function to display the current problem on the GUI
def display_problem(problem_text):
    problem_label.config(text=problem_text)
    answer_entry.delete(0, tk.END)
    attempts_label.config(text=f"Attempts left: {attempts_left}")
    timer_label.config(text=f"Time left: {time_limit}")

# Function to check the student's answer
def check_answer():
    global attempts_left, start_time, current_shape, correct_answers_in_row
    try:
        student_answer = float(answer_entry.get())
        if student_answer <= 0:
            raise ValueError("Please enter a positive number.")
        elapsed_time = time.time() - start_time
        if student_answer == current_answer:
            correct_answers_in_row[current_shape] += 1  # Increment streak for correct answers
            messagebox.showinfo("Correct!", "Well done, your answer is correct!")
            log_student_performance(student_id, current_shape, True, elapsed_time)
            next_problem()  # Move to the next problem after correct answer
        else:
            attempts_left -= 1
            if attempts_left == 0:
                messagebox.showerror("Incorrect", f"Sorry, the correct answer was {current_answer}.")
                log_student_performance(student_id, current_shape, False, elapsed_time)
                next_problem()  # Move to the next problem after all attempts are used
            else:
                messagebox.showwarning("Incorrect", f"Oops! Try again. Attempts left: {attempts_left}")
                display_problem(current_problem)  # Redisplay problem with updated attempts left
    except ValueError as e:
        messagebox.showerror("Error", f"Invalid input: {e}")

# Function to reset the timer and update the time left
def update_timer():
    global time_limit, start_time
    elapsed_time = time.time() - start_time
    remaining_time = time_limit - int(elapsed_time)
    if remaining_time <= 0:
        messagebox.showerror("Time's up!", "Sorry, you ran out of time.")
        log_student_performance(student_id, current_shape, False, elapsed_time)
        next_problem()  # Move to the next problem after time is up
    else:
        timer_label.config(text=f"Time left: {remaining_time}")
        root.after(1000, update_timer)  # Update the timer every second

# Function to move to the next problem
def next_problem():
    global attempts_left
    attempts_left = 3  # Reset attempts for the next problem
    if len(shapes) > 0:  # If we still have more shapes
        shape_name = shapes.pop(0)  # Pop the next shape from the list
        generate_problem(shape_name)  # Generate a problem for the new shape
    else:
        messagebox.showinfo("All Done", "You've completed all the problems!")
        show_performance_report()  # Show the performance report after all problems are done
        shapes[:] = ["square", "triangle", "rectangle"]  # Reset the shapes list for the next session

# Helper function to initialize student performance data
def initialize_student_performance(student_id):
    return {
        "total_problems": 0,
        "correct_answers": 0,
        "incorrect_answers": 0,
        "time_spent": 0,
        "problem_attempts": {},
        "incorrect_shapes": {}
    }

# Function to log student performance data
def log_student_performance(student_id, shape_name, correct, time_spent):
    performance_data = load_student_data()

    if student_id not in performance_data:
        performance_data[student_id] = initialize_student_performance(student_id)

    student_data = performance_data[student_id]
    student_data["total_problems"] += 1
    student_data["time_spent"] += time_spent
    student_data["problem_attempts"][shape_name] = student_data["problem_attempts"].get(shape_name, 0) + 1

    if correct:
        student_data["correct_answers"] += 1
    else:
        student_data["incorrect_answers"] += 1
        student_data["incorrect_shapes"][shape_name] = student_data["incorrect_shapes"].get(shape_name, 0) + 1

    save_student_data(performance_data)

# Load student data (from a file or memory)
def load_student_data():
    try:
        with open("student_data.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save student data to file
def save_student_data(performance_data):
    with open("student_data.json", "w") as file:
        json.dump(performance_data, file)

# Generate and show the performance report
def show_performance_report():
    performance_data = load_student_data()
    if student_id in performance_data:
        data = performance_data[student_id]
        report_text = f"Performance Report for {student_id}:\n"
        report_text += f"Total Problems: {data['total_problems']}\n"
        report_text += f"Correct Answers: {data['correct_answers']}\n"
        report_text += f"Incorrect Answers: {data['incorrect_answers']}\n"
        report_text += f"Time Spent: {data['time_spent']} seconds\n"
        messagebox.showinfo("Performance Report", report_text)
    else:
        messagebox.showerror("Error", "No data found for student.")

# Create the GUI
root = tk.Tk()
root.title("Math Problem Solver - ITS")

# Labels
problem_label = tk.Label(root, text="Welcome to the Math Problem Solver!", font=("Arial", 16), justify="left")
problem_label.pack(pady=10)

attempts_label = tk.Label(root, text="Attempts left: 3", font=("Arial", 12))
attempts_label.pack()

timer_label = tk.Label(root, text="Time left: 30", font=("Arial", 12))
timer_label.pack()

# Answer input field
answer_entry = tk.Entry(root, font=("Arial", 14))
answer_entry.pack(pady=10)

# Buttons
check_button = tk.Button(root, text="Check Answer", font=("Arial", 14), command=check_answer)
check_button.pack(pady=10)

# Dropdown menu for shape selection
shape_selection = tk.StringVar(root)
shape_selection.set(shapes[0])  # Default shape is square
shape_menu = tk.OptionMenu(root, shape_selection, *shapes)
shape_menu.pack(pady=10)

# Start button
start_button = tk.Button(root, text="Start Problem", font=("Arial", 14), command=lambda: generate_problem(shape_selection.get()))
start_button.pack(pady=20)

# Start the GUI loop
root.mainloop()
