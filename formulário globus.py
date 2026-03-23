import streamlit as st
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

# ========== CONFIGURAÇÕES ==========
# ⚠️ SUBSTITUA PELOS SEUS DADOS REAIS
EMAIL_ORIGEM = "seu_email@gmail.com" 
SENHA_APP = "qnml kuiq eenv pcqx" # Insira os 16 dígitos sem espaços
EMAIL_DESTINO = "victormoreiraicnv@gmail.com"

# ========== GERAR PDF ==========
def gerar_pdf(dados_cabecalho, respostas, dissertativa, media_final):
    nome_limpo = dados_cabecalho['Nome'].replace(' ', '_')
    arquivo_pdf = f"AVALIACAO_MALDIVAS_{nome_limpo}.pdf"
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    width, height = A4

    titulo_style = ParagraphStyle("Titulo", fontSize=16, leading=20, alignment=1, textColor=colors.darkblue)
    pergunta_style = ParagraphStyle("Pergunta", fontSize=11, leading=14, textColor=colors.HexColor("#003366"))
    resposta_style = ParagraphStyle("Resposta", fontSize=10, leading=14, backColor=colors.whitesmoke, leftIndent=10)

    def draw_paragraph(text, style, x, y, max_width):
        p = Paragraph(text, style)
        w, h = p.wrap(max_width, 1000)
        p.drawOn(c, x, y - h)
        return h

    y = height - 50
    y -= draw_paragraph("🏝️ PROGRAMA DE AVALIAÇÃO DE DESEMPENHO INDIVIDUAL MALDIVAS", titulo_style, 50, y, width - 100) + 20
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, f"Colaborador: {dados_cabecalho['Nome']} | Ano: {dados_cabecalho['Ano']} | Período: {dados_cabecalho['Periodo']}")
    y -= 15
    c.drawString(50, y, f"Área: {dados_cabecalho['Area']} | Gestor: {dados_cabecalho['Gestor']}")
    y -= 30

    for i, (pergunta, nota, justificativa) in enumerate(respostas, start=1):
        if y < 150: 
            c.showPage()
            y = height - 50
        
        y -= draw_paragraph(f"<b>{i}. {pergunta}</b> - Nota: {nota}", pergunta_style, 50, y, width - 100) + 5
        if justificativa:
            y -= draw_paragraph(f"Justificativa: {justificativa}", resposta_style, 50, y, width - 100) + 10
        y -= 15

    if y < 150:
        c.showPage()
        y = height - 50

    y -= draw_paragraph("<b>Visão de Futuro e Suporte:</b>", pergunta_style, 50, y, width - 100) + 5
    y -= draw_paragraph(dissertativa, resposta_style, 50, y, width - 100) + 20

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"MÉDIA FINAL (Ponderada 40%): {media_final:.2f}")
    
    c.save()
    return arquivo_pdf

# ========== ENVIAR E-MAIL ==========
def enviar_email(nome, arquivo_pdf, media):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = EMAIL_DESTINO
    msg["Subject"] = f"Avaliação Maldivas - {nome}"
    
    corpo = f"Avaliação de {nome} concluída.\nMédia Final: {media:.2f}\n\nO PDF detalhado está em anexo."
    msg.attach(MIMEText(corpo, "plain"))

    try:
        with open(arquivo_pdf, "rb") as f:
            parte = MIMEBase("application", "pdf")
            parte.set_payload(f.read())
            encoders.encode_base64(parte)
            parte.add_header("Content-Disposition", f"attachment; filename={os.path.basename(arquivo_pdf)}")
            msg.attach(parte)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ORIGEM, SENHA_APP.replace(" ", "")) 
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"ERRO DE ENVIO: {e}") 
        return False

# ========== INTERFACE STREAMLIT ==========
st.set_page_config(page_title="Avaliação Maldivas", layout="centered")
st.title("🏝️ PROGRAMA DE AVALIAÇÃO DE DESEMPENHO INDIVIDUAL MALDIVAS")

# CAMPOS DE CABEÇALHO
col1, col2 = st.columns(2)
with col1:
    nome_input = st.text_input("Nome do Avaliado*")
    area_input = st.text_input("Qual sua área*")
with col2:
    ano_input = st.selectbox("Qual ano", ["2026", "2027", "2028"])
    periodo_input = st.radio("Qual período", ["1º semestre", "2º semestre"], horizontal=True)
gestor_input = st.text_input("Gestor Direto*")

st.divider()

# LISTA DE PERGUNTAS ATUALIZADA
perguntas_texto = [
    "Qualidade técnica e precisão nas tarefas operacionais?",
    "Cumprimento de prazos e organização de demandas?",
    "Proatividade em sugerir melhorias nos processos?",
    "Colaboração e trabalho em equipe?",
    "Resiliência e postura profissional sob pressão?",
    "Alinhamento com a cultura e valores da empresa?",
    "Capacidade de aprender e se adaptar a mudanças",
    "Proatividade na identificação e solução de problemas",
    "Comunicação clara e eficaz"
]

respostas_coletadas = []
notas_para_media = []

for i, p in enumerate(perguntas_texto):
    st.write(f"**{i+1}. {p}**")
    nota = st.selectbox(f"Selecione a nota (1-5)", options=[1, 2, 3, 4, 5], index=2, key=f"n_{i}")
    
    obs = ""
    if nota == 1 or nota == 5:
        obs = st.text_area(f"Justificativa obrigatória (Nota {nota})*", key=f"obs_{i}")
    
    respostas_coletadas.append((p, nota, obs))
    notas_para_media.append(nota)
    st.markdown("---")

with st.form("botao_final"):
    dissertativa_input = st.text_area("Como você enxerga seu papel no crescimento da empresa nos próximos meses? Como podemos ajudar?*")
    enviar = st.form_submit_button("Finalizar e Enviar Avaliação")

if enviar:
    erros = []
    if not nome_input or not area_input or not gestor_input or not dissertativa_input:
        erros.append("Preencha todos os campos obrigatórios.")
    
    for i, (p, nota, obs) in enumerate(respostas_coletadas):
        if (nota == 1 or nota == 5) and len(obs.strip()) < 5:
            erros.append(f"A pergunta {i+1} exige uma justificativa.")

    if erros:
        for erro in erros: st.error(erro)
    else:
        with st.spinner("Gerando avaliação e enviando e-mail..."):
            media_final = (sum(notas_para_media) / len(notas_para_media)) * 0.40
            dados = {"Nome": nome_input, "Ano": ano_input, "Periodo": periodo_input, "Area": area_input, "Gestor": gestor_input}
            
            pdf_path = gerar_pdf(dados, respostas_coletadas, dissertativa_input, media_final)
            
            if enviar_email(nome_input, pdf_path, media_final):
                st.success(f"Avaliação enviada com sucesso! Média Final: {media_final:.2f}")
                st.balloons()
            else:
                st.error("Erro ao enviar e-mail. Verifique a Senha de App no terminal.")
            
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
