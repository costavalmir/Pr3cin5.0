from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'chave_super_secreta'

# Carregamento do Excel com produtos
df = pd.read_excel("compras_05-04-2025.xlsx")
df["Descrição do Item"] = df["Descrição do Item"].astype(str)
df["Valor Unitário"] = pd.to_numeric(df["Valor Unitário"], errors="coerce")

def validar_login(usuario, senha):
    usuarios_df = pd.read_excel("usuarios.xlsx")
    usuario = usuario.strip().lower()
    senha = senha.strip()
    for _, row in usuarios_df.iterrows():
        if str(row["usuario"]).strip().lower() == usuario and str(row["senha"]).strip() == senha:
            return True
    return False

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        if validar_login(usuario, senha):
            session["usuario"] = usuario
            return redirect(url_for("index"))
        else:
            return render_template("login.html", erro="Usuário ou senha inválidos.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

@app.route("/", methods=["GET", "POST"])
def index():
    if "usuario" not in session:
        return redirect(url_for("login"))

    produtos_exibicao = []
    produtos_vistos = set()

    for _, row in df.iterrows():
        nome = row["Descrição do Item"]
        imagem = row.get("imagem", "")
        if nome not in produtos_vistos:
            produtos_exibicao.append({"nome": nome, "imagem": imagem})
            produtos_vistos.add(nome)

    return render_template("index.html", produtos=produtos_exibicao)

@app.route("/resultado", methods=["POST"])
def resultado():
    if "usuario" not in session:
        return redirect(url_for("login"))

    itens_selecionados = request.form.getlist("produto")
    quantidades = request.form.getlist("quantidade")

    if not itens_selecionados:
        return "Nenhum item selecionado."

    resultado_por_mercado = {}
    economia_total = 0
    gasto_total = 0

    for item, qtde in zip(itens_selecionados, quantidades):
        qtde = int(qtde) if qtde.isdigit() else 1
        dados_item = df[df["Descrição do Item"] == item]

        if not dados_item.empty:
            dados_item = dados_item.sort_values("Valor Unitário")
            local_mais_barato = dados_item.iloc[0]
            local_mais_caro = dados_item.iloc[-1]

            valor_unitario_barato = local_mais_barato["Valor Unitário"]
            valor_unitario_caro = local_mais_caro["Valor Unitário"]

            valor_total_barato = valor_unitario_barato * qtde
            valor_total_caro = valor_unitario_caro * qtde

            economia = valor_total_caro - valor_total_barato
            economia_total += economia
            gasto_total += valor_total_barato

            local = local_mais_barato["Local"]
            item_resultado = {
                "item": item,
                "quantidade": qtde,
                "local": local,
                "valor_unitario": round(valor_unitario_barato, 2),
                "valor_total": round(valor_total_barato, 2),
                "data_oferta": local_mais_barato.get("data da oferta", "")
            }

            if local not in resultado_por_mercado:
                resultado_por_mercado[local] = []

            resultado_por_mercado[local].append(item_resultado)

    return render_template(
        "resultado.html",
        resultado_por_mercado=resultado_por_mercado,
        economia_total=round(economia_total, 2),
        gasto_total=round(gasto_total, 2)
    )

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        enviar_email(nome, email)
        return redirect(url_for("sucesso"))
    return render_template("cadastro.html")

@app.route("/sucesso")
def sucesso():
    return render_template("sucesso.html")

@app.route("/upload_fotos", methods=["GET", "POST"])
def upload_fotos():
    if "usuario" not in session:
        return redirect(url_for("login"))

    itens_aleatorios = df["Descrição do Item"].dropna().unique().tolist()
    if request.method == "POST":
        return redirect(url_for("sucesso"))

    return render_template("upload_fotos.html", itens=itens_aleatorios)

@app.route("/mapeamento", methods=["GET", "POST"])
def mapeamento():
    if "usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        total_itens = int(request.form.get("total_itens", 0))
        precos = []
        for i in range(total_itens):
            nome = request.form.get(f"nome_{i}")
            preco = request.form.get(f"preco_{i}")
            if nome and preco:
                precos.append((nome, preco))

        print("Preços mapeados:")
        for nome, preco in precos:
            print(f"{nome}: R$ {preco}")

        return redirect(url_for("upload_fotos"))

    # GET: mostra todos os itens únicos do Excel
    itens_completos = df["Descrição do Item"].dropna().unique().tolist()
    return render_template("mapeamento.html", itens=itens_completos)

def enviar_email(nome, email):
    remetente = "costavalmir2011@gmail.com"
    senha = "knnazlcxoxeuxklj"
    destinatario = "Pr3cin.econ@outlook.com"

    corpo = f"Novo cadastro:\n\nNome: {nome}\nEmail: {email}"
    msg = MIMEText(corpo)
    msg["Subject"] = "Novo Cadastro no Pr3cin"
    msg["From"] = remetente
    msg["To"] = destinatario

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(remetente, senha)
        servidor.send_message(msg)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

