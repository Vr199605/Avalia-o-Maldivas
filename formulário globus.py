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

# ========== CONFIGURAÇÕES ==========
# ⚠️ IMPORTANTE: Substitua pelos seus dados reais.
EMAIL_ORIGEM = "victormoreiraicnv@gmail.com" 
SENHA_APP = "hlvu kwvm tyfw pxem" 

# AGORA VOCÊ PODE ADICIONAR VÁRIOS E-MAILS AQUI:
EMAIL_DESTINO = ["victormoreiraicnv@gmail.com"]

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

# ========== GERAR PDF (LAYOUT PREMIUM) ==========
def gerar_pdf_final(dados_cabecalho, perguntas, n_colab, n_gestor, j_colab, j_gestor, dissert, m_final, cargo_avaliador):
    nome_limpo = dados_cabecalho['Nome'].replace(' ', '_')
    arquivo_pdf = f"AVALIACAO_{nome_limpo}.pdf"
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    width, height = A4
    
    # Cabeçalho Azul Institucional
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 45, "RELATÓRIO DE DESEMPENHO")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 70, f"Programa Maldivas | Período: {dados_cabecalho['Periodo']}")
    
    # Informações do Colaborador
    c.setFillColor(colors.black)
    y = height - 130
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, f"COLABORADOR: {dados_cabecalho['Nome'].upper()}")
    c.drawString(350, y, f"ÁREA: {dados_cabecalho['Area'].upper()}")
    y -= 18
    c.setFont("Helvetica", 9)
    c.drawString(50, y, f"AVALIADOR: {dados_cabecalho['Gestor']}")
    c.drawString(350, y, f"DATA DE EMISSÃO: {time.strftime('%d/%m/%Y')}")
    
    y -= 10
    c.setStrokeColor(colors.lightgrey)
    c.line(50, y, width - 50, y)
    y -= 30

    # Iteração das Perguntas
    for i, p in enumerate(perguntas):
        if y < 150:
            c.showPage()
            y = height - 60
            
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor("#1E3A8A"))
        c.drawString(50, y, f"{i+1}. {p}")
        y -= 15
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(60, y, f"Nota Autoavaliação: {n_colab[i]}")
        c.drawString(200, y, f"Nota {cargo_avaliador.upper()}: {n_gestor[i]}")
        y -= 12
        
        c.setFont("Helvetica-Oblique", 8)
        if j_colab[i]:
            c.setFillColor(colors.gray)
            c.drawString(60, y, f"Justificativa Colab: {j_colab[i][:110]}")
            y -= 10
        if j_gestor[i]:
            c.setFillColor(colors.HexColor("#2563EB"))
            c.drawString(60, y, f"Obs {cargo_avaliador}: {j_gestor[i][:110]}")
            y -= 10
            
        y -= 15
        c.setStrokeColor(colors.whitesmoke)
        c.line(60, y, width - 50, y)
        y -= 20

    # Visão de Futuro
    if y < 180: c.showPage(); y = height - 60
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.drawString(50, y, "VISÃO DE FUTURO E PAPEL NO CRESCIMENTO:")
    y -= 15
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    
    texto_dissert = c.beginText(50, y)
    texto_dissert.setFont("Helvetica", 9)
    texto_dissert.setLeading(12)
    lines = [dissert[i:i+95] for i in range(0, len(dissert), 95)]
    for line in lines:
        texto_dissert.textLine(line)
    c.drawText(texto_dissert)
    
    y_footer = 80
    c.setFillColor(colors.HexColor("#F3F4F6"))
    c.rect(50, y_footer - 10, width - 100, 40, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, y_footer + 10, f"MÉDIA FINAL PONDERADA: {m_final:.2f}")
    
    c.save()
    return arquivo_pdf

def enviar_email(nome, arquivo_pdf, media):
    # Converte a lista de destinos em uma string separada por vírgula para o cabeçalho "To"
    destinatarios_str = ", ".join(EMAIL_DESTINO) if isinstance(EMAIL_DESTINO, list) else EMAIL_DESTINO
    
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = destinatarios_str
    msg["Subject"] = f"Avaliação Maldivas Concluída: {nome}"
    corpo = f"Prezados,\n\nA avaliação de desempenho de {nome} foi finalizada com sucesso.\n\nMédia Final Ponderada: {media:.2f}\n\nO relatório detalhado segue em anexo."
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
        # Envia para a lista completa
        server.send_message(msg); server.quit()
        return True
    except Exception as e:
        st.error(f"Erro no envio: {e}")
        return False

# ========== INTERFACE STREAMLIT ==========
st.set_page_config(page_title="Avaliação Maldivas", layout="wide")

nome_para_carregar = "" 

with st.sidebar:
    st.header("🔐 Gestão e Direção")
    senha_input = st.text_input("Senha de Acesso", type="password")
    is_gestora = (senha_input == SENHA_GESTOR)
    is_diretora = (senha_input == SENHA_DIRETORA)
    
    if is_gestora or is_diretora:
        st.success(f"Acesso { 'Gestora' if is_gestora else 'Diretora' }")
        st.divider()
        lista_pendentes = listar_avaliacoes_pendentes()
        if lista_pendentes:
            selecionado = st.selectbox("Colaboradores para Avaliar:", [""] + lista_pendentes)
            if selecionado: nome_para_carregar = selecionado
        
        if is_diretora:
            st.divider()
            if st.button("Limpar Ciclo Atual"):
                for f in glob.glob(os.path.join(PASTA_DADOS, "*.json")): os.remove(f)
                st.rerun()

st.title("🏝️ PROGRAMA DE AVALIAÇÃO MALDIVAS")

dados_existentes = carregar_dados_colaborador(nome_para_carregar) if nome_para_carregar else None
is_bloqueado = dados_existentes is not None

col_cab1, col_cab2 = st.columns(2)
with col_cab1:
    nome_input = st.text_input("Nome Completo*", value=nome_para_carregar, disabled=is_bloqueado).strip()
    v_area = dados_existentes.get('area', "") if is_bloqueado else ""
    area_input = st.text_input("Sua Área*", value=v_area, disabled=is_bloqueado)

with col_cab2:
    v_ano = dados_existentes.get('ano', "2026") if is_bloqueado else "2026"
    ano_input = st.selectbox("Ano de Referência", ["2026", "2027", "2028"], index=["2026", "2027", "2028"].index(v_ano), disabled=is_bloqueado)
    v_per = dados_existentes.get('periodo', "1º semestre") if is_bloqueado else "1º semestre"
    periodo_input = st.radio("Semestre", ["1º semestre", "2º semestre"], index=0 if v_per == "1º semestre" else 1, horizontal=True, disabled=is_bloqueado)

v_gestor = dados_existentes.get('gestor', "") if is_bloqueado else ""
gestor_input = st.text_input("Avaliador Responsável*", value=v_gestor, disabled=is_bloqueado)

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
        v_nota_c = dados_existentes.get('notas_c', [3]*10)[i] if is_bloqueado else 3
        n_c = st.selectbox(f"Sua Nota", [1,2,3,4,5], index=v_nota_c-1, key=f"nc_{i}", disabled=is_bloqueado)
        v_obs_c = dados_existentes.get('just_c', [""]*10)[i] if is_bloqueado else ""
        obs_c = st.text_area(f"Justificativa", value=v_obs_c, key=f"obsc_{i}", disabled=is_bloqueado) if n_c in [1, 5] else ""
    
    with c2:
        st.markdown("**Avaliação Gestão**")
        n_g = st.selectbox(f"Nota Gestão", [1,2,3,4,5], index=2, key=f"ng_{i}", disabled=not (is_gestora or is_diretora))
        obs_g = st.text_area(f"Observações Gestão", key=f"obsg_{i}", disabled=not (is_gestora or is_diretora))
    
    notas_colab.append(n_c); notas_gestor.append(n_g)
    just_colab.append(obs_c); just_gestor.append(obs_g)

v_dissert = dados_existentes.get('dissert', "") if is_bloqueado else ""
dissert_input = st.text_area("Como você enxerga seu papel no crescimento da empresa nos próximos meses? Como podemos ajudar?*", value=v_dissert, disabled=is_bloqueado)

# ========== BOTÕES DE EXECUÇÃO ==========
if not is_bloqueado:
    if st.button("Enviar minha Autoavaliação", type="primary", use_container_width=True):
        if nome_input and area_input and dissert_input:
            dados_save = {"notas_c": notas_colab, "just_c": just_colab, "dissert": dissert_input, "area": area_input, "gestor": gestor_input, "periodo": periodo_input, "ano": ano_input}
            salvar_dados_colaborador(nome_input, dados_save)
            st.success("✅ Autoavaliação enviada com sucesso!")
            time.sleep(1); st.rerun()
        else:
            st.error("⚠️ Preencha Nome, Área e a Pergunta Final.")

elif is_gestora or is_diretora:
    label = "Gestora" if is_gestora else "Diretora"
    if st.button(f"Finalizar Avaliação e Gerar Média (40/60)", type="primary", use_container_width=True):
        with st.spinner("Gerando Relatório de Performance..."):
            m_final = ((sum(notas_colab)/10) * 0.4) + ((sum(notas_gestor)/10) * 0.6)
            cab = {"Nome": nome_input, "Area": area_input, "Gestor": gestor_input, "Periodo": periodo_input}
            path = gerar_pdf_final(cab, perguntas, notas_colab, notas_gestor, just_colab, just_gestor, dissert_input, m_final, label)
            if enviar_email(nome_input, path, m_final):
                st.success(f"✅ Relatório de {nome_input} enviado para os destinatários selecionados!"); st.balloons()
                if os.path.exists(path): os.remove(path)
            else:
                st.error("❌ Erro técnico ao enviar o e-mail.")
