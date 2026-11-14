import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
HTTPS_ONLY = os.getenv("HTTPS_ONLY", "false").lower() == "true"
SESSION_MAX_AGE = 60 * 60 * 2  # sessiya 2 soat

# --- Talaba ma'lumotlari (kabinetda chiqadi). O'zingizniki bilan almashtiring ---
SEED_USERNAME = os.getenv("SEED_USERNAME", "oxunjon")          # login: ismingiz
SEED_PASSWORD = os.getenv("SEED_PASSWORD", "Jabborov2026")     # 12 belgi, familiya bilan
SEED_FULL_NAME = os.getenv("SEED_FULL_NAME", "Jabborov Oxunjon Shakirali o'g'li")
SEED_GROUP = os.getenv("SEED_GROUP", "WEI003-1")                 # TODO: guruhingiz
SEED_FACULTY = os.getenv("SEED_FACULTY", "Dasturiy injiniring")      # TODO: fakultetingiz
SEED_AGE = int(os.getenv("SEED_AGE", "20"))                    # TODO: yoshingiz
