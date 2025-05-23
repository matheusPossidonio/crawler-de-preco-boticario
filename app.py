# app.py
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        driver.get(url)

        try:
            nome = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, 'h1'))
            ).text.strip()
        except:
            nome = "Não encontrado"

        preco_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//h5[contains(text(), "R$")]'))
        )
        preco_texto = preco_element.text.strip()

        desconto_element = driver.find_elements(By.XPATH, '//span[contains(text(), "%")]')
        desconto = desconto_element[0].text.strip() if desconto_element else None

        preco_com_desconto = float(re.sub(r'[^\d,]', '', preco_texto).replace(',', '.'))

        if desconto:
            percentual = float(re.sub(r'[^\d]', '', desconto))
            preco_original = preco_com_desconto / (1 - percentual / 100)
            preco_original = round(preco_original, 2)
        else:
            preco_original = preco_com_desconto

        driver.quit()

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
