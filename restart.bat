@echo off
echo 🔄 Stopping and removing old containers...
docker compose down

echo 🛠 Building and starting English Bot...
docker compose up --build -d

echo ✅ Done! Your bot is now running with the latest changes.
pause
