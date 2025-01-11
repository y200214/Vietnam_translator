@echo off
echo Starting Flask app in Docker...

REM Dockerイメージをビルド
docker build -t flask-app .

REM Flaskアプリを起動（ポート5000をマッピング）
docker run -p 5000:5000 flask-app

pause
