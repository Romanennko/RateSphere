# RateSphere

RateSphere is a desktop application built with Python and KivyMD, designed for tracking and rating various media like movies, books, games, and more.

## 🚀 Features

* **User Accounts:** Secure registration and login system. [cite: 1]
* **Media Tracking:** Add, view, edit, and delete items you've consumed or plan to consume.
* **Detailed Entries:** Store information like title, alternative title, media type, status (Completed, Planned, etc.), review, and overall rating.
* **Advanced Rating:**
    * Rate items using a simple 1-10 overall score.
    * Alternatively, rate based on specific criteria (e.g., Gameplay, Plot, Graphics) with automatic calculation of the average score.
    * Predefined criteria are included, with suggestions based on media type.
* **Customizable List View:** View your rated items and sort them by name, type, status, rating, or date added/updated.
* **User Profile:** View statistics about your rated items, including counts by type/status, average ratings, and rating distribution. Manage account settings like changing your password and default sort preferences.
* **Persistent Session:** The application remembers your login state between launches (session data is stored locally).
* **Theme Switching:** Easily switch between light and dark interface themes.
* **Security:** User passwords are securely hashed using bcrypt. [cite: 1]

## 🛠️ Technologies

* **Language:** Python 3.x
* **GUI Framework:** Kivy & KivyMD
* **Database:** PostgreSQL
* **Database Adapter:** psycopg2 (`psycopg2-binary` recommended for easy installation)
* **Configuration:** python-dotenv (for loading `.env` files)
* **Password Hashing:** bcrypt [cite: 1]

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python:** Version 3.7 or higher. [Download Python](https://www.python.org/downloads/)
2.  **PostgreSQL:** An installed and running PostgreSQL server. [Download PostgreSQL](https://www.postgresql.org/download/)
3.  **Git:** For cloning the repository. [Download Git](https://git-scm.com/downloads/)

## ⚙️ Installation and Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Romanennko/RateSphere](https://github.com/Romanennko/RateSphere)
    cd RateSphere
    ```

2.  **Create and activate a virtual environment** (Highly Recommended):
    * Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    * macOS / Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Configure the PostgreSQL Database:**
    * Connect to your PostgreSQL instance (using `psql`, pgAdmin, or another client).
    * Create a new database for the application:
        ```sql
        CREATE DATABASE ratesphere_db; -- Or choose a different name
        ```
    * Create a dedicated user (recommended for security) and assign a password:
        ```sql
        CREATE USER ratesphere_user WITH PASSWORD 'your_super_secure_password';
        ```
    * Grant the necessary privileges to the user on the new database:
        ```sql
        GRANT ALL PRIVILEGES ON DATABASE ratesphere_db TO ratesphere_user;
        ```
    * Connect to the newly created database (`ratesphere_db`).
    * Execute the `schema.sql` script to set up the tables and initial data:
        ```bash
        # Example using psql while connected to ratesphere_db:
        \i /path/to/your/project/RateSphere/schema.sql
        ```
        *(Replace `/path/to/your/project/` with the actual path to the cloned repository)*

4.  **Create the Configuration File (`.env`):**
    * In the root directory of the project (`RateSphere/`), create a file named `.env`.
    * Add the following content, replacing the placeholder values with your actual database connection details:
        ```dotenv
        # RateSphere Environment Variables
        DB_NAME=ratesphere_db
        DB_USER=ratesphere_user
        DB_PASSWORD=your_super_secure_password
        DB_HOST=localhost  # Or the IP address/hostname of your DB server
        DB_PORT=5432       # Default PostgreSQL port
        ```

5.  **Install Python Dependencies:**
    * Ensure your virtual environment is activated.
    * Install the required packages using the provided `requirements.txt` file:
        ```bash
        pip install -r requirements.txt
        ```

6.  **Run the Application:**
    ```bash
    python main.py
    ```

## 📄 License

Distributed under the MIT License. See the `LICENSE` file for more information.