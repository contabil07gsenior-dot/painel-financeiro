import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, render_template, request
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# =============================
# CLOUDINARY
# =============================
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

print("CLOUD:", cloudinary.config().cloud_name)

# =============================
# CONEXÃO SUPABASE (POSTGRES)
# =============================
def conectar():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        port=os.environ.get("DB_PORT"),
        cursor_factory=RealDictCursor
    )

# =============================
# ROTAS
# =============================
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dados")
def dados():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            categoria,
            tipo,
            valor,
            observacao,
            cliente_fornecedor,
            data,
            anexo
        FROM lancamentos
        ORDER BY data DESC
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(rows)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    item_id = request.form.get("id")

    if not file or not item_id:
        return jsonify({"ok": False, "erro": "Arquivo ou ID ausente"}), 400

    try:
        # Upload Cloudinary
        resultado = cloudinary.uploader.upload(
            file,
            folder="painel-financeiro",
            public_id=str(item_id),
            overwrite=True,
            resource_type="auto"
        )

        url = resultado["secure_url"]

        # Salvar URL no Supabase
        conn = conectar()
        cur = conn.cursor()

        cur.execute(
            "UPDATE lancamentos SET anexo = %s WHERE id = %s",
            (url, item_id)
        )

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"ok": True, "arquivo": url})

    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 500

# =============================
# START
# =============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)