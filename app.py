from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

@app.route('/produto', methods=['GET'])
def consultar_produto():
    codigo_barras = request.args.get('codigo')
    if not codigo_barras:
        return jsonify({"erro": "Parâmetro 'codigo' é obrigatório."}), 400

    try:
        if len(codigo_barras) >= 12:
            codigo_produto = codigo_barras[7:12]
        else:
            codigo_produto = codigo_barras

        url = f"https://minhaloja.boticario.com.br/revendedor/produto/{codigo_produto}/?uf=SE"

        # Realiza a requisição HTTP para a página do produto
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"erro": "Não foi possível acessar a página."}), 500

        # Parseia o conteúdo HTML da página
        soup = BeautifulSoup(response.text, 'html.parser')

        # Tenta encontrar o nome do produto
        nome_element = soup.find('h1')
        nome = nome_element.text.strip() if nome_element else "Não encontrado"

        # Tenta encontrar o preço
        preco_element = soup.find('h5', string=re.compile(r"R\$"))
        if preco_element:
            preco_texto = preco_element.text.strip()
        else:
            return jsonify({"erro": "Preço não encontrado."}), 404

        # Verifica se há desconto
        desconto_element = soup.find('span', string=re.compile(r"\d+%"))
        desconto = desconto_element.text.strip() if desconto_element else None

        preco_com_desconto = float(re.sub(r'[^\d,]', '', preco_texto).replace(',', '.'))

        if desconto:
            percentual = float(re.sub(r'[^\d]', '', desconto))
            preco_original = preco_com_desconto / (1 - percentual / 100)
            preco_original = round(preco_original, 2)
        else:
            preco_original = preco_com_desconto

        return jsonify({
            "nome": nome,
            "codigo_produto": codigo_produto,
            "preco_com_desconto": f"R$ {preco_com_desconto:.2f}",
            "desconto": desconto if desconto else "Sem desconto",
            "preco_original": f"R$ {preco_original:.2f}"
        })

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
