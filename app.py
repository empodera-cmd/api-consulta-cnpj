import io
import requests
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from fpdf import FPDF
from datetime import datetime

app = Flask(__name__)
CORS(app)

def buscar_dados_cnpj(cnpj_limpo):
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

class PDFRelatorio(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Contatos: (21) 99292-0144 | E-mail: empodera@empoderacontabilidade.com.br', ln=True, align='C')
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(15, 44, 89)
        self.cell(0, 10, 'RELATÓRIO TÉCNICO DE DIAGNÓSTICO E REGULARIZAÇÃO DE CNPJ', ln=True, align='C')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

def gerar_pdf_isca(dados_empresa):
    """Gera o PDF Preliminar para o cliente no site público"""
    pdf = PDFRelatorio()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    if not dados_empresa:
        pdf.cell(0, 10, "Dados não encontrados. Entre em contato.", ln=True)
        return io.BytesIO(pdf.output(dest='S').encode('latin1'))

    pdf.cell(0, 6, f"Razão Social: {dados_empresa.get('razao_social', 'N/A')}", ln=True)
    pdf.cell(0, 6, f"CNPJ: {dados_empresa.get('cnpj', 'N/A')}", ln=True)
    pdf.cell(0, 6, f"Situação Cadastral: {dados_empresa.get('descricao_situacao_cadastral', 'N/A')}", ln=True)
    pdf.ln(10)
    
    pdf.set_fill_color(255, 235, 235)
    pdf.set_text_color(150, 0, 0)
    pdf.multi_cell(0, 8, "AVISO PRELIMINAR: Identificamos seu CNPJ na base da Receita Federal. Para emitir o relatório completo com cruzamento de dados de Omissões, Simples Nacional e Editais, entre em contato com nosso time pelo WhatsApp.", fill=True)
    
    return io.BytesIO(pdf.output(dest='S').encode('latin1'))

def gerar_pdf_completo(dados_empresa, manual_data):
    """Gera o PDF Completo (Backoffice) com as 3 consultas juntas"""
    pdf = PDFRelatorio()
    pdf.add_page()
    
    razao_social = dados_empresa.get("razao_social", "N/A") if dados_empresa else "N/A"
    cnpj = dados_empresa.get("cnpj", manual_data.get('cnpj', 'N/A')) if dados_empresa else manual_data.get('cnpj', 'N/A')
    data_abertura = dados_empresa.get("data_inicio_atividade", "N/A") if dados_empresa else "N/A"
    natureza = dados_empresa.get("natureza_juridica", "N/A") if dados_empresa else "N/A"
    
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, f"Cliente / Razão Social: {razao_social}", ln=True)
    pdf.cell(0, 6, f"CNPJ: {cnpj}", ln=True)
    pdf.cell(0, 6, f"Data da Análise: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(5)

    # SEÇÃO 1
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(15, 44, 89)
    pdf.cell(0, 8, "1. SITUAÇÃO ATUAL DA EMPRESA", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    
    # Tabela Simples
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(50, 6, "Situação Cadastral:", border=1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, manual_data.get('status', 'N/A'), border=1, ln=True)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(50, 6, "Pendências (Omissões):", border=1)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 6, manual_data.get('pendencias', 'Nenhuma identificada'), border=1)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(50, 6, "Regime Tributário:", border=1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, manual_data.get('regime', 'N/A'), border=1, ln=True)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(50, 6, "Natureza / Abertura:", border=1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 6, f"{natureza} (Aberta em {data_abertura})", border=1, ln=True)
    pdf.ln(5)

    pdf.set_fill_color(255, 235, 235)
    pdf.set_text_color(150, 0, 0)
    pdf.set_font("Arial", 'B', 9)
    pdf.multi_cell(0, 5, "ATENÇÃO / RISCOS IMEDIATOS: A condição de Inaptidão paralisa as operações legais da empresa e gera impactos imediatos:\n- Inidoneidade de Documentos: Impedimento total de emitir notas fiscais válidas.\n- Bloqueio Bancário: Restrições na conta e travamento financeiro.\n- Responsabilização do CPF: As pendências e débitos são transferidos para o CPF dos sócios.", fill=True)
    pdf.ln(5)

    # SEÇÃO 2
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(15, 44, 89)
    pdf.cell(0, 8, "2. OPÇÕES PARA DECISÃO DO CLIENTE", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, "OPÇÃO A: Regularização das Pendências e Manutenção do CNPJ Ativo", ln=True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 5, "Passo 1: Transmissão das declarações em atraso.\nPasso 2: Quitação/Parcelamento das multas para reversão do status para ATIVA.")
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, "OPÇÃO B: Regularização das Pendências e Baixa Definitiva do CNPJ", ln=True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 5, "Passo 1: Entrega das declarações omitidas (requisito obrigatório para baixa).\nPasso 2: Pedido de encerramento do CNPJ.")
    pdf.ln(5)

    # SEÇÃO 3
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(15, 44, 89)
    pdf.cell(0, 8, "3. PRÓXIMOS PASSOS", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 5, "1. Escolha a opção desejada (A ou B).\n2. Responda a esta mensagem no nosso WhatsApp.\n3. Solicitaremos o acesso via GOV.BR para o levantamento das guias.")

    return io.BytesIO(pdf.output(dest='S').encode('latin1'))

# ROTA 1: Site Público (Isca)
@app.route('/gerar-pdf', methods=['POST'])
def rota_isca():
    cnpj_limpo = ''.join(filter(str.isdigit, request.json.get('cnpj', '')))
    dados = buscar_dados_cnpj(cnpj_limpo)
    pdf_file = gerar_pdf_isca(dados)
    return send_file(pdf_file, mimetype='application/pdf', as_attachment=True, download_name=f'Preliminar_{cnpj_limpo}.pdf')

# ROTA 2: Backoffice (Relatório Completo)
@app.route('/gerar-pdf-completo', methods=['POST'])
def rota_completa():
    dados_manuais = request.json
    cnpj_limpo = ''.join(filter(str.isdigit, dados_manuais.get('cnpj', '')))
    dados_api = buscar_dados_cnpj(cnpj_limpo)
    pdf_file = gerar_pdf_completo(dados_api, dados_manuais)
    return send_file(pdf_file, mimetype='application/pdf', as_attachment=True, download_name=f'Completo_{cnpj_limpo}.pdf')

if __name__ == '__main__':
    app.run(debug=True)
