# RateSphere

A simple desktop application created using Python and KivyMD that allows users to track and rate various media: movies, books, games, and more.

## 🚀 Features

* **User Accounts:** Registration and login.
* **Adding elements:** The ability to add new elements with details (title, alternative title, type, viewing/passing status, grade, review).
* **View List:** Display a list of the user's graded items.
* **Permanent session:** The application remembers the user between launches (session data is stored locally).
* **Change theme:** Switching between light and dark interface themes.
* **Security:** Passwords are hashed using bcrypt.

## 🛠️ Technologies

* **Language:** Python 3.x
* **GUI:** Kivy & KivyMD
* **Database:** PostgreSQL
* **Database adapter:** psycopg2 (the `psycopg2-binary` library is recommended for ease of installation)
* **Configuration:** python-dotenv (to load environment variables from `.env`)
* **Password hashing:** bcrypt

## 📋 Preliminary requirements

Make sure you have the following installed before installing:

1.  **Python:** Version 3.7 or higher. [Download Python](https://www.python.org/downloads/)
2.  **PostgreSQL:** Installed and running PostgreSQL server. [Download PostgreSQL](https://www.postgresql.org/download/)
3.  **Git:** To clone a repository. [Download Git](https://git-scm.com/downloads/)

## ⚙️ Installation and startup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Romanennko/RateSphere
    cd RateSphere
    ```

2.  **Create and activate a virtual environment** (recommended):
    * Windows:
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```
    * macOS / Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Configure the PostgreSQL database:**
    * Connect to your PostgreSQL server (for example, via `psql` or a GUI client like pgAdmin).
    * Create a new database for the application:
        ```sql
        CREATE DATABASE ratesphere_db; -- You can choose another name
        ```
    * Create a new user (recommended for security) and set a password for it:
        ```sql
        CREATE USER ratesphere_user WITH PASSWORD 'your_super-secure_password';
        ```
    * Grant the user rights to the created database:
        ```sql
        GRANT ALL PRIVILEGES ON DATABASE ratesphere_db TO ratesphere_user;
        ```
    * Connect to the created database (`ratesphere_db`).
    * Execute the `schema.sql` script to create the tables and necessary structures:
        ```bash
        # In psql, connecting to ratesphere_db:
        \i /path/to/your/project/RateSphere/schema.sql
        ```
        *(Replace `/path/to/your/project/' with the actual path)*

4.  **Create configuration file `.env`:**
    * In the root directory of the project (`RateSphere/`), create a file named `.env`.
    * Copy the following content into it, replacing the values with your actual database connection data:
        ```dotenv
        # RateSphere Environment Variables
        DB_NAME=ratesphere_db
        DB_USER=ratesphere_user
        DB_PASSWORD=your_super-secure_password
        DB_HOST=localhost  # Or the IP address/host of your database server
        DB_PORT=5432       # PostgreSQL standard port
        ```

5.  **Install Python dependencies:**
    * **(Important!)** If you do not already have a `requirements.txt` file, create one now while in an activated virtual environment:
        ```bash
        pip freeze > requirements.txt
        ```
        *(Make sure to include `kivy`, `kivymd`, `psycopg2-binary`, `python-dotenv`, `bcrypt`).
    * Establish dependencies:
        ```bash
        pip install -r requirements.txt
        ```

6.  **Start the application:**
    ```bash
    python main.py
    ```

## 📄 License
Distributed under the MIT license. See the `LICENSE` file for more information.
---