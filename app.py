import os
import time
import threading
from flask import Flask, request, render_template, send_file, Response
from docx import Document
import zipfile
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
    "中国語 (簡体字)": "zh-Hans",
    "中国語 (繁体字)": "zh-Hant",
    "ベトナム語": "vi",
    "フランス語": "fr",
    "ドイツ語": "de",
    "スペイン語": "es",
    "韓国語": "ko",
    "ロシア語": "ru",
    "イタリア語": "it",
    "ポルトガル語": "pt",
    "アラビア語": "ar",
}

TRANSLATOR_API_KEY = "1r2WZwFSKT5F2Qbvk40JSqVElgs8TP17pTMwfkWsNtS26KgkNPs0JQQJ99BAACi0881XJ3w3AAAbACOGHRrZ"
TRANSLATOR_REGION = "japaneast"

# 進捗管理
progress = {"current": 0, "total": 0, "paused": False}

def translate_word_file(input_file, output_file, source_language, target_language):
    """Wordファイルの翻訳処理"""
    doc = Document(input_file)
    paragraphs = [{"index": idx, "text": p.text.strip()} for idx, p in enumerate(doc.paragraphs) if p.text.strip()]
    table_texts = []
    table_cells = []

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    table_texts.append(cell.text.strip())
                    table_cells.append(cell)

    all_texts = [p["text"] for p in paragraphs] + table_texts
    translated_texts = translate_texts_with_retry(all_texts, source_language, target_language)

    for p in paragraphs:
        doc.paragraphs[p["index"]].text = translated_texts.pop(0)
    for cell in table_cells:
        cell.text = translated_texts.pop(0)

    doc.save(output_file)

def translate_texts_with_retry(texts, source_language, target_language, max_retries=10, batch_size=50):
    """翻訳処理"""
    translated_texts = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for attempt in range(max_retries):
            try:
                translated_texts.extend(translate_texts(batch, source_language, target_language))
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise e
    return translated_texts

def translate_texts(texts, source_language, target_language):
    endpoint = "https://api.cognitive.microsofttranslator.com/translate"
    headers = {
        "Ocp-Apim-Subscription-Key": TRANSLATOR_API_KEY,
        "Ocp-Apim-Subscription-Region": TRANSLATOR_REGION,
        "Content-type": "application/json",
    }
    params = {"api-version": "3.0", "from": source_language, "to": target_language}
    body = [{"text": text} for text in texts]
    response = requests.post(endpoint, headers=headers, params=params, json=body)
    response.raise_for_status()
    return [t["translations"][0]["text"] for t in response.json()]

@app.route("/", methods=["GET", "POST"])
def index():
    global progress
    if request.method == "POST":
        source_language = request.form.get("source_language")
        target_language = request.form.get("target_language")
        uploaded_files = request.files.getlist("files")
        if not source_language or not target_language or not uploaded_files:
            return render_template("index.html", languages=LANGUAGE_CODES.keys(), error="入力項目を確認してください。")

        progress["current"] = 0
        progress["total"] = len(uploaded_files)
        progress["paused"] = False
        results = []

        def process_files():
            for file in uploaded_files:
                while progress["paused"]:
                    time.sleep(0.5)
                input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
                output_path = os.path.join(OUTPUT_FOLDER, f"translated_{file.filename}")
                file.save(input_path)
                translate_word_file(input_path, output_path, LANGUAGE_CODES[source_language], LANGUAGE_CODES[target_language])
                results.append(output_path)
                progress["current"] += 1

        threading.Thread(target=process_files).start()
        return render_template("index.html", languages=LANGUAGE_CODES.keys(), files=results, message="翻訳が進行中です。")
    return render_template("index.html", languages=LANGUAGE_CODES.keys())

@app.route("/progress")
def progress_status():
    def generate():
        while progress["current"] < progress["total"]:
            yield f"data:{progress['current']}/{progress['total']}\n\n"
            time.sleep(0.5)
        yield "data:complete\n\n"
    return Response(generate(), content_type="text/event-stream")

@app.route("/download_zip")
def download_zip():
    zip_path = os.path.join(OUTPUT_FOLDER, "translations.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for file_name in os.listdir(OUTPUT_FOLDER):
            zipf.write(os.path.join(OUTPUT_FOLDER, file_name), arcname=file_name)
    return send_file(zip_path, as_attachment=True)

@app.route("/pause", methods=["POST"])
def pause():
    global progress
    progress["paused"] = True
    return "Paused"

@app.route("/resume", methods=["POST"])
def resume():
    global progress
    progress["paused"] = False
    return "Resumed"

if __name__ == "__main__":
    app.run(debug=True)
