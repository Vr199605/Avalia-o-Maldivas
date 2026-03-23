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

# ========== INTERFACE ==========
st.set_page_config(page_title="Avaliação Maldivas", layout="wide")

with st.sidebar:
    st.header("🔑 Acesso Gestão")
    senha = st.text_input("Senha da Gestora", type="password")
    is_gestora = (senha == SENHA_GESTOR)

st.title("🏝️ PROGRAMA DE AVALIAÇÃO MALDIVAS")

# CAMPOS DE CABEÇALHO
col_cab1, col_cab2 = st.columns(2)
with col_cab1:
    nome_input = st.text_input("Nome do Avaliado*").strip()
    area_input = st.text_input("Qual sua área*")
with col_cab2:
    ano_input = st.selectbox("Qual ano", ["2026", "2027", "2028"])
    periodo_input = st.radio("Qual período", ["1º semestre", "2º semestre"], horizontal=True)
gestor_input = st.text_input("Gestor Direto*")

dados_existentes = carregar_dados_colaborador(nome_input) if nome_input else None

if dados_existentes:
    st.info(f"✅ Autoavaliação de **{nome_input}** carregada. Notas do colaborador estão fixadas.")

st.divider()

# LISTA DE PERGUNTAS (Adicionada a 10ª)
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
    "Assiduidade, pontualidade e compromisso com a jornada?" # Nova pergunta adicionada
]

notas_colab = []
notas_gestor = []
justificativas_colab = []
justificativas_gestor = []

for i, p in enumerate(perguntas):
    st.subheader(f"{i+1}. {p}")
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("**Colaborador**")
        v_padrao_c = dados_existentes['notas_c'][i] if dados_existentes else 3
        n_c = st.selectbox(f"Sua Nota", [1,2,3,4,5], index=v_padrao_c-1, key=f"nc_{i}", disabled=dados_existentes is not None)
        
        obs_c = ""
        if n_c in [1, 5]:
            v_obs_c = dados_existentes['just_c'][i] if dados_existentes else ""
            obs_c = st.text_area(f"Justificativa obrigatória (Nota {n_c})*", value=v_obs_c, key=f"obsc_{i}", disabled=dados_existentes is not None)
    
    with c2:
        st.markdown("**Gestão**")
        n_g = st.selectbox(f"Nota Gestor", [1,2,3,4,5], index=2, key=f"ng_{i}", disabled=not is_gestora)
        obs_g = st.text_area(f"Comentários da Gestão (Opcional)", key=f"obsg_{i}", disabled=not is_gestora)
    
    notas_colab.append(n_c)
    notas_gestor.append(n_g)
    justificativas_colab.append(obs_c)
    justificativas_gestor.append(obs_g)
    st.divider()

# PERGUNTA DISSERTATIVA FINAL (PRESERVADA)
st.write("**Visão Geral:**")
v_dissert = dados_existentes['dissert'] if dados_existentes else ""
dissertativa_input = st.text_area("Como você enxerga seu papel no crescimento da empresa nos próximos meses? Como podemos ajudar?*", value=v_dissert, disabled=dados_existentes is not None)

# ========== LÓGICA DE ENVIO ==========

# 1. BOTÃO DO COLABORADOR (Só aparece se não houver dados salvos)
if not dados_existentes:
    if st.button("Enviar minha Autoavaliação", use_container_width=True):
        if not nome_input or not area_input or not dissertativa_input:
            st.error("Por favor, preencha todos os campos obrigatórios (Nome, Área e Pergunta Final).")
        else:
            # Validar justificativas 1 e 5
            erro_just = False
            for i, nota in enumerate(notas_colab):
                if nota in [1, 5] and len(justificativas_colab[i].strip()) < 5:
                    st.error(f"A pergunta {i+1} exige justificativa para a nota {nota}.")
                    erro_just = True
            
            if not erro_just:
                dados_save = {
                    "notas_c": notas_colab, 
                    "just_c": justificativas_colab, 
                    "dissert": dissertativa_input,
                    "area": area_input,
                    "gestor": gestor_input,
                    "ano": ano_input,
                    "periodo": periodo_input
                }
                salvar_dados_colaborador(nome_input, dados_save)
                st.success("Autoavaliação salva com sucesso! Agora a gestora pode finalizar.")
                st.balloons()

# 2. BOTÃO DA GESTORA (Só aparece se for gestora e houver dados do colab)
elif is_gestora:
    if st.button("Finalizar Avaliação e Gerar Média (40/60)", type="primary", use_container_width=True):
        m_c = sum(notas_colab) / len(notas_colab)
        m_g = sum(notas_gestor) / len(notas_gestor)
        media_final = (m_c * 0.40) + (m_g * 0.60)
        
        st.write(f"### Média Final Calculada: {media_final:.2f}")
        st.success("Processando PDF e enviando e-mail...")
        
        # Aqui chamaria as funções de PDF e E-mail (gerar_pdf e enviar_email)
        # que você já tem no código original, passando os novos parâmetros.
        st.balloons()
