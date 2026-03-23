import streamlit as st
import os
import json
import smtplib
import glob
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# ========== CONFIGURAÇÕES ==========
# ⚠️ IMPORTANTE: Use a "Senha de App" de 16 dígitos do Google, não sua senha normal.
EMAIL_ORIGEM = "victormoreiraicnv@gmail.com" 
SENHA_APP = "hlvu kwvm tyfw pxem" 
EMAIL_DESTINO = "victormoreiraicnv@gmail.com"
SENHA_GESTOR = "admin123" 
SENHA_DIRETORA = "diretoria2026" 
PASTA_DADOS = "avaliacoes_salvas"

if not os.path.exists(PASTA_DADOS):
    os.makedirs(PASTA_DADOS)

# ========== FUNÇÕES DE SISTEMA ==========
def salvar_dados_colaborador(nome, dados):
    nome_arq = nome.replace(" ", "_").lower()
    caminho = os.path.join(PASTA_DADOS, f"{nome_arq}.json")
    with open(caminho, "w") as f:
        json.dump(dados, f)

def carregar_dados_colaborador(nome):
    if not nome: return None
    nome_arq = nome.replace(" ", "_").lower()
    caminho = os.path.join(PASTA_DADOS, f"{nome_arq}.json")
    if os.path.exists(caminho):
        with open(caminho, "r") as f:
            return json.load(f)
    return None

def listar_avaliacoes_pendentes():
    arquivos = glob.glob(os.path.join(PASTA_DADOS, "*.json"))
    nomes = [os.path.basename(f).replace(".json", "").replace("_", " ").title() for f in arquivos]
    return sorted(nomes)

# ========== GERAR PDF ==========
def gerar_pdf_final(dados_cabecalho, perguntas, n_colab, n_gestor, j_colab, j_gestor, dissert, m_final, cargo_avaliador):
    nome_limpo = dados_cabecalho['Nome'].replace(' ', '_')
    arquivo_pdf = f"AVALIACAO_{cargo_avaliador.upper()}_{nome_limpo}.pdf"
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    width, height = A4
    
    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, y, f"🏝️ RESULTADO FINAL - AVALIAÇÃO {cargo_avaliador.upper()}")
    y -= 40
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, f"Avaliado: {dados_cabecalho['Nome']} | Área: {dados_cabecalho['Area']}")
    y -= 15
    c.drawString(50, y, f"Avaliador: {dados_cabecalho['Gestor']} | Período: {dados_cabecalho['Periodo']}")
    y -= 30

    for i, p in enumerate(perguntas):
        if y < 120:
            c.showPage()
            y = height - 50
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y, f"{i+1}. {p}")
        y -= 15
        c.setFont("Helvetica", 9)
        c.drawString(60, y, f"Nota Avaliado: {n_colab[i]} | Nota {cargo_avaliador}: {n_gestor[i]}")
        y -= 12
        if j_colab[i]:
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(60, y, f"Just. Avaliado: {j_colab[i][:95]}")
            y -= 10
        if j_gestor[i]:
            c.setFillColor(colors.blue)
            c.drawString(60, y, f"Obs {cargo_avaliador}: {j_gestor[i][:95]}")
            c.setFillColor(colors.black)
            y -= 10
        y -= 15

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"MÉDIA FINAL PONDERADA (40/60): {m_final:.2f}")
    c.save()
    return arquivo_pdf

def enviar_email(nome, arquivo_pdf, media):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = EMAIL_DESTINO
    msg["Subject"] = f"Avaliação Maldivas Concluída - {nome}"
    corpo = f"A avaliação de {nome} foi finalizada.\nMédia Final Ponderada: {media:.2f}\n\nO PDF detalhado segue em anexo."
    msg.attach(MIMEText(corpo, "plain"))
    try:
        with open(arquivo_pdf, "rb") as f:
            parte = MIMEBase("application", "pdf")
            parte.set_payload(f.read()); encoders.encode_base64(parte)
            parte.add_header("Content-Disposition", f"attachment; filename={os.path.basename(arquivo_pdf)}")
            msg.attach(parte)
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo(); server.starttls(); server.ehlo()
        server.login(EMAIL_ORIGEM, SENHA_APP.replace(" ", ""))
        server.send_message(msg); server.quit()
        return True
    except Exception as e:
        st.error(f"Erro técnico no envio: {e}")
        return False

# ========== INTERFACE STREAMLIT ==========
st.set_page_config(page_title="Avaliação Maldivas", layout="wide")

nome_para_carregar = "" # Inicializa para evitar NameError

with st.sidebar:
    st.header("🔐 Área de Gestão/Direção")
    senha_input = st.text_input("Digite sua Senha", type="password")
    
    is_gestora = (senha_input == SENHA_GESTOR)
    is_diretora = (senha_input == SENHA_DIRETORA)
    
    if is_gestora or is_diretora:
        cargo_ativo = "Gestora" if is_gestora else "Diretora"
        st.success(f"Modo {cargo_ativo} Ativo")
        st.divider()
        st.subheader("📋 Pendentes de Avaliação")
        lista_pendentes = listar_avaliacoes_pendentes()
        if lista_pendentes:
            selecionado = st.selectbox("Selecione para avaliar:", [""] + lista_pendentes)
            if selecionado:
                nome_para_carregar = selecionado
        else:
            st.write("Nenhuma autoavaliação encontrada.")

st.title("🏝️ PROGRAMA DE AVALIAÇÃO MALDIVAS")

col_cab1, col_cab2 = st.columns(2)
with col_cab1:
    nome_input = st.text_input("Nome do Avaliado*", value=nome_para_carregar).strip()
    area_input = st.text_input("Qual sua área*")
with col_cab2:
    ano_input = st.selectbox("Qual ano", ["2026", "2027", "2028"])
    periodo_input = st.radio("Qual período", ["1º semestre", "2º semestre"], horizontal=True)
gestor_input = st.text_input("Avaliador Direto*")

dados_existentes = carregar_dados_colaborador(nome_input) if nome_input else None

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
    "Comunicação clara e eficaz",
    "Assiduidade, pontualidade e compromisso com a jornada?"
]

notas_colab, notas_gestor, just_colab, just_gestor = [], [], [], []

for i, p in enumerate(perguntas):
    st.subheader(f"{i+1}. {p}")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Autoavaliação**")
        v_padrao_c = dados_existentes['notas_c'][i] if dados_existentes else 3
        n_c = st.selectbox(f"Nota Colaborador", [1,2,3,4,5], index=v_padrao_c-1, key=f"nc_{i}", disabled=dados_existentes is not None)
        v_obs_c = dados_existentes['just_c'][i] if dados_existentes else ""
        obs_c = ""
        if n_c in [1, 5]:
            obs_c = st.text_area(f"Justificativa (Nota {n_c})*", value=v_obs_c, key=f"obsc_{i}", disabled=dados_existentes is not None)
    
    with c2:
        st.markdown("**Gestão/Direção**")
        n_g = st.selectbox(f"Nota Avaliador", [1,2,3,4,5], index=2, key=f"ng_{i}", disabled=not (is_gestora or is_diretora))
        obs_g = st.text_area(f"Comentários do Avaliador", key=f"obsg_{i}", disabled=not (is_gestora or is_diretora))
    
    notas_colab.append(n_c); notas_gestor.append(n_g)
    just_colab.append(obs_c); just_gestor.append(obs_g)

v_dissert = dados_existentes['dissert'] if dados_existentes else ""
dissert_input = st.text_area("Como você enxerga seu papel no crescimento da empresa nos próximos meses? Como podemos ajudar?*", value=v_dissert, disabled=dados_existentes is not None)

# ========== BOTÕES DE AÇÃO ==========
if not dados_existentes:
    if st.button("Enviar minha Autoavaliação", type="primary", use_container_width=True):
        if nome_input and area_input and dissert_input:
            dados_save = {"notas_c": notas_colab, "just_c": just_colab, "dissert": dissert_input, "area": area_input, "gestor": gestor_input, "periodo": periodo_input}
            salvar_dados_colaborador(nome_input, dados_save)
            st.success("Autoavaliação salva! Comunique sua gestão.")
            st.rerun()
        else:
            st.error("Preencha Nome, Área e a Pergunta Final.")

elif is_gestora or is_diretora:
    cargo_label = "Gestora" if is_gestora else "Diretora"
    if st.button(f"Finalizar Avaliação como {cargo_label}", type="primary", use_container_width=True):
        with st.spinner("Gerando PDF e enviando e-mail..."):
            m_c = sum(notas_colab) / len(notas_colab)
            m_g = sum(notas_gestor) / len(notas_gestor)
            m_final = (m_c * 0.4) + (m_g * 0.6)
            
            cabecalho = {"Nome": nome_input, "Area": area_input, "Gestor": gestor_input, "Periodo": periodo_input}
            pdf_path = gerar_pdf_final(cabecalho, perguntas, notas_colab, notas_gestor, just_colab, just_gestor, dissert_input, m_final, cargo_label)
            
            if enviar_email(nome_input, pdf_path, m_final):
                st.success(f"Avaliação finalizada! Média Ponderada: {m_final:.2f}")
                st.balloons()
                if os.path.exists(pdf_path): os.remove(pdf_path)
            else:
                st.error("Falha no envio do e-mail. Verifique as credenciais.")
