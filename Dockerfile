# ベースイメージとして公式のPythonイメージを使用
FROM python:3.9

# 作業ディレクトリを設定
WORKDIR /app

# アプリケーションのコードをコンテナにコピー
COPY . /app

# 依存パッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# コンテナ起動時に実行するコマンド
CMD ["python", "app.py"]

# Flaskアプリケーションをポート5000で起動
EXPOSE 5000
