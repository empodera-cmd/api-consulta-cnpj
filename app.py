import io
import requests
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from fpdf import FPDF

app = Flask(__name__)
# Permite que seu Google Sites faça requisições para esta API
CORS(app)

def buscar_dados_cnpj(cnpj_limpo):
    """Busca dados da empresa usando a BrasilAPI (gratuita)"""
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def criar_pdf(dados_empresa):
    """Gera o documento PDF com os dados encontrados"""
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(15, 44, 89) # Azul escuro (tom da sua marca)
    pdf.cell(0, 10, "Diagnóstico Preliminar de CNPJ", ln=True, align="C")
    pdf.ln(10)
    
    # Corpo do texto
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)
    
    if dados_empresa:
        # Extrai os dados principais
        razao_social = dados_empresa.get("razao_social", "N/A")
        cnpj = dados_empresa.get("cnpj", "N/A")
        status = dados_empresa.get("descricao_situacao_cadastral", "N/A")
        natureza = dados_empresa.get("natureza_juridica", "N/A")
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Razão Social: {razao_social}", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"CNPJ: {cnpj}", ln=True)
        pdf.cell(0, 10, f"Situação Cadastral: {status}", ln=True)
        pdf.cell(0, 10, f"Natureza Jurídica: {natureza}", ln=True)
        
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(255, 0, 0) # Vermelho para alerta
        pdf.multi_cell(0, 10, "Aviso: Este é um diagnóstico preliminar gerado pela Empodera Contabilidade. Para um parecer completo e orientações sobre Regularização, Baixa ou Continuidade do seu CNPJ, entre em contato com nosso time de especialistas.")
        
    else:
        pdf.cell(0, 10, "Não foi possível localizar os dados desse CNPJ.", ln=True)
        pdf.cell(0, 10, "Verifique se o número foi digitado corretamente.", ln=True)
        
    # Salva o PDF em memória
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return io.BytesIO(pdf_bytes)

@app.route('/gerar-pdf', methods=['POST'])
def gerar_pdf():
    dados = request.json
    cnpj_recebido = dados.get('cnpj', '')
    
    # Limpa o CNPJ (remove pontos, traços e barras)
    cnpj_limpo = ''.join(filter(str.isdigit, cnpj_recebido))
    
    if len(cnpj_limpo) != 14:
        return jsonify({"erro": "CNPJ inválido"}), 400
        
    # 1. Busca os dados
    dados_empresa = buscar_dados_cnpj(cnpj_limpo)
    
    # 2. Gera o PDF
    pdf_file = criar_pdf(dados_empresa)
    
    # 3. Retorna o PDF para download
    return send_file(
        pdf_file,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Diagnostico_CNPJ_{cnpj_limpo}.pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)
