import os
import time
import threading
from flask import Flask, request, render_template, send_file, Response
from docx import Document
from werkzeug.utils import secure_filename

app = Flask(__name__)

# フォルダ設定
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 言語設定
LANGUAGE_CODES = {
    "日本語": "ja",
    "英語": "en",
}

# Microsoft Translator APIキー
TRANSLATOR_API_KEY = "1r2WZwFSKT5F2Qbvk40JSqVElgs8TP17pTMwfkWsNtS26KgkNPs0JQQJ99BAACi0881XJ3w3AAAbACOGHRrZ"
TRANSLATOR_REGION = "japaneast"

# 進捗管理
progress = {"current": 0, "total": 0, "paused": False}


def translate_word_file(input_file, output_file, source_language, target_language):
    """模擬翻訳処理"""
    time.sleep(1)  # 翻訳処理を模擬
    with open(input_file, "r") as f_in, open(output_file, "w") as f_out:
        f_out.write(f_in.read().upper())  # テキストを大文字に変換（模擬翻訳）


@app.route("/", methods=["GET", "POST"])
def index():
    global progress
    if request.method == "POST":
        source_language = request.form.get("source_language")
        target_language = request.form.get("target_language")
        uploaded_files = request.files.getlist("files")

        if not source_language or not target_language or not uploaded_files:
            return render_template("index.html", languages=LANGUAGE_CODES.keys(), error="入力項目を確認してください。")

        # 初期化
        progress["current"] = 0
        progress["total"] = len(uploaded_files)
        progress["paused"] = False

        def process_files():
            global progress
            for file in uploaded_files:
                input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
                output_path = os.path.join(OUTPUT_FOLDER, f"translated_{file.filename}")
                file.save(input_path)

                while progress["paused"]:
                    time.sleep(0.1)

                translate_word_file(input_path, output_path, source_language, target_language)
                progress["current"] += 1

        threading.Thread(target=process_files).start()
        return render_template("index.html", languages=LANGUAGE_CODES.keys(), message="翻訳が進行中です。")

    return render_template("index.html", languages=LANGUAGE_CODES.keys())


@app.route("/progress")
def progress_status():
    """進捗状況をクライアントに送信"""
    def generate():
        while progress["current"] < progress["total"]:
            yield f"data:{progress['current']}/{progress['total']}\n\n"
            time.sleep(0.5)
        yield "data:complete\n\n"
    return Response(generate(), content_type="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True)
