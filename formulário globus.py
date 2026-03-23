import streamlit as st
import os
import json
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
SENHA_GESTOR = "admin123" 
PASTA_DADOS = "avaliacoes_salvas"

if not os.path.exists(PASTA_DADOS):
    os.makedirs(PASTA_DADOS)

# ========== FUNÇÕES DE APOIO ==========
def salvar_dados_colaborador(nome, dados):
    nome_arq = nome.replace(" ", "_").lower()
    caminho = os.path.join(PASTA_DADOS, f"{nome_arq}.json")
    with open(caminho, "w") as f:
        json.dump(dados, f)

def carregar_dados_colaborador(nome):
    nome_arq = nome.replace(" ", "_").lower()
    caminho = os.path.join(PASTA_DADOS, f"{nome_arq}.json")
    if os.path.exists(caminho):
        with open(caminho, "r") as f:
            return json.load(f)
    return None

# ========== GERAR PDF (Média Final Ponderada) ==========
def gerar_pdf(dados_cabecalho, perguntas, notas_c, notas_g, dissertativa, m_final):
    nome_limpo = dados_cabecalho['Nome'].replace(' ', '_')
    arquivo_pdf = f"AVALIACAO_FINAL_{nome_limpo}.pdf"
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    width, height = A4
    
    # Estilos simples para manter o código limpo
    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, y, "AVALIAÇÃO DE DESEMPENHO - RESULTADO FINAL")
    y -= 30
    
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Colaborador: {dados_cabecalho['Nome']} | Gestor: {dados_cabecalho['Gestor']}")
    y -= 40

    for i, p in enumerate(perguntas):
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, f"{i+1}. {p}")
        y -= 15
        c.setFont("Helvetica", 10)
        c.drawString(60, y, f"Nota Colaborador: {notas_c[i]} | Nota Gestor: {notas_g[i]}")
        y -= 25

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"MÉDIA FINAL PONDERADA (40/60): {m_final:.2f}")
    c.save()
    return arquivo_pdf

def enviar_email(nome, arquivo_pdf, media):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = EMAIL_DESTINO
    msg["Subject"] = f"Avaliação Finalizada - {nome}"
    corpo = f"A avaliação de {nome} foi concluída com a participação da gestão.\nMédia Final: {media:.2f}"
    msg.attach(MIMEText(corpo, "plain"))
    try:
        with open(arquivo_pdf, "rb") as f:
            parte = MIMEBase("application", "pdf")
            parte.set_payload(f.read()); encoders.encode_base64(parte)
            parte.add_header("Content-Disposition", f"attachment; filename={os.path.basename(arquivo_pdf)}")
            msg.attach(parte)
        server = smtplib.SMTP("smtp.gmail.com", 587); server.starttls()
        server.login(EMAIL_ORIGEM, SENHA_APP.replace(" ", "")); server.send_message(msg); server.quit()
        return True
    except: return False

# ========== INTERFACE ==========
st.set_page_config(page_title="Avaliação Maldivas", layout="centered")

# Login da Gestora
with st.sidebar:
    st.header("🔑 Acesso Gestão")
    senha = st.text_input("Senha", type="password")
    is_gestora = (senha == SENHA_GESTOR)

st.title("🏝️ PROGRAMA DE AVALIAÇÃO MALDIVAS")

# Identificação
nome_input = st.text_input("Nome Completo do Colaborador*").strip()
dados_existentes = carregar_dados_colaborador(nome_input) if nome_input else None

if dados_existentes:
    st.info(f"✅ Notas do Colaborador carregadas. Aguardando avaliação da gestão.")
    if not is_gestora:
        st.warning("Apenas a gestora pode prosseguir com esta avaliação.")

st.divider()

perguntas = [
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

respostas_colab = []
respostas_gestor = []

for i, p in enumerate(perguntas):
    st.write(f"**{i+1}. {p}**")
    col1, col2 = st.columns(2)
    
    with col1:
        # Se já existe dado, a nota do colaborador fica travada (disabled)
        valor_padrao_c = dados_existentes['notas_c'][i] if dados_existentes else 3
        n_c = st.selectbox(f"Nota Colaborador", [1,2,3,4,5], index=valor_padrao_c-1, key=f"c_{i}", disabled=dados_existentes is not None)
    
    with col2:
        # Nota do gestor só habilita se for gestora E se o colab já tiver preenchido
        n_g = st.selectbox(f"Nota Gestor", [1,2,3,4,5], index=2, key=f"g_{i}", disabled=not is_gestora)
    
    respostas_colab.append(n_c)
    respostas_gestor.append(n_g)

dissertativa = st.text_area("Comentários/Visão de Futuro", value=dados_existentes['dissert'] if dados_existentes else "")

# Lógica de botões
if not dados_existentes:
    if st.button("Enviar minha Autoavaliação"):
        if nome_input:
            dados_para_salvar = {"notas_c": respostas_colab, "dissert": dissertativa}
            salvar_dados_colaborador(nome_input, dados_para_salvar)
            st.success("Sua avaliação foi salva! Agora peça para sua gestora acessar e finalizar.")
        else:
            st.error("Digite seu nome antes de enviar.")

elif is_gestora:
    if st.button("Finalizar Avaliação e Gerar Média (40/60)"):
        m_c = sum(respostas_colab) / len(respostas_colab)
        m_g = sum(respostas_gestor) / len(respostas_gestor)
        media_final = (m_c * 0.4) + (m_g * 0.6)
        
        cabecalho = {"Nome": nome_input, "Gestor": "Gestão Direta"}
        pdf = gerar_pdf(cabecalho, perguntas, respostas_colab, respostas_gestor, dissertativa, media_final)
        
        if enviar_email(nome_input, pdf, media_final):
            st.success(f"Avaliação de {nome_input} finalizada! Média: {media_final:.2f}")
            st.balloons()
