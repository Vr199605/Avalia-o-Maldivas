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
EMAIL_DESTINO = ["victormoreiraicnv@gmail.com"]

SENHA_GESTOR = "admin123" 
SENHA_DIRETORA = "diretoria2026" 
PASTA_DADOS = "avaliacoes_salvas"
ARQUIVO_LOGO = os.path.join(PASTA_DADOS, "logo_maldivas.png") 

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

# ========== GERAR PDF (LAYOUT COM LOGO MAIOR) ==========
def gerar_pdf_final(dados_cabecalho, perguntas, n_colab, n_gestor, j_colab, j_gestor, dissert, m_final, cargo_avaliador):
    nome_limpo = dados_cabecalho['Nome'].replace(' ', '_')
    arquivo_pdf = f"AVALIACAO_{nome_limpo}.pdf"
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    width, height = A4
    
    # --- Fundo do Cabeçalho ---
    c.setFillColor(colors.HexColor("#0F172A"))
    c.rect(0, height - 120, width, 120, fill=1, stroke=0)
    
    # --- Adição da Logo no PDF ---
    if os.path.exists(ARQUIVO_LOGO):
        try:
            logo = ImageReader(ARQUIVO_LOGO)
            c.drawImage(logo, width - 180, height - 100, width=150, preserveAspectRatio=True, mask='auto')
        except:
            pass

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
            
        c.setFillColor(colors.HexColor("#0F172A"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, f"{i+1}. {p}")
        y -= 22
        
        c.setFillColor(colors.HexColor("#64748B"))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(60, y, f"AUTOAVALIAÇÃO: {n_colab[i]}")
        c.setFillColor(colors.HexColor("#CBD5E1"))
        c.rect(160, y - 2, 50, 6, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#64748B"))
        c.rect(160, y - 2, (n_colab[i]/5)*50, 6, fill=1, stroke=0)

        c.setFillColor(colors.HexColor("#2563EB"))
        c.drawString(240, y, f"NOTA {cargo_avaliador.upper()}: {n_gestor[i]}")
        c.setFillColor(colors.HexColor("#DBEAFE"))
        c.rect(340, y - 2, 50, 6, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#2563EB"))
        c.rect(340, y - 2, (n_gestor[i]/5)*50, 6, fill=1, stroke=0)
        
        y -= 15
        
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
    c.roundRect(50, y - 110, width - 100, 120, 4, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, y - 15, "VISÃO ESTRATÉGICA E APOIO:")
    y -= 35
    text_obj = c.beginText(60, y)
    text_obj.setFont("Helvetica", 9)
    text_obj.setFillColor(colors.HexColor("#334155"))
    text_obj.setLeading(12)
    from textwrap import wrap
    linhas = wrap(dissert, width=105)
    for linha in linhas[:7]:
        text_obj.textLine(linha)
    c.drawText(text_obj)

    # --- Rodapé ---
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

if os.path.exists(ARQUIVO_LOGO):
    st.image(ARQUIVO_LOGO, width=350)

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

with st.expander("ℹ️ LEGENDA DA ESCALA DE AVALIAÇÃO", expanded=True):
    st.markdown("""
    **1 – Muito abaixo do esperado:** desempenho insuficiente, não atende aos requisitos da função.  
    **2 – Abaixo do esperado:** atende parcialmente, com necessidade frequente de orientação.  
    **3 – Atende plenamente:** cumpre o que é esperado para a função.  
    **4 – Supera expectativas:** desempenho acima do esperado de forma consistente.  
    **5 – Destaque:** desempenho excepcional, referência para o time.  
    \**Campo obrigatório quando a avaliação dada for 1 ou 5*
    """)

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

perguntas_data = [
    {"pergunta": "Demonstro domínio técnico absoluto e precisão na execução das minhas tarefas operacionais.", "pilar": "Alta performance", "desc": "Excelência técnica: não permite erros básicos e domina as ferramentas de trabalho."},
    {"pergunta": "Proponho constantemente inovações que otimizam o tempo e os recursos dos processos atuais.", "pilar": "Alta performance", "desc": "Inovação: buscar o 'estado da arte' em tudo o que é executado."},
    {"pergunta": "Cumpro integralmente meus compromissos e prazos, sem necessidade de cobranças externas.", "pilar": "Sem desculpas", "desc": "Comprometimento: sua palavra vale ouro e o prazo é sagrado."},
    {"pergunta": "Assumo total responsabilidade pelos meus resultados, focando na solução em vez de justificar falhas.", "pilar": "Sem desculpas", "desc": "Autorresponsabilidade: não terceiriza erros para terceiros ou circunstâncias."},
    {"pergunta": "Minhas entregas geram o valor máximo esperado, impactando positivamente nossos parceiros.", "pilar": "Foco no cliente/parceiro", "desc": "Valor Extra: ir além do solicitado para encantar quem recebe o serviço."},
    {"pergunta": "Atuo ativamente na construção de relações sólidas e de confiança no longo prazo.", "pilar": "Foco no cliente/parceiro", "desc": "Relacionamento: construir parcerias que resistem ao tempo e aos desafios."},
    {"pergunta": "Mantenho rigorosa disciplina e constância na execução das rotinas diárias da empresa.", "pilar": "Obcecados por resultados", "desc": "Consistência: o resultado extraordinário vem da repetição disciplinada do básico."},
    {"pergunta": "Demonstro determinação incansável para superar metas e buscar o crescimento contínuo.", "pilar": "Obcecados por resultados", "desc": "Fome de Crescer: determinação para atingir objetivos ambiciosos."},
    {"pergunta": "Possuo autonomia para conduzir minhas demandas do início ao fim com mínima supervisão.", "pilar": "Postura empreendedora", "desc": "Ownership: agir como dono do negócio, resolvendo o que precisa ser resolvido."},
    {"pergunta": "Tenho iniciativa para abraçar novos desafios e assumir riscos calculados em prol da empresa.", "pilar": "Postura empreendedora", "desc": "Iniciativa: não espera ordens para agir diante de uma oportunidade de melhoria."},
    {"pergunta": "Priorizo o sucesso coletivo, oferecendo suporte e colaboração constante aos meus colegas.", "pilar": "Mentalidade de time", "desc": "Colaboração: ninguém vence sozinho. Se o time ganha, você ganha."},
    {"pergunta": "Sou capaz de ser firme na defesa dos processos e metas, mantendo total gentileza com as pessoas.", "pilar": "Mentalidade de time", "desc": "Equilíbrio: firmeza com os assuntos e gentileza com as pessoas."}
]

perguntas = [item["pergunta"] for item in perguntas_data]
notas_colab, notas_gestor, just_colab, just_gestor = [], [], [], []

escala_nomes = {1: "1 = Insuficiente", 2: "2 = Abaixo do esperado", 3: "3 = Adequado", 4: "4 = Acima do esperado", 5: "5 = Destaque"}

for i, item in enumerate(perguntas_data):
    st.markdown(f"### {i+1}. {item['pergunta']}")
    st.info(f"**Pilar {item['pilar']}**: {item['desc']}")
    
    st.markdown("**Autoavaliação do Colaborador**")
    v_nota_c = dados_existentes.get('notas_c', [3]*12)[i] if is_bloqueado else 3
    
    if is_gestora or is_diretora:
        st.warning("🔒 Nota Confidencial Oculta")
        n_c = v_nota_c 
        obs_c = dados_existentes.get('just_c', [""]*12)[i] if is_bloqueado else ""
    else:
        n_c_str = st.selectbox(f"Nível de aderência", list(escala_nomes.values()), index=v_nota_c-1, key=f"nc_{i}", disabled=is_bloqueado)
        n_c = int(n_c_str[0])
        v_obs_c = dados_existentes.get('just_c', [""]*12)[i] if is_bloqueado else ""
        label_just = "Justificativa Obrigatória (Nota 1 ou 5)*" if n_c in [1, 5] else "Comentários Adicionais"
        obs_c = st.text_area(label_just, value=v_obs_c, key=f"obsc_{i}", disabled=is_bloqueado)

    if is_gestora or is_diretora:
        st.markdown("**Avaliação da Liderança**")
        n_g_str = st.selectbox(f"Nota Liderança", list(escala_nomes.values()), index=2, key=f"ng_{i}")
        n_g = int(n_g_str[0])
        obs_g = st.text_area(f"Feedback Executivo", key=f"obsg_{i}", placeholder="Pontos fortes e melhorias...")
    else:
        n_g = 3; obs_g = ""
    
    notas_colab.append(n_c); notas_gestor.append(n_g)
    just_colab.append(obs_c); just_gestor.append(obs_g)
    st.divider()

v_dissert = dados_existentes.get('dissert', "") if is_bloqueado else ""
if is_gestora or is_diretora:
    st.markdown("### 🎯 Visão de Futuro e Suporte")
    st.text_area("Como você enxerga seu papel no crescimento da empresa nos próximos meses? Como podemos ajudar?*", value=v_dissert, disabled=True, height=180)
    dissert_input = v_dissert
else:
    st.markdown("### 🎯 Visão de Futuro e Suporte")
    dissert_input = st.text_area("Como você enxerga seu papel no crescimento da empresa nos próximos meses? Como podemos ajudar?*", value=v_dissert, disabled=is_bloqueado, height=180)

if not is_bloqueado:
    if st.button("Finalizar e Protocolar Autoavaliação", type="primary", use_container_width=True):
        faltando_just = False
        for idx, n in enumerate(notas_colab):
            if n in [1, 5] and not just_colab[idx].strip():
                faltando_just = True
                st.error(f"⚠️ A afirmação {idx+1} requer justificativa.")
        if nome_input and area_input and dissert_input and not faltando_just:
            dados_save = {"notas_c": notas_colab, "just_c": just_colab, "dissert": dissert_input, "area": area_input, "gestor": gestor_input, "periodo": periodo_input, "ano": v_ano}
            salvar_dados_colaborador(nome_input, dados_save)
            st.success("Autoavaliação salva!"); time.sleep(1); st.rerun()
        elif not faltando_just:
            st.error("Preencha todos os campos obrigatórios.")

elif is_gestora or is_diretora:
    label = "Gestora" if is_gestora else "Diretora"
    if st.button(f"Gerar Relatório Final e Enviar PDF ({label})", type="primary", use_container_width=True):
        with st.spinner("Processando..."):
            m_final = ((sum(notas_colab)/12) * 0.4) + ((sum(notas_gestor)/12) * 0.6)
            cab = {"Nome": nome_input, "Area": area_input, "Gestor": gestor_input, "Periodo": periodo_input, "Ano": ano_input}
            # CORREÇÃO AQUI: Passando just_colab e just_gestor para a função
            path = gerar_pdf_final(cab, perguntas, notas_colab, notas_gestor, just_colab, just_gestor, dissert_input, m_final, label)
            if enviar_email(nome_input, path, m_final):
                st.success("Relatório enviado!"); st.balloons()
                if os.path.exists(path): os.remove(path)
