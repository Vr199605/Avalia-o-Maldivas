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
EMAIL_ORIGEM = "seu_email@gmail.com" 
SENHA_APP = "qnml kuiq eenv pcqx" 
EMAIL_DESTINO = "victormoreiraicnv@gmail.com"
SENHA_GESTOR = "admin123" # Senha para liberar as notas da gestora

# ========== GERAR PDF ==========
def gerar_pdf(dados_cabecalho, respostas, dissertativa, media_colab, media_gestor, media_final):
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

    for i, (pergunta, n_colab, n_gestor, justificativa) in enumerate(respostas, start=1):
        if y < 150: 
            c.showPage()
            y = height - 50
        
        y -= draw_paragraph(f"<b>{i}. {pergunta}</b>", pergunta_style, 50, y, width - 100) + 5
        c.setFont("Helvetica", 10)
        c.drawString(60, y-10, f"Nota Colaborador: {n_colab} | Nota Gestor: {n_gestor}")
        y -= 20
        if justificativa:
            y -= draw_paragraph(f"Justificativa: {justificativa}", resposta_style, 50, y, width - 100) + 10
        y -= 10

    if y < 150:
        c.showPage()
        y = height - 50

    y -= draw_paragraph("<b>Visão de Futuro e Suporte:</b>", pergunta_style, 50, y, width - 100) + 5
    y -= draw_paragraph(dissertativa, resposta_style, 50, y, width - 100) + 20

    y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, f"Média Colaborador (40%): {media_colab:.2f}")
    y -= 15
    c.drawString(50, y, f"Média Gestor (60%): {media_gestor:.2f}")
    y -= 20
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.darkblue)
    c.drawString(50, y, f"PONTUAÇÃO FINAL: {media_final:.2f}")
    
    c.save()
    return arquivo_pdf

# ========== ENVIAR E-MAIL ==========
def enviar_email(nome, arquivo_pdf, media):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = EMAIL_DESTINO
    msg["Subject"] = f"Avaliação Maldivas - {nome}"
    
    corpo = f"Avaliação de {nome} concluída.\nMédia Final Ponderada: {media:.2f}\n\nO PDF detalhado está em anexo."
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
        return False

# ========== INTERFACE STREAMLIT ==========
st.set_page_config(page_title="Avaliação Maldivas", layout="centered")
st.title("🏝️ PROGRAMA DE AVALIAÇÃO DE DESEMPENHO INDIVIDUAL MALDIVAS")

# ÁREA DO GESTOR (OCULTA)
with st.sidebar:
    st.header("🔐 Área da Gestão")
    senha_acesso = st.text_input("Senha da Gestora", type="password")
    modo_gestor = senha_acesso == SENHA_GESTOR
    if senha_acesso and not modo_gestor:
        st.error("Senha incorreta")
    elif modo_gestor:
        st.success("Modo Gestora Ativo")

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
notas_colab = []
notas_gestor = []

for i, p in enumerate(perguntas_texto):
    st.write(f"**{i+1}. {p}**")
    
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        n_c = st.selectbox(f"Nota Colaborador", options=[1, 2, 3, 4, 5], index=2, key=f"nc_{i}")
    with c_col2:
        n_g = st.selectbox(f"Nota Gestor", options=[1, 2, 3, 4, 5], index=2, key=f"ng_{i}", disabled=not modo_gestor)
    
    obs = ""
    if n_c == 1 or n_c == 5 or (modo_gestor and (n_g == 1 or n_g == 5)):
        obs = st.text_area(f"Justificativa obrigatória (Notas 1 ou 5)*", key=f"obs_{i}")
    
    respostas_coletadas.append((p, n_c, n_g, obs))
    notas_colab.append(n_c)
    notas_gestor.append(n_g)
    st.markdown("---")

with st.form("botao_final"):
    dissertativa_input = st.text_area("Como você enxerga seu papel no crescimento da empresa nos próximos meses? Como podemos ajudar?*")
    enviar = st.form_submit_button("Finalizar e Enviar Avaliação")

if enviar:
    erros = []
    if not nome_input or not area_input or not gestor_input or not dissertativa_input:
        erros.append("Preencha todos os campos obrigatórios.")
    
    if erros:
        for erro in erros: st.error(erro)
    else:
        with st.spinner("Processando médias e enviando e-mail..."):
            m_c = sum(notas_colab) / len(notas_colab)
            m_g = sum(notas_gestor) / len(notas_gestor)
            # Cálculo 40% Colaborador + 60% Gestor
            media_final = (m_c * 0.40) + (m_g * 0.60)
            
            dados = {"Nome": nome_input, "Ano": ano_input, "Periodo": periodo_input, "Area": area_input, "Gestor": gestor_input}
            
            pdf_path = gerar_pdf(dados, respostas_coletadas, dissertativa_input, m_c, m_g, media_final)
            
            if enviar_email(nome_input, pdf_path, media_final):
                st.success(f"Avaliação enviada! Média Final Ponderada: {media_final:.2f}")
                st.balloons()
            else:
                st.error("Erro ao enviar e-mail.")
            
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
