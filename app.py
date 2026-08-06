import io
import requests
import re
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from fpdf import FPDF
from datetime import datetime
from pypdf import PdfReader

app = Flask(__name__)
CORS(app)

def buscar_dados_cnpj(cnpj_limpo):
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def extrair_texto_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() + "\n"
        return texto
    except:
        return ""

def ler_pdf_simples(pdf_file):
    texto = extrair_texto_pdf(pdf_file)
    if not texto:
        return "NÃO Optante pelo Simples / SIMEI (Documento ilegível)"
    
    status_final = "NÃO Optante pelo Simples / SIMEI"
    if "Optante pelo Simples Nacional" in texto and "NÃO" not in texto.split("Optante pelo Simples Nacional")[0][-10:]:
        status_final = "OPTANTE pelo Simples Nacional"
        
    if "Exclusão" in texto or "Desenquadramento" in texto or "excluído" in texto.lower():
        status_final += " (Histórico de Exclusão identificado no documento da RFB)"
        
    return status_final

def ler_pdf_ade(pdf_file):
    texto = extrair_texto_pdf(pdf_file)
    if "discriminadas abaixo:" in texto:
        partes = texto.split("discriminadas abaixo:")
        pendencias = partes[1].split("Parágrafo único")[0].strip()
        pendencias = pendencias.replace("PGDASD", "PGDAS-D").replace("MENSAL", "\n• PGDAS-D MENSAL")
        return pendencias.strip()
    return "Pendências não detalhadas no documento."

class PDFRelatorio(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, 'Contatos: (21) 99292-0144 | E-mail: empodera@empoderacontabilidade.com.br', ln=True, align='C')
        self.ln(3)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(15, 44, 89)
        self.cell(0, 6, 'RELATÓRIO TÉCNICO DE DIAGNÓSTICO E REGULARIZAÇÃO DE CNPJ', ln=True, align='C')
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

@app.route('/gerar-pdf-completo', methods=['POST'])
def rota_completa():
    cnpj_recebido = request.form.get('cnpj', '')
    cnpj_limpo = ''.join(filter(str.isdigit, cnpj_recebido))
    
    dados_api = buscar_dados_cnpj(cnpj_limpo)
    razao_social = dados_api.get("razao_social", "N/A") if dados_api else "N/A"
    status = dados_api.get("descricao_situacao_cadastral", "INAPTA") if dados_api else "INAPTA"
    data_abertura = dados_api.get("data_inicio_atividade", "N/A") if dados_api else "N/A"
    natureza = dados_api.get("natureza_juridica", "N/A") if dados_api else "N/A"
    porte = dados_api.get("porte", "ME") if dados_api else "ME"
    nome_socio = "Sócio(s) Responsável(is)"
    if dados_api and dados_api.get("qsa"):
        nome_socio = dados_api["qsa"][0].get("nome_socio", nome_socio)

    regime = "Documento do Simples não enviado."
    if 'pdf_simples' in request.files and request.files['pdf_simples'].filename != '':
        regime = ler_pdf_simples(request.files['pdf_simples'])

    texto_pendencias = "Nenhuma pendência informada / ADE não enviado."
    if 'pdf_ade' in request.files and request.files['pdf_ade'].filename != '':
        texto_pendencias = ler_pdf_ade(request.files['pdf_ade'])

    pdf = PDFRelatorio()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, f"Cliente / Razão Social: {razao_social}", ln=True)
    pdf.cell(0, 5, f"CNPJ: {cnpj_recebido}", ln=True)
    pdf.cell(0, 5, f"Data da Análise: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(0, 5, f"Contadora Responsável: Cássia Anastacia", ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(15, 44, 89)
    pdf.cell(0, 6, "1. SITUAÇÃO ATUAL DA EMPRESA", ln=True)
    pdf.set_font("Arial", '', 9)
    pdf.set_text_color(0, 0, 0)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(45, 6, "Situação Cadastral", border=1)
    pdf.set_font("Arial", 'B', 9)
    pdf.set_text_color(200, 0, 0) if status == "INAPTA" else pdf.set_text_color(0, 150, 0)
    pdf.cell(145, 6, f" {status} (Identificado na base da RFB)", border=1, ln=True)
    pdf.set_text_color(0, 0, 0)
    
    x = pdf.get_x()
    y = pdf.get_y()
    pdf.cell(45, 20, "Pendências (Pública)", border=1)
    pdf.set_xy(x + 45, y)
    pdf.set_font("Arial", '', 8)
    pdf.multi_cell(145, 4, f"{texto_pendencias}", border=1)
    pdf.set_xy(x, pdf.get_y())
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(45, 6, "Regime Tributário", border=1)
    pdf.set_font("Arial", '', 8)
    pdf.cell(145, 6, f" {regime}", border=1, ln=True)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(45, 6, "Natureza / Porte", border=1)
    pdf.set_font("Arial", '', 8)
    pdf.cell(145, 6, f" {natureza} / {porte} (Aberta em {data_abertura})", border=1, ln=True)
    pdf.ln(4)

    pdf.set_fill_color(255, 235, 235)
    pdf.set_text_color(150, 0, 0)
    pdf.set_font("Arial", 'B', 8)
    pdf.multi_cell(0, 4, f"ATENÇÃO / RISCOS IMEDIATOS: A condição de Inaptidão paralisa as operações.\n- Inidoneidade de Documentos: Impedimento total de emitir notas.\n- Responsabilização do CPF: Pendências transferidas para {nome_socio}.", fill=True)
    pdf.ln(4)
    pdf.set_text_color(0, 0, 0)

    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(15, 44, 89)
    pdf.cell(0, 6, "2. OPÇÕES PARA DECISÃO DO CLIENTE", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "OPÇÃO A: Regularizar e Manter Ativo", ln=True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 4, f"- Passo 1: Transmissão de declarações em atraso.\n- Passo 2: Reversão automática para ATIVA após processamento.")
    pdf.ln(3)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, "OPÇÃO B: Regularizar e Baixar o CNPJ", ln=True)
    pdf.set_font("Arial", '', 9)
    pdf.multi_cell(0, 4, "- Passo 1: Entrega de declarações omitidas é requisito prévio.\n- Passo 2: Pedido de Baixa de encerramento do CNPJ.")
    pdf.ln(4)

    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(15, 44, 89)
    pdf.cell(0, 6, "3. PRÓXIMOS PASSOS E ATENDIMENTO", ln=True)
    pdf.set_font("Arial", '', 9)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 5, "Responda a esta mensagem no WhatsApp (21) 99292-0144 com a opção desejada. Solicitaremos o acesso via GOV.BR para o Levantamento Fiscal Completo.")

    return send_file(io.BytesIO(pdf.output(dest='S').encode('latin1')), mimetype='application/pdf', as_attachment=True, download_name=f'Relatorio_{cnpj_limpo}.pdf')

# ===== A MÁGICA ACONTECE AQUI: A TELA DO APLICATIVO =====
@app.route('/', methods=['GET'])
def index():
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Backoffice Empodera - Gerador de Relatórios</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #e9ecef; display: flex; justify-content: center; padding: 40px 20px; }
            .container { background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 600px; }
            h2 { color: #0f2c59; text-align: center; border-bottom: 2px solid #0f2c59; padding-bottom: 10px; }
            label { font-weight: bold; font-size: 14px; display: block; margin-top: 15px; }
            input[type="text"], input[type="file"] { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; background-color: #f8f9fa; }
            button { margin-top: 25px; width: 100%; background-color: #28a745; color: white; padding: 15px; border: none; font-size: 16px; font-weight: bold; border-radius: 5px; cursor: pointer; transition: 0.3s; }
            button:hover { background-color: #218838; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔧 GERADOR DE RELATÓRIOS (Uso Interno)</h2>
            <form action="/gerar-pdf-completo" method="POST" enctype="multipart/form-data">
                
                <label>1. CNPJ do Cliente:</label>
                <input type="text" name="cnpj" placeholder="Ex: 00.000.000/0000-00" required>
                
                <label style="color: #d9534f;">2. PDF Situação Cadastral (Consulta 1):</label>
                <input type="file" name="pdf_cadastral" accept="application/pdf">
                
                <label style="color: #0275d8;">3. PDF Simples Nacional (Consulta 2):</label>
                <input type="file" name="pdf_simples" accept="application/pdf">
                
                <label style="color: #5cb85c;">4. PDF Editais / ADE (Consulta 3):</label>
                <input type="file" name="pdf_ade" accept="application/pdf">
                
                <button type="submit">UNIFICAR PDFs E GERAR RELATÓRIO</button>
            </form>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    app.run(debug=True)
