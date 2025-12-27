# FITFUEL: FITNESS APP DEVELOPMENT
**A-Level Computer Science Non-Exam Assessment (2024)**
**Student:** Silmoon Hossain (HOS21004547)
**Centre:** NewVIc (13227)

---

## SECTION 1: ANALYSIS

### 1.1 Project Background
The fitness industry is undergoing a rapid digital transformation. While technology has made it easier to track health metrics, many users feel overwhelmed by the sheer volume of data without actionable guidance. The developer notes that existing fitness apps often feel "impersonal," resembling a rigid spreadsheet rather than a supportive coach. 

The core philosophy of this project is to move away from "robot-like" workout plans. Research conducted by the developer indicates that users desire an application that learns their habits, understands their motivations, and builds a holistic plan that integrates workouts, nutrition, and lifestyle balance. The goal of "FitFuel" is to provide a personalized experience that treats fitness as a whole lifestyle change rather than just a series of gym sessions.

### 1.2 Current System Review
The developer performed a deep dive into three market leaders to identify gaps:
*   **MyFitnessPal:** Praised for its massive food database and barcode scanner. However, it was found lacking in personalized workout advice or meal planning. It functions as a journal, leaving the user to figure out the "how" and "why" on their own.
*   **Fitbit:** Strong in hardware integration (wearables) and tracking passive metrics like steps and sleep. The downside identified was that its fitness plans feel generic and "made-for-everyone," and users often struggle with hardware synchronization issues.
*   **AlphaProgression:** Excellent for muscle building, providing workouts based on specific equipment availability and high-quality video guidance. Its major flaw is the complete absence of nutrition tracking features.

**The FitFuel Solution:** To bridge these gaps, FitFuel combines the personalization of AlphaProgression with the comprehensive tracking of MyFitnessPal, enhanced by an AI-powered conversational coach to provide the "human" element missing from current systems.

### 1.3 Research and Personas
The developer's research was extensive, involving an online survey via Instagram Stories that garnered an average of 620 responses per question. This was supplemented by direct observations in a local gym to see how people actually interact with apps mid-workout.

#### 1.3.1 Key Findings from Research:
*   **Holistic Needs:** 27% of users want a single app for both nutrition and workouts to avoid app-switching fatigue.
*   **Primary Goals:** Weight loss (29%) and body recomposition (14%) are the leading drivers for app usage.
*   **Personalization Gap:** 48% of respondents cited a lack of personalization as their biggest frustration.
*   **Content Preference:** 35% prefer video tutorials, and 32% desire interactive coaching.

#### 1.3.2 User Personas:
*   **Abdullah (35):** A busy professional with family duties. He has past injuries and is terrified of poor form. He needs time-efficient, safe, and guided workouts.
*   **Abby (20):** A college student who is overwhelmed by conflicting fitness advice online. She lacks a routine and struggles with staying motivated.
*   **Zak (17):** A student who wants to build strength but finds set schedules boring. He needs a plan that is fun and adapts to his specific needs.

### 1.4 Objectives and Requirements
The project defined ten primary objectives, ranging from algorithm development for workout generation to secure data handling. Each objective includes a specific "Test Objective" to ensure the final product meets the initial requirements.

**Key Data Requirements:**
To function, the app must collect:
*   **Personal Stats:** Gender, age, height, weight, and body fat percentage.
*   **Fitness Profile:** Experience level (Novice to Elite), equipment access (Gym vs. Home), and schedule availability.
*   **Tracking Data:** Exercises performed (sets/reps/weight), meal logs (macros/calories), and body measurement changes over time.

### 1.6 Acceptable Limitations
The developer acknowledges that as a solo project, certain features are limited:
*   **Injury Management:** Plans assume a generally healthy user; the app cannot replace medical diagnosis.
*   **Manual Entry:** Nutrition tracking relies on manual input rather than automated photo recognition.
*   **Niche Disciplines:** The app focuses on general fitness and hypertrophy rather than elite-level powerlifting or professional calisthenics.

---

## SECTION 2: DESIGN

### 2.1 System Flowchart (User Onboarding)
The onboarding process is a sophisticated logic engine designed to calculate a user's metabolic needs.
1.  **Initial Inputs:** The user starts by selecting gender, age, height, and weight.
2.  **Body Fat Logic:** The app asks if the user knows their body fat percentage.
    *   If **YES**, the user enters the value.
    *   If **NO**, the app triggers a sub-routine using the **US Navy Body Fat Formula**. For males, it requires waist and neck circumferences. For females, it adds a hip measurement.
3.  **Metabolic Calculations:**
    *   **BMR (Basal Metabolic Rate):** Calculated using gender-specific formulas (Mifflin-St Jeor Equation).
    *   **TDEE (Total Daily Energy Expenditure):** The BMR is multiplied by an activity level factor (ranging from 1.2 for sedentary to 1.9 for extra active).
4.  **Goal Setting:** The user selects a goal (Lose weight, Maintain, Gain muscle). The app then calculates a "Target Calorie" count by adding or subtracting a caloric buffer based on the desired rate of change (e.g., 0.25kg to 1kg per week).
5.  **Workout Split Selection:** Based on the user's available days and equipment, the system assigns a workout split (e.g., Full Body, Push/Pull/Legs, or Upper/Lower).

### 2.2 Hierarchy Chart
The system is organized into a clear hierarchy. The **Dashboard** acts as the central node, connecting to:
*   **AI Chatbot:** Handles natural language queries and provides fitness advice.
*   **Exercise Library:** Allows for searching, viewing techniques, and creating custom exercises.
*   **Workout Engine:** Manages generated plans, custom plans, and the live workout logging interface.
*   **Nutrition Engine:** Manages food searching via API and daily log management.
*   **Progress Tracking:** Visualizes weight trends and caloric intake.

### 2.3 Normalisation
The developer meticulously moved the database design through the stages of normalization to ensure data integrity.

*   **Unnormalized Form (0NF):** A single table where plan names and user IDs were repeated for every single exercise entry, leading to massive data redundancy.
*   **First Normal Form (1NF):** Ensuring all attributes are atomic.
*   **Second Normal Form (2NF):** Removing partial functional dependencies.
*   **Third Normal Form (3NF):** The final design consists of several interlinked tables:
    *   `WorkoutPlans`: Stores the plan name and owner.
    *   `WorkoutDays`: Links specific days to a plan.
    *   `Exercises`: A master list of all possible movements.
    *   `DayExercises`: A link table that stores the specific sets and reps for an exercise on a specific day of a specific plan.

### 2.4 SQL Tables Design
The database is built on MySQL with the following key structures:
*   **Userdata Table:** Uses `CHAR(36)` for a unique UUID primary key. It stores everything from hashed passwords (using `bcrypt`) to prioritized muscle groups.
*   **Food_items Table:** Stores every individual food entry with high precision (`DECIMAL(5,2)`) for macronutrients.
*   **Daily_totals Table:** Aggregates food data to provide a snapshot of a user's day against their target.
*   **Chats Table:** Uses a `TEXT` field for messages and a `DATETIME` stamp to maintain conversation history for the AI coach.

### 2.6 Entity Relationship Diagram (ERD)
The ERD shows a "Star Schema" influence where `USERDATA` is the central entity.
*   One user can have many `FOOD_ITEMS`, `DAILY_TOTALS`, `WORKOUT_PLANS`, and `CHATS`.
*   A `WORKOUT_PLAN` consists of multiple `WORKOUT_DAYS`.
*   A `WORKOUT_DAY` contains multiple `DAY_EXERCISES`.
*   The `EXERCISES` table is a reference entity linked to `DAY_EXERCISES`.

### 2.10 High Fidelity User Interface
The UI was designed in **Figma** and edited in **Photoshop**.
*   **Aesthetic:** A "Dark Mode" theme using charcoal blacks and deep purples to reduce eye strain during workouts.
*   **Interactive Elements:** Custom-designed icons for every exercise. The onboarding uses large, touch-friendly buttons and clear progress indicators.
*   **Visualizations:** The dashboard features a "Calories Remaining" ring and a "Weight Trend" spline graph to provide immediate visual feedback on progress.

---

## SECTION 3: TECHNICAL SOLUTION

### 3.1 Main Functionalities
The developer implemented several complex systems:
*   **User Profile Management:** A robust registration system that captures the data necessary for the metabolic and workout algorithms.
*   **Personalized Workout Plans:** An algorithm that considers the user's level, equipment, and muscle priorities to generate a balanced routine.
*   **Nutrition Tracking:** Integration with an external API to allow users to log real-world foods and see their nutritional breakdown.
*   **AI Conversational Coach:** A virtual assistant that provides motivational support and answers technical fitness questions.

### 3.2 Technologies Used
*   **Python:** The backbone of the application.
*   **Kivy & KivyMD:** Chosen for their ability to create modern, responsive UIs that work across different platforms.
*   **MySQL:** Used for persistent data storage.
*   **Requests Library:** Essential for making HTTP calls to the Edamam food database.
*   **Langchain:** Used to manage the logic and memory of the AI chatbot.
*   **Bcrypt:** Implemented to ensure that user passwords are never stored in plain text, providing high-level security.

### 3.4 Code Overview (Class Logic)
The application is built using Object-Oriented Programming (OOP) principles:
*   **UserManager (Singleton):** This class ensures that only one user session is active at a time, preventing data cross-contamination.
*   **DatabaseManager:** Centralizes all SQL interactions. It uses a connection pool to manage resources efficiently and includes methods for transactions (start, commit, rollback) to ensure database stability.
*   **WindowManager:** A Kivy-specific class that handles the transitions between different screens (e.g., moving from the Dashboard to the Workout Logger).
*   **GeneratePlan Class:** This is the "brain" of the workout system. It uses a `muscle_divisions` dictionary to categorize exercises and a `create_split` method to determine the structure of the week.

### 3.5 Completeness of Solution: Workout Generation Algorithm
The workout generation is the most complex part of the backend. It uses a **Tree Data Structure** to navigate choices:
1.  **Step 1:** Retrieve user details (frequency, experience, gender).
2.  **Step 2:** Divide prioritized muscle groups into individual muscles.
3.  **Step 3:** Create a workout split (e.g., if a user trains 3 times a week, it might choose a 'Push/Pull/Legs' split).
4.  **Step 4:** The algorithm traverses the exercise tree. It looks for the highest-rated exercises for the required muscle group.
5.  **Step 5:** It uses a **Merge Sort Algorithm** to reorder the plan based on the user's specific muscle priorities (e.g., if a user wants to focus on "Chest," chest exercises are moved to the start of the session when energy is highest).
6.  **Step 6:** The plan is formatted into a dictionary and saved to the database.

### 3.4.1 Hash Maps (Data Structures)
The developer used dictionaries (Hash Maps) extensively to optimize the app:
*   **Muscle Categorization:** Mapping broad groups like "Shoulders" to specific divisions like "Front Delts" and "Rear Delts."
*   **Exercise Selection:** A nested dictionary linking muscle groups to specific exercises and their respective "Hypertrophy Ratings" (on a scale of 1-10).
*   **UI Mapping:** A dictionary called `character_widths` was created to manually calculate the width of text strings in the UI, ensuring that icons and labels are perfectly aligned regardless of the word length.

### 3.4.2 Trees (Data Structures)
The workout plan is modeled as a multi-level tree.
*   **Level 3:** Muscle groups (e.g., Chest, Lats, Quads).
*   **Level 4:** Divisions (e.g., Upper Chest, Middle Chest).
*   **Level 5:** Specific Exercises (e.g., Incline Dumbbell Press).
*   **Level 6:** Hypertrophy Scale (The rating used by the sorting algorithm).
The developer used the `pydot` library to visualize this tree during the design phase.

### 3.4.8 AI Integration (Langchain & OpenAI)
The `ChatBotScreen` class manages the interaction with the OpenAI API. 
*   **Initial Prompt:** The developer "primes" the AI with a specific persona: an enthusiastic, supportive personal trainer. It also feeds the AI the user's specific data (age, weight, goal) so the advice is tailored.
*   **Memory:** Using `ConversationBufferMemory`, the app allows the AI to remember previous parts of the conversation, creating a natural flow.
*   **UI Feedback:** Because AI responses can take time, the developer implemented a "Typing..." status to improve the user experience.

---

## SECTION 4: TESTING

### 4.1 Final Test Table
The developer conducted rigorous testing across all modules:
*   **Test 1 (Workout Logic):** Verified that the algorithm correctly generates plans for all frequencies (1-7 days). A minor UI issue was noted where long lists overlapped on 1-day plans.
*   **Test 5 (Nutrition Logic):** Tested the conversion of food units. For "Peanuts," the app correctly calculated calories whether the user entered "grams," "ounces," or "cups."
*   **Test 6 (Database Integrity):** A bug was discovered where the app was summing "old data" from the database during food logging. This was fixed by refining the SQL `REPLACE INTO` logic.
*   **Test 9 (Security):** Verified that the system rejects incorrect passwords and that the database only stores `bcrypt` hashes.

### 4.2 Testing Evidence & Iteration
The developer provided screenshots showing the evolution of the app.
*   **Performance Optimization:** During testing, the developer noticed a performance lag when generating workout plans. The original design used a standard `MDList`, which rendered every item at once. To fix this, the developer switched to a **RecycleView**. This only renders the items currently visible on the screen, making the app much faster and more "reactive."
*   **UI Refinement:** Screenshots show the addition of a "shaky animation" if a user tries to log a set without entering weight or reps, providing intuitive feedback.

### User Feedback
*   **Misha:** Praised the customization but found the exercise library "overwhelming." Suggested adding filters for equipment or difficulty.
*   **Bashir:** Loved the food database and the UI design, noting it felt "modern."
*   **Hamed:** Found the AI coach helpful but noted that responses could sometimes feel "generic and long."

---

## SECTION 5: EVALUATION

### 5.1 Evaluating Objectives
*   **Objective 1.4.1 (Customizable Plans):** Successfully achieved using the Tree structure. The developer noted that while powerlifting was an option, they didn't fully implement specific powerlifting-style periodization due to time constraints.
*   **Objective 1.4.2 (Food Tracking):** Effectively met. The main challenge was handling the complex JSON files returned by the Edamam API.
*   **Objective 1.4.8 (User Interface):** The developer feels this was a major success. Learning the Kivy framework from scratch was "painfully slow" but resulted in a professional-looking product.
*   **Objective 1.4.10 (AI Coach):** Successfully implemented. A future improvement would be "streaming" the text (showing it as it generates) rather than waiting for the full response.

### 5.2 Final Thoughts
The developer concludes that the project was a significant learning curve. It provided practical experience in:
*   **Full-Stack Development:** Connecting a Python frontend to a MySQL backend.
*   **Functional Programming:** Moving from large, clunky code blocks to small, reusable functions.
*   **Data Structures:** Implementing Trees and Hash Maps to solve real-world logic problems.
*   **Problem Solving:** Overcoming framework-specific bugs and API integration hurdles.

---

## APPENDIX A: RESEARCH DATA

### 1. Survey Results
*   **App Usage:** Only 17% of respondents do *not* use a fitness app, showing a high market readiness.
*   **Goal Alignment:** 29% are focused on weight loss, while 24% are focused on general wellness.
*   **Feature Importance:** "Customized workout plans" was the most requested feature (56%), followed by "Progress tracking" (58%).

### 2. Gym Interviews
*   **Abdullah:** Emphasized that safety is his priority. He wants an app that tells him *exactly* how to perform a move so he doesn't hurt his knee again.
*   **Abby:** Highlighted the "information overload" on social media. She wants an app that acts as a "cheerleader" and simplifies her choices.
*   **Zak:** Wants to track progress to stay motivated. He finds traditional gym routines repetitive and wants something that "grows with him."

---
