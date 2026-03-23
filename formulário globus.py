import streamlit as st
import os
import json
import smtplib
import glob
import time
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

# ========== CONFIGURAÇÕES ==========
EMAIL_ORIGEM = "victormoreiraicnv@gmail.com" 
SENHA_APP = "hlvu kwvm tyfw pxem" 
EMAIL_DESTINO = ["victormoreiraicnv@gmail.com"] # Pode adicionar mais aqui

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

# ========== GERAR PDF (LAYOUT PERFEIÇÃO) ==========
def gerar_pdf_final(dados_cabecalho, perguntas, n_colab, n_gestor, j_colab, j_gestor, dissert, m_final, cargo_avaliador):
    nome_limpo = dados_cabecalho['Nome'].replace(' ', '_')
    arquivo_pdf = f"AVALIACAO_{nome_limpo}.pdf"
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    width, height = A4
    
    # --- Fundo do Cabeçalho ---
    c.setFillColor(colors.HexColor("#0F172A")) # Azul Navy Profundo
    c.rect(0, height - 120, width, 120, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 55, "AVALIAÇÃO DE PERFORMANCE")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.drawString(50, height - 75, f"CICLO DE DESEMPENHO MALDIVAS | {dados_cabecalho['Periodo'].upper()}")
    
    # --- Box de Informações ---
    y_box = height - 110
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.roundRect(40, y_box - 75, width - 80, 85, 6, fill=1, stroke=1)
    
    c.setFillColor(colors.HexColor("#1E293B"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y_box - 25, f"COLABORADOR: {dados_cabecalho['Nome'].upper()}")
    c.drawString(320, y_box - 25, f"ÁREA: {dados_cabecalho['Area'].upper()}")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#475569"))
    c.drawString(60, y_box - 45, f"AVALIADOR: {dados_cabecalho['Gestor']}")
    c.drawString(320, y_box - 45, f"ANO: {dados_cabecalho['Ano']}")
    c.drawString(60, y_box - 60, f"DATA DO RELATÓRIO: {time.strftime('%d/%m/%Y %H:%M')}")

    # --- Conteúdo (Perguntas) ---
    y = y_box - 110
    
    for i, p in enumerate(perguntas):
        if y < 130:
            c.showPage()
            y = height - 60
            
        # Título da Pergunta
        c.setFillColor(colors.HexColor("#0F172A"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, f"{i+1}. {p}")
        y -= 22
        
        # Grid de Notas (Barras Visuais)
        # Nota Colaborador
        c.setFillColor(colors.HexColor("#64748B"))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(60, y, f"AUTOAVALIAÇÃO: {n_colab[i]}")
        # Desenha barra de progresso nota colab
        c.setFillColor(colors.HexColor("#CBD5E1"))
        c.rect(160, y - 2, 50, 6, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#64748B"))
        c.rect(160, y - 2, (n_colab[i]/5)*50, 6, fill=1, stroke=0)

        # Nota Gestão
        c.setFillColor(colors.HexColor("#2563EB"))
        c.drawString(240, y, f"NOTA {cargo_avaliador.upper()}: {n_gestor[i]}")
        # Desenha barra de progresso nota gestão
        c.setFillColor(colors.HexColor("#DBEAFE"))
        c.rect(340, y - 2, 50, 6, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#2563EB"))
        c.rect(340, y - 2, (n_gestor[i]/5)*50, 6, fill=1, stroke=0)
        
        y -= 15
        
        # Comentários
        c.setFont("Helvetica-Oblique", 8)
        if j_colab[i]:
            c.setFillColor(colors.HexColor("#64748B"))
            c.drawString(65, y, f"💬 Just. Colab: {j_colab[i][:115]}")
            y -= 12
        if j_gestor[i]:
            c.setFillColor(colors.HexColor("#1D4ED8"))
            c.drawString(65, y, f"📝 Obs {cargo_avaliador}: {j_gestor[i][:115]}")
            y -= 12
            
        y -= 15
        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.setLineWidth(0.5)
        c.line(50, y, width - 50, y)
        y -= 20

    # --- Seção Dissertativa ---
    if y < 180: c.showPage(); y = height - 60
    
    c.setFillColor(colors.HexColor("#F1F5F9"))
    c.roundRect(50, y - 90, width - 100, 100, 4, fill=1, stroke=0)
    
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y - 15, "VISÃO ESTRATÉGICA (CRESCIMENTO E APOIO):")
    
    y -= 35
    text_obj = c.beginText(60, y)
    text_obj.setFont("Helvetica", 9)
    text_obj.setFillColor(colors.HexColor("#334155"))
    text_obj.setLeading(12)
    
    # Quebra de texto automática
    from textwrap import wrap
    linhas = wrap(dissert, width=105)
    for linha in linhas[:5]: # Limite de 5 linhas no box
        text_obj.textLine(linha)
    c.drawText(text_obj)

    # --- Rodapé com Score Final ---
    y_footer = 80
    c.setFillColor(colors.HexColor("#1E293B"))
    c.rect(0, 0, width, 100, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, 60, f"SCORE FINAL: {m_final:.2f} / 5.00")
    
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#94A3B8"))
    c.drawCentredString(width/2, 40, "Este documento é confidencial e propriedade da Maldivas.")

    c.save()
    return arquivo_pdf

def enviar_email(nome, arquivo_pdf, media):
    destinatarios_str = ", ".join(EMAIL_DESTINO) if isinstance(EMAIL_DESTINO, list) else EMAIL_DESTINO
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = destinatarios_str
    msg["Subject"] = f"🎯 Avaliação Concluída: {nome}"
    
    corpo = f"Prezados,\n\nRelatório de Performance de {nome} gerado.\nScore Final: {media:.2f}\n\nO anexo contém o detalhamento visual completo."
    msg.attach(MIMEText(corpo, "plain"))
    
    try:
        with open(arquivo_pdf, "rb") as f:
            parte = MIMEBase("application", "pdf")
            parte.set_payload(f.read()); encoders.encode_base64(parte)
            parte.add_header("Content-Disposition", f"attachment; filename={os.path.basename(arquivo_pdf)}")
            msg.attach(parte)
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo(); server.starttls(); server.login(EMAIL_ORIGEM, SENHA_APP.replace(" ", ""))
        server.send_message(msg); server.quit()
        return True
    except Exception as e:
        st.error(f"Erro no envio: {e}")
        return False

# ========== INTERFACE STREAMLIT ==========
st.set_page_config(page_title="Avaliação Maldivas", layout="wide")

nome_para_carregar = "" 

with st.sidebar:
    st.header("🔐 Portal Administrativo")
    senha_input = st.text_input("Credencial", type="password")
    is_gestora = (senha_input == SENHA_GESTOR)
    is_diretora = (senha_input == SENHA_DIRETORA)
    
    if is_gestora or is_diretora:
        st.success(f"Acesso: { 'Gestora' if is_gestora else 'Diretora' }")
        st.divider()
        lista_pendentes = listar_avaliacoes_pendentes()
        if lista_pendentes:
            selecionado = st.selectbox("Escolha o Colaborador:", [""] + lista_pendentes)
            if selecionado: nome_para_carregar = selecionado
        
        if is_diretora:
            if st.button("🔥 Resetar Ciclo"):
                for f in glob.glob(os.path.join(PASTA_DADOS, "*.json")): os.remove(f)
                st.rerun()

st.title("🏝️ PROGRAMA DE AVALIAÇÃO MALDIVAS")

# Dados e Bloqueio
dados_existentes = carregar_dados_colaborador(nome_para_carregar) if nome_para_carregar else None
is_bloqueado = dados_existentes is not None

col_cab1, col_cab2 = st.columns(2)
with col_cab1:
    nome_input = st.text_input("Nome do Colaborador*", value=nome_para_carregar, disabled=is_bloqueado).strip()
    v_area = dados_existentes.get('area', "") if is_bloqueado else ""
    area_input = st.text_input("Departamento*", value=v_area, disabled=is_bloqueado)

with col_cab2:
    v_ano = dados_existentes.get('ano', "2026") if is_bloqueado else "2026"
    ano_input = st.selectbox("Ano", ["2026", "2027", "2028"], index=["2026", "2027", "2028"].index(v_ano), disabled=is_bloqueado)
    v_per = dados_existentes.get('periodo', "1º semestre") if is_bloqueado else "1º semestre"
    periodo_input = st.radio("Período de Avaliação", ["1º semestre", "2º semestre"], index=0 if v_per == "1º semestre" else 1, horizontal=True, disabled=is_bloqueado)

v_gestor = dados_existentes.get('gestor', "") if is_bloqueado else ""
gestor_input = st.text_input("Liderança Direta*", value=v_gestor, disabled=is_bloqueado)

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
        st.markdown("**Sua Autoavaliação**")
        v_nota_c = dados_existentes.get('notas_c', [3]*10)[i] if is_bloqueado else 3
        n_c = st.selectbox(f"Nota", [1,2,3,4,5], index=v_nota_c-1, key=f"nc_{i}", disabled=is_bloqueado)
        v_obs_c = dados_existentes.get('just_c', [""]*10)[i] if is_bloqueado else ""
        obs_c = st.text_area(f"Justificativa", value=v_obs_c, key=f"obsc_{i}", disabled=is_bloqueado) if n_c in [1, 5] else ""
    
    with c2:
        st.markdown("**Avaliação da Liderança**")
        n_g = st.selectbox(f"Nota Liderança", [1,2,3,4,5], index=2, key=f"ng_{i}", disabled=not (is_gestora or is_diretora))
        obs_g = st.text_area(f"Comentário da Gestão", key=f"obsg_{i}", disabled=not (is_gestora or is_diretora))
    
    notas_colab.append(n_c); notas_gestor.append(n_g)
    just_colab.append(obs_c); just_gestor.append(obs_g)

v_dissert = dados_existentes.get('dissert', "") if is_bloqueado else ""
dissert_input = st.text_area("Como você enxerga seu papel no crescimento da empresa nos próximos meses? Como podemos ajudar?*", value=v_dissert, disabled=is_bloqueado)

# ========== BOTÕES ==========
if not is_bloqueado:
    if st.button("Finalizar e Enviar Minha Autoavaliação", type="primary", use_container_width=True):
        if nome_input and area_input and dissert_input:
            dados_save = {"notas_c": notas_colab, "just_c": just_colab, "dissert": dissert_input, "area": area_input, "gestor": gestor_input, "periodo": periodo_input, "ano": v_ano}
            salvar_dados_colaborador(nome_input, dados_save)
            st.success("Autoavaliação salva! Aguarde o feedback da gestão.")
            time.sleep(1); st.rerun()
        else:
            st.error("Campos obrigatórios faltando.")

elif is_gestora or is_diretora:
    label = "Gestora" if is_gestora else "Diretora"
    if st.button(f"Emitir Relatório Final e Enviar PDF ({label})", type="primary", use_container_width=True):
        with st.spinner("Compilando dados visuais..."):
            m_final = ((sum(notas_colab)/10) * 0.4) + ((sum(notas_gestor)/10) * 0.6)
            cab = {"Nome": nome_input, "Area": area_input, "Gestor": gestor_input, "Periodo": periodo_input, "Ano": ano_input}
            path = gerar_pdf_final(cab, perguntas, notas_colab, notas_gestor, just_colab, just_gestor, dissert_input, m_final, label)
            if enviar_email(nome_input, path, m_final):
                st.success(f"Relatório enviado para a diretoria!"); st.balloons()
                if os.path.exists(path): os.remove(path)
