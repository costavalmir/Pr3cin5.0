
from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Carrega os dados do Excel
df = pd.read_excel("compras_05-04-2025.xlsx")
df["Descrição do Item"] = df["Descrição do Item"].astype(str)
df["Valor Unitário"] = pd.to_numeric(df["Valor Unitário"], errors="coerce")

# Remove duplicatas e ordena os produtos
produtos_unicos = sorted(df["Descrição do Item"].dropna().unique())

@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html", produtos=produtos_unicos)

@app.route("/resultado", methods=["POST"])
def resultado():
    itens_selecionados = request.form.getlist("produto")
    quantidades = request.form.getlist("quantidade")

    if not itens_selecionados:
        return "Nenhum item selecionado."

    resultado = []
    economia_total = 0
    gasto_total = 0
    resultado_por_mercado = {}

    for item, qtde in zip(itens_selecionados, quantidades):
        qtde = int(qtde) if qtde.isdigit() else 1
        dados_item = df[df["Descrição do Item"] == item]
        if not dados_item.empty:
            dados_item = dados_item.sort_values("Valor Unitário")
            local_mais_barato = dados_item.iloc[0]
            local_mais_caro = dados_item.iloc[-1]

            valor_unitario = local_mais_barato["Valor Unitário"]
            valor_total = valor_unitario * qtde
            economia = (local_mais_caro["Valor Unitário"] - valor_unitario) * qtde

            economia_total += economia
            gasto_total += valor_total

            local = local_mais_barato["Local"]
            item_resultado = {
                "item": item,
                "quantidade": qtde,
                "local": local,
                "valor_unitario": round(valor_unitario, 2),
                "valor_total": round(valor_total, 2)
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
    app.run(debug=True)
