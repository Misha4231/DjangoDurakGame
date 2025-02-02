# Durak Game (Django + Django Channels)

## 📌 Overview
This project is an online **Durak card game** built with **Django** and **Django Channels**. It features real-time gameplay using **WebSockets** without external message brokers like Redis, relying instead on Django Channels' in-memory layer.

## 🛠️ Tech Stack
- **Django** – Backend framework
- **Django Channels** – WebSockets for real-time communication
- **SQLite3** – Lightweight database for storing user and game state
- **HTML/CSS/JavaScript** – Frontend for game interface

## 📦 Installation & Setup

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Apply Migrations
```bash
python manage.py migrate
```

### 3️⃣ Run Django Development Server
```bash
python manage.py runserver
```

## 🎮 How to Play
1. Open the game in your browser.
2. Join waiting room with desired players count.
3. Play turns in real-time.
