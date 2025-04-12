from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'chave_super_secreta'  # Recomendado alterar para algo mais seguro

# Carrega os dados do Excel de compras
df = pd.read_excel("compras_05-04-2025.xlsx")
df["Descrição do Item"] = df["Descrição do Item"].astype(str)
df["Valor Unitário"] = pd.to_numeric(df["Valor Unitário"], errors="coerce")
produtos_unicos = sorted(df["Descrição do Item"].dropna().unique())

# Função para validar o login via Excel
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
    return render_template("index.html", produtos=produtos_unicos)

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

