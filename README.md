# CompoundX Project

## Project Overview

This project consists of a backend and a frontend component. Currently, the backend and frontend are not yet fully integrated, but this README provides instructions on how to set up and run each part independently.

## Setup Instructions

Follow these steps to set up and run the CompoundX project:

### Step-1: Environment Variables Setup

* **Backend:**
    * Navigate to the `Backend` directory.
    * Create a `.env` file in the `Backend` directory.
    * Add your backend environment variables to the `.env` file. Refer to `.env.example` for the required variables and their format.

* **Frontend:**
    * Navigate to the `frontend` directory.
    *  Environment variables for the frontend are typically handled differently depending on your frontend framework (e.g., Next.js, React).  Consult your frontend framework's documentation for how to set environment variables.  If you have specific environment variables for the frontend, document them in the frontend's `README.md` (if you create one within the `frontend` directory) or here.

### Step-2: Install Dependencies

* **Backend:**
    * Navigate to the `Backend` directory in your terminal:
      ```bash
      cd Backend
      ```
    * Install the required Python packages using pip:
      ```bash
      pip install -r requirements.txt
      ```
      *(Ensure you have a `requirements.txt` file in your `Backend` directory listing your Python dependencies. If not, create one using `pip freeze > requirements.txt` after installing your dependencies manually).*

* **Frontend:**
    * Navigate to the `frontend` directory in your terminal:
      ```bash
      cd frontend
      ```
    * Install frontend dependencies using either pnpm or npm. Choose one package manager and use the corresponding command:

      **Using pnpm:**
      ```bash
      pnpm install
      ```

      **Using npm:**
      ```bash
      npm install
      ```

### Step-3: Run the Frontend

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
      ```
   2. Start the frontend development server using `npm run dev`:
   ```bash
   npm run dev
      ```
   2. Start the frontend convex server using `npx convex dev`:
   ```bash
   npx convex dev
      ```
### Step-4: Test the python backend scripts

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
   2. Run the crawl_main.py using `python crawl_main.py`: (It will scrape and store the data of the stock in database)
   ```bash
   python crawl_main.py
   ```
   2. Start the agent.py using `python agent.py`: (To talk with the data saved in database)
   ```bash
   python agent.py
   ```
