import streamlit as pd_stream  # Alias temporário para evitar conflito de namespace com pandas
import streamlit as st
import os
import json
import smtplib
import glob
import time
import math
import unicodedata
import urllib.request
import urllib.parse
from textwrap import wrap
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ========== CONFIGURAÇÕES ==========
EMAIL_ORIGEM = "victormoreiraicnv@gmail.com"
SENHA_APP = "hlvu kwvm tyfw pxem"

SENHA_FINANCEIRO = "financeiro2026"
SENHA_BENEFICIOS = "beneficios2026"
PASTA_DADOS = "avaliacoes_salvas"
PASTA_FONTES = os.path.join(PASTA_DADOS, "fontes")
ARQUIVO_LOGO = os.path.join(PASTA_DADOS, "logo_maldivas.png")

# URL DO SEU GOOGLE APPS SCRIPT
URL_GOOGLE_SHEETS_API = "https://script.google.com/macros/s/AKfycbzHfMAGGNCCZlGya-qtunExpLxW9wbqyIl7gVvd7V8MsKeZ4ZZpL13_LwG8qmPbI104/exec"

os.makedirs(PASTA_DADOS, exist_ok=True)
os.makedirs(PASTA_FONTES, exist_ok=True)

# ========== PALETA DE CORES ==========
COR_FUNDO_ESCURO = colors.HexColor("#0F172A")
COR_PRIMARIA = colors.HexColor("#2563EB")
COR_PRIMARIA_CLARA = colors.HexColor("#DBEAFE")
COR_TEXTO = colors.HexColor("#1E293B")
COR_TEXTO_SUAVE = colors.HexColor("#475569")
COR_CINZA = colors.HexColor("#64748B")
COR_CINZA_CLARO = colors.HexColor("#94A3B8")
COR_TRILHO = colors.HexColor("#E2E8F0")
COR_CARD = colors.HexColor("#F8FAFC")
COR_BRANCO = colors.white

COR_BAIXO = colors.HexColor("#DC2626")    
COR_MEDIO = colors.HexColor("#D97706")    
COR_ALTO = colors.HexColor("#16A34A")     

def cor_da_nota(n):
    if n <= 2: return COR_BAIXO
    if n == 3: return COR_MEDIO
    return COR_ALTO

# ========== FONTES ==========
FONTES_LATO = {
    "Lato": "Lato-Regular.ttf",
    "Lato-Bold": "Lato-Bold.ttf",
    "Lato-Black": "Lato-Black.ttf",
    "Lato-Italic": "Lato-Italic.ttf",
}
_BASE_FONTE_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/lato/"

F_REGULAR = "Helvetica"
F_BOLD = "Helvetica-Bold"
F_BLACK = "Helvetica-Bold"
F_ITALIC = "Helvetica-Oblique"

def configurar_fontes():
    global F_REGULAR, F_BOLD, F_BLACK, F_ITALIC
    try:
        for nome, arq in FONTES_LATO.items():
            caminho = os.path.join(PASTA_FONTES, arq)
            if not os.path.exists(caminho):
                urllib.request.urlretrieve(_BASE_FONTE_URL + arq, caminho)
            pdfmetrics.registerFont(TTFont(nome, caminho))
        F_REGULAR, F_BOLD, F_BLACK, F_ITALIC = "Lato", "Lato-Bold", "Lato-Black", "Lato-Italic"
    except Exception:
        pass

# ========== INTEGRAÇÃO DIRETA COM GOOGLE SHEETS (REAL-TIME BI) ==========
@st.cache_data(ttl=10)
def carregar_dados_da_planilha():
    """Busca em tempo real as linhas cadastradas no Sheets para evitar perdas do servidor."""
    try:
        # Lendo diretamente a versão web/CSV publicada da sua planilha ou via API do Apps Script
        # Adaptado para ler os dados enviados estruturadamente.
        url_read = URL_GOOGLE_SHEETS_API + "?action=read"
        req = urllib.request.Request(url_read, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            dados = json.loads(response.read().decode("utf-8"))
            return pd.DataFrame(dados)
    except Exception:
        # Fallback de segurança para não quebrar a aplicação caso a API esteja instável
        return pd.DataFrame(columns=["colaborador", "lideranca", "departamento", "feedback_gestor", "periodo", "ano", "notas_c", "just_c", "dissert"])

def _slug(nome):
    nfkd = unicodedata.normalize("NFKD", nome)
    sem_acento = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return sem_acento.replace(" ", "_").lower()

def salvar_dados_colaborador(nome, dados):
    """Mantém o salvamento em JSON local para redundância de curto prazo."""
    text_slug = _slug(nome)
    caminho = os.path.join(PASTA_DADOS, f"{text_slug}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)

def carregar_dados_colaborador(nome, df_sheets=None):
    """Puxa os dados prioritariamente do DataFrame do Google Sheets para evitar sumiços."""
    if not nome: return None
    
    if df_sheets is not None and not df_sheets.empty:
        df_filtrado = df_sheets[df_sheets["colaborador"].str.lower() == nome.lower()]
        if not df_filtrado.empty:
            linha = df_filtrado.iloc[-1] # Pega a última inserção válida
            
            # Reconstrói o dicionário padrão que o PDF espera
            try:
                notas_c = json.loads(linha.get("notas_c", "[3,3,3,3,3,3,3,3,3,3,3,3]"))
                just_c = json.loads(linha.get("just_c", '["","","","","","","","","","","",""]'))
                notas_g = json.loads(linha.get("notas_g", "[3,3,3,3,3,3,3,3,3,3,3,3]"))
                just_g = json.loads(linha.get("just_g", '["","","","","","","","","","","",""]'))
            except:
                notas_c = [3]*12; just_c = [""]*12; notas_g = [3]*12; just_g = [""]*12

            return {
                "notas_c": notas_c, "just_c": just_c, "notas_g": notas_g, "just_g": just_g,
                "area": linha.get("departamento", "Financeiro"),
                "gestor": linha.get("lideranca", "Elaine Jatobá"),
                "email_gestor": "globus@globus.com",
                "periodo": linha.get("periodo", "1º semestre"),
                "ano": linha.get("ano", "2026"),
                "dissert": linha.get("dissert", "")
            }
            
    # Fallback local se não achar no Sheets
    text_slug = _slug(nome)
    caminho = os.path.join(PASTA_DADOS, f"{text_slug}.json")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def salvar_na_planilha(colaborador, lideranca, departamento, feedback_gestor, periodo, ano, adicionais=None):
    payload = {
        "colaborador": str(colaborador),
        "lideranca": str(lideranca),
        "departamento": str(departamento),
        "periodo": str(periodo),
        "ano": str(ano),
        "feedback_gestor": str(feedback_gestor)
    }
    if adicionais:
        payload.update(adicionais)
        
    try:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(
            URL_GOOGLE_SHEETS_API, 
            data=data, 
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.getcode() in [200, 201]
    except Exception:
        return False

# ========== GERAÇÃO DO GRÁFICO RADAR ==========
def gerar_radar(pilares, vals_colab, vals_gestor, caminho_png, modo_gestor=False):
    n = len(pilares)
    angulos = [i / n * 2 * math.pi for i in range(n)]
    angulos += angulos[:1]
    vc = vals_colab + vals_colab[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.set_facecolor("#FFFFFF")
    fig.patch.set_alpha(0)
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], color="#94A3B8", size=9)
    ax.set_xticks(angulos[:-1])
    rotulos = ["\n".join(wrap(p, 14)) for p in pilares]
    ax.set_xticklabels(rotulos, size=10, color="#1E293B")
    ax.tick_params(pad=12)
    ax.spines["polar"].set_color("#E2E8F0")
    ax.grid(color="#E2E8F0")

    ax.plot(angulos, vc, color="#2563EB", linewidth=2, label="Performance")
    ax.fill(angulos, vc, color="#2563EB", alpha=0.15)
    ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1.12), frameon=False, fontsize=10)
    plt.tight_layout()
    fig.savefig(caminho_png, dpi=150, transparent=True, bbox_inches="tight")
    plt.close(fig)

# ========== HELPERS DO PDF ==========
def _rodape(c, width, num_pagina):
    c.setFillColor(COR_CINZA_CLARO)
    c.setFont(F_REGULAR, 7)
    c.drawString(50, 25, "Documento confidencial · propriedade da Maldivas")
    c.drawRightString(width - 50, 25, f"Página {num_pagina}")
    c.setStrokeColor(COR_TRILHO)
    c.setLineWidth(0.5)
    c.line(50, 38, width - 50, 38)

def _cabecalho_corrido(c, width, height, nome, ciclo):
    c.setFillColor(COR_FUNDO_ESCURO)
    c.rect(0, height - 45, width, 45, fill=1, stroke=0)
    c.setFillColor(COR_BRANCO)
    c.setFont(F_BOLD, 11)
    c.drawString(50, height - 30, nome.upper())
    c.setFillColor(COR_CINZA_CLARO)
    c.setFont(F_REGULAR, 8)
    c.drawRightString(width - 50, height - 30, ciclo.upper())

def texto_multilinha(c, texto, x, y, largura_chars, leading, fonte, tamanho, cor, contexto, min_y=70):
    if not texto: return y
    for linha in wrap(texto, width=largura_chars):
        if y < min_y: y = contexto["nova_pagina"]()
        c.setFont(fonte, tamanho)
        c.setFillColor(cor)
        c.drawString(x, y, linha)
        y -= leading
    return y

def barra(c, x, y, largura, valor, cor_preench, cor_trilho=COR_TRILHO, altura=7):
    c.setFillColor(cor_trilho)
    c.roundRect(x, y, largura, altura, altura / 2, fill=1, stroke=0)
    if valor > 0:
        w = max((valor / 5) * largura, altura)
        c.setFillColor(cor_preench)
        c.roundRect(x, y, w, altura, altura / 2, fill=1, stroke=0)

def medidor_score(c, cx, cy, raio, score, esp=14):
    frac = max(0.0, min(score / 5.0, 1.0))
    cor = cor_da_nota(round(score))
    c.setStrokeColor(COR_TRILHO)
    c.setLineWidth(esp)
    c.circle(cx, cy, raio, stroke=1, fill=0)
    c.setStrokeColor(cor)
    c.setLineCap(1)
    p = c.beginPath()
    passos = max(2, int(frac * 90))
    for i in range(passos + 1):
        ang = math.radians(90 - (frac * 360) * (i / passos))
        px = cx + raio * math.cos(ang)
        py = cy + raio * math.sin(ang)
        if i == 0: p.moveTo(px, py)
        else: p.lineTo(px, py)
    c.drawPath(p, stroke=1, fill=0)
    c.setFillColor(COR_BRANCO)
    c.setFont(F_BLACK, raio * 0.7)
    c.drawCentredString(cx, cy - raio * 0.22, f"{score:.2f}")
    c.setFillColor(COR_CINZA_CLARO)
    c.setFont(F_REGULAR, 11)
    c.drawCentredString(cx, cy - raio * 0.55, "de 5.00")

# ========== GERAR PDF ==========
def gerar_pdf_final(dados_cabecalho, perguntas_data, n_colab, n_gestor, j_colab, j_gestor, dissert, m_final, cargo_avaliador, modo_gestor=False):
    nome_limpo = _slug(dados_cabecalho["Nome"])
    suffix = "GESTOR" if modo_gestor else "COLABORADOR"
    arquivo_pdf = f"AVALIACAO_{nome_limpo}_{suffix}.pdf"
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    width, height = A4
    ciclo = f"Ciclo Maldivas | {dados_cabecalho['Periodo']} {dados_cabecalho['Ano']}"
    estado = {"pagina": 1}

    def nova_pagina():
        _rodape(c, width, estado["pagina"])
        c.showPage()
        estado["pagina"] += 1
        _cabecalho_corrido(c, width, height, dados_cabecalho["Nome"], ciclo)
        return height - 75

    # CAPA
    c.setFillColor(COR_FUNDO_ESCURO)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    if os.path.exists(ARQUIVO_LOGO):
        try:
            logo = ImageReader(ARQUIVO_LOGO)
            c.drawImage(logo, width / 2 - 90, height - 150, width=180, preserveAspectRatio=True, mask="auto")
        except: pass

    c.setFillColor(COR_BRANCO)
    c.setFont(F_BLACK, 30)
    c.drawCentredString(width / 2, height - 230, "AVALIAÇÃO DE PERFORMANCE")
    c.setFillColor(COR_CINZA_CLARO)
    c.setFont(F_REGULAR, 12)
    c.drawCentredString(width / 2, height - 255, ciclo.upper())

    c.setStrokeColor(COR_PRIMARIA)
    c.setLineWidth(2)
    c.line(width / 2 - 40, height - 275, width / 2 + 40, height - 275)

    medidor_score(c, width / 2, height - 420, 90, m_final)

    c.setFillColor(COR_BRANCO)
    c.setFont(F_BOLD, 22)
    c.drawCentredString(width / 2, height - 560, dados_cabecalho["Nome"].upper())
    c.setFillColor(COR_CINZA_CLARO)
    c.setFont(F_REGULAR, 12)
    c.drawCentredString(width / 2, height - 585, f"{dados_cabecalho['Area'].upper()}")
    c.drawCentredString(width / 2, height - 605, f"Avaliador(a): {dados_cabecalho['Gestor']}")

    y = nova_pagina()
    ctx = {"nova_pagina": nova_pagina}

    pilares_ordem = []
    grupos = {}
    for idx, item in enumerate(perguntas_data):
        pil = item["pilar"]
        if pil not in grupos:
            grupos[pil] = []
            pilares_ordem.append(pil)
        grupos[pil].append(idx)

    for pil in pilares_ordem:
        indices = grupos[pil]
        if y < 170: y = nova_pagina()

        media_pilar = sum(n_colab[i] for i in indices) / len(indices)
        c.setFillColor(COR_FUNDO_ESCURO)
        c.roundRect(50, y - 8, width - 100, 30, 5, fill=1, stroke=0)
        c.setFillColor(COR_BRANCO)
        c.setFont(F_BOLD, 12)
        c.drawString(64, y, pil.upper())
        c.setFillColor(cor_da_nota(round(media_pilar)))
        c.setFont(F_BLACK, 13)
        c.drawRightString(width - 64, y, f"{media_pilar:.1f}")
        y -= 34

        for i in indices:
            if y < 150: y = nova_pagina()
            y = texto_multilinha(c, f"{i+1}. {perguntas_data[i]['pergunta']}", 50, y, 108, 13, F_BOLD, 9.5, COR_TEXTO, ctx)
            y -= 6

            c.setFont(F_BOLD, 8)
            c.setFillColor(COR_CINZA)
            c.drawString(64, y, "Aderência")
            barra(c, 150, y - 1, 120, n_colab[i], COR_CINZA)
            y -= 16

            if j_colab[i]:
                y = texto_multilinha(c, f"Justificativa: {j_colab[i]}", 64, y, 118, 11, F_ITALIC, 8, COR_CINZA, ctx)
            y -= 14

    _rodape(c, width, estado["pagina"])
    c.save()
    return arquivo_pdf

def enviar_email(nome, email_gestor, link_app, departamento):
    senha_setor = SENHA_FINANCEIRO if departamento == "Financeiro" else SENHA_BENEFICIOS
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = email_gestor
    msg["Subject"] = f"🎯 Avaliação de Desempenho Concluída: {nome}"
    corpo = f"Olá,\n\nO colaborador {nome} concluiu a autoavaliação.\nAcesse o portal pelo link abaixo:\n\n{link_app}\n\n🔑 Credencial do setor {departamento}: {senha_setor}"
    msg.attach(MIMEText(corpo, "plain"))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
        server.starttls()
        server.login(EMAIL_ORIGEM, SENHA_APP.replace(" ", ""))
        server.send_message(msg)
        server.quit()
        return True
    except: return False

# ========== DASHBOARD AVANÇADO DE BI TRALHADO EM REAL-TIME ==========
def renderizar_dashboard_gestao(setor_atual, df_sheets):
    st.markdown(f"## 📊 Dashboard Executivo de Performance — Time {setor_atual}")
    st.caption("Métricas consolidadas em tempo real direto do banco de dados unificado.")
    
    if df_sheets.empty:
        st.info("🎯 Nenhuma avaliação integrada ao Sheets para este setor ainda.")
        return

    # Filtrar o DataFrame pelo departamento correto de forma segura
    df_setor = df_sheets[df_sheets["departamento"].str.lower() == setor_atual.lower()].copy()

    if df_setor.empty:
        st.info(f"🎯 Nenhuma resposta localizada para o setor {setor_atual} na planilha.")
        return

    dados_time = []
    for _, linha in df_setor.iterrows():
        nome = str(linha["colaborador"]).title()
        try:
            notas = json.loads(linha.get("notas_c", "[3,3,3,3,3,3,3,3,3,3,3,3]"))
        except:
            notas = [3] * len(perguntas_data)
            
        row = {"Colaborador": nome}
        for idx, nota in enumerate(notas):
            pilar = perguntas_data[idx]["pilar"]
            row[f"P_{idx+1}_{pilar}"] = int(nota)
        row["Média Geral"] = sum(notas) / len(perguntas_data)
        dados_time.append(row)

    df = pd.DataFrame(dados_time)

    # Métricas de KPI do BI
    media_geral_setor = df["Média Geral"].mean()
    desvio_padrao = df["Média Geral"].std() if len(df) > 1 else 0.0
    status_coesao = "Alta" if desvio_padrao < 0.4 else "Moderada" if desvio_padrao < 0.8 else "Dispersa"

    st.markdown("### 🔍 Insights de Liderança Avançados")
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1: st.metric("👥 Ativos no Setor", f"{len(df)} Integrantes")
    with kpi2: st.metric("📈 IAP (Índice de Aderência do Setor)", f"{media_geral_setor:.2f} / 5.00")
    with kpi3: st.metric("📉 Volatilidade de Performance", f"{desvio_padrao:.2f}", f"Coesão {status_coesao}")

    st.divider()

    # MATRIZ DE COMPETÊNCIAS PREMIUM COM CONTRASTE ABSOLUTO
    st.markdown("### 🗺️ Matriz de Competências Dinâmica")
    df_clean = df.copy()
    colunas_renomeadas = {"Colaborador": "Colaborador"}
    for col in df_clean.columns:
        if col != "Colaborador" and col != "Média Geral":
            partes = col.split("_")
            colunas_renomeadas[col] = f"P{partes[1]} - {partes[2]}"
            
    df_clean = df_clean.rename(columns=colunas_renomeadas).set_index("Colaborador")
    df_clean = df_clean[["Média Geral"] + [c for c in df_clean.columns if c != "Média Geral"]]

    cmap_custom = mcolors.LinearSegmentedColormap.from_list("maldivas_perf", ["#FCA5A5", "#FEF08A", "#BBF7D0"])

    df_estilizado = (
        df_clean.style
        .background_gradient(cmap=cmap_custom, vmin=1, vmax=5)
        .format("{:.2f}")
        .set_properties(**{
            'color': '#0F172A',            # Força o contraste preto/grafite absoluto em cima do verde/amarelo
            'font-weight': '600',
            'border': '1px solid #E2E8F0',
            'padding': '10px'
        })
    )
    st.dataframe(df_estilizado, use_container_width=True)

# ========== PERGUNTAS ESTRUTURAIS ==========
perguntas_data = [
    {"pergunta": "Busco melhoria contínua e domínio técnico, elevando o nível das minhas entregas e do time.", "pilar": "Alta performance", "desc": "Excelência e superação constante de metas."},
    {"pergunta": "Demonstro domínio técnico absoluto e precisão na execução das minhas tarefas operacionais.", "pilar": "Alta performance", "desc": "Precisão e domínio das ferramentas de trabalho."},
    {"pergunta": "Assumo erros e problemas agindo com postura de dono, sem transferir a responsabilidade aos outros.", "pilar": "Sem desculpa", "desc": "Autorresponsabilidade e foco total na solução rápida."},
    {"pergunta": "Cumpro integralmente meus compromissos e prazos, sem necessidade de cobranças externas.", "pilar": "Sem desculpa", "desc": "Comprometimento e disciplina com o que foi acordado."},
    {"pergunta": "Priorizo o cliente nas minhas decisões, entendendo o impacto real do meu trabalho no cliente/parceiro.", "pilar": "Foco no cliente", "desc": "Gerar valor real e construir relações de confiança."},
    {"pergunta": "Minhas entregas geram o valor máximo esperado, impactando positivamente nossos parceiros.", "pilar": "Foco no cliente", "desc": "Encantamento e visão de longo prazo na parceria."},
    {"pergunta": "Mantenho rigorosa disciplina e constância para cumprir metas e superar obstáculos.", "pilar": "Obcecados por resultados", "desc": "Fome de crescer e consistência na execução diária."},
    {"pergunta": "Demonstro determinação incansável para superar metas e buscar o crescimento contínuo.", "pilar": "Obcecados por resultados", "desc": "Resiliência e foco no atingimento de objetivos ambiciosos."},
    {"pergunta": "Tomo iniciativa e proponho soluções com autonomia, assumindo riscos inteligentes.", "pilar": "Postura empreendedora", "desc": "Agir como dono, resolvendo problemas sem esperar ordens."},
    {"pergunta": "Possuo autonomia para conduzir minhas demandas do início ao fim com mínima supervisão.", "pilar": "Postura empreendedora", "desc": "Independência e proatividade na condução de processos."},
    {"pergunta": "Colaboro ativamente, elevo as pessoas ao redor e mantém postura madura e respeitosa.", "pilar": "Mentalidade de time", "desc": "Sucesso coletivo acima do individual e equilíbrio nas relações."},
    {"pergunta": "Priorizo o sucesso coletivo, oferecendo suporte e colaboração constante aos meus colegas.", "pilar": "Mentalidade de time", "desc": "Espírito de equipe e apoio mútuo para vencer."},
]
num_total = len(perguntas_data)
escala_nomes = {1: "1 = Muito abaixo do esperado", 2: "2 = Abaixo do esperado", 3: "3 = Atende plenamente", 4: "4 = Supera expectativas", 5: "5 = Destaque"}

# ========== FLUXO PRINCIPAL PORTAL ==========
def main():
    st.set_page_config(page_title="Avaliação Maldivas", layout="wide")
    configurar_fontes()

    # PUXAR BASE REAL-TIME LOGO NO INIT DO SISTEMA
    df_sheets = carregar_dados_da_planilha()

    if os.path.exists(ARQUIVO_LOGO): st.image(ARQUIVO_LOGO, width=350)

    nome_para_carregar = ""
    modo_visao = "Análise Individual"

    with st.sidebar:
        st.header("🔐 Portal Administrativo")
        senha_input = st.text_input("Credencial", type="password")
        is_financeiro = (senha_input == SENHA_FINANCEIRO)
        is_beneficios = (senha_input == SENHA_BENEFICIOS)
        is_gestao = is_financeiro or is_beneficios

        if is_gestao:
            setor_atual = "Financeiro" if is_financeiro else "Benefícios"
            st.success(f"Acesso: Gestão {setor_atual}")
            modo_visao = st.radio("Selecione o Modo:", ["Análise Individual", "Dashboard do Time Total"])
            
            if modo_visao == "Análise Individual" and not df_sheets.empty:
                df_setor_list = df_sheets[df_sheets["departamento"].str.lower() == setor_atual.lower()]
                lista_pendentes = sorted(df_setor_list["colaborador"].unique().tolist())
                
                if lista_pendentes:
                    selecionado = st.selectbox("Escolha o Colaborador:", [""] + lista_pendentes)
                    if selecionado: nome_para_carregar = selecionado

    st.title("🏝️ PROGRAMA DE AVALIAÇÃO MALDIVAS")

    if is_gestao and modo_visao == "Dashboard do Time Total":
        renderizar_dashboard_gestao(setor_atual, df_sheets)
        return

    dados_existentes = carregar_dados_colaborador(nome_para_carregar, df_sheets)
    is_bloqueado = dados_existentes is not None

    col_cab1, col_cab2 = st.columns(2)
    with col_cab1:
        nome_input = st.text_input("Nome do Colaborador*", value=nome_para_carregar, disabled=is_bloqueado).strip()
        v_area = dados_existentes.get("area", "Financeiro") if is_bloqueado else "Financeiro"
        area_input = st.selectbox("Departamento*", ["Financeiro", "Benefícios"], index=["Financeiro", "Benefícios"].index(v_area), disabled=is_bloqueado)
    with col_cab2:
        v_ano = dados_existentes.get("ano", "2026") if is_bloqueado else "2026"
        ano_input = st.selectbox("Ano", ["2026", "2027", "2028"], index=["2026", "2027", "2028"].index(v_ano), disabled=is_bloqueado)
        v_per = dados_existentes.get("periodo", "1º semestre") if is_bloqueado else "1º semestre"
        periodo_input = st.radio("Período de Avaliação", ["1º semestre", "2º semestre"], index=0 if v_per == "1º semestre" else 1, horizontal=True, disabled=is_bloqueado)

    lideranca_automatica = "Elaine Jatobá" if area_input == "Financeiro" else "Roberta Bastos"
    email_automatico = "elaine.jatoba@globusseguros.com.br" if area_input == "Financeiro" else "roberta.bastos@globusseguros.com.br"
    gestor_input = st.text_input("Liderança Direta*", value=dados_existentes.get("gestor", lideranca_automatica) if is_bloqueado else lideranca_automatica, disabled=True)
    email_gestor_input = st.text_input("E-mail do Gestor*", value=email_automatico, disabled=True)

    st.divider()

    notas_colab, notas_gestor, just_colab, just_gestor = [], [], [], []
    pilares_ordem = ["Alta performance", "Sem desculpa", "Foco no cliente", "Obcecados por resultados", "Postura empreendedora", "Mentalidade de time"]
    
    n_c_map, n_g_map, j_c_map, j_g_map = {}, {}, {}, {}
    titulos_abas = [f"{p} ➜" for p in pilares_ordem] + ["📊 Média e Visão de Futuro"]
    abas = st.tabs(titulos_abas)

    # Mapeamento dinâmico
    for idx_aba, aba in enumerate(abas[:-1]):
        pil = pilares_ordem[idx_aba]
        indices_pilar = [k for k, item in enumerate(perguntas_data) if item["pilar"] == pil]
        with aba:
            for i in indices_pilar:
                item = perguntas_data[i]
                st.markdown(f"#### {i+1}. {item['pergunta']}")
                v_nota_c = dados_existentes.get("notas_c", [3] * num_total)[i] if is_bloqueado else 3

                if is_gestao:
                    st.info(f"Nota na Planilha: {v_nota_c} ({escala_nomes[v_nota_c]})")
                    n_c = v_nota_c
                    obs_c = dados_existentes.get("just_c", [""] * num_total)[i]
                    if obs_c.strip(): st.warning(f"💬 Justificativa: {obs_c}")
                    n_g, obs_g = v_nota_c, ""
                else:
                    n_c_str = st.selectbox("Aderência", list(escala_nomes.values()), index=v_nota_c - 1, key=f"nc_{i}", disabled=is_bloqueado)
                    n_c = int(n_c_str[0])
                    v_obs_c = dados_existentes.get("just_c", [""] * num_total)[i] if is_bloqueado else ""
                    obs_c = st.text_area("Justificativa (Obrigatória para 1 ou 5)", value=v_obs_c, key=f"obsc_{i}", disabled=is_bloqueado)
                    n_g, obs_g = n_c, ""

                n_c_map[i], n_g_map[i], j_c_map[i], j_g_map[i] = n_c, n_g, obs_c, obs_g

    for i in range(num_total):
        notas_colab.append(n_c_map.get(i, 3)); notas_gestor.append(n_g_map.get(i, 3))
        just_colab.append(j_c_map.get(i, "")); just_gestor.append(j_g_map.get(i, ""))

    with abas[-1]:
        media_colab = sum(notas_colab) / num_total
        st.metric("Índice de Aderência Operacional (IAO)", f"{media_colab:.2f} / 5.00")
        
        v_dissert = dados_existentes.get("dissert", "") if is_bloqueado else ""
        dissert_input = st.text_area("Visão de Futuro e Crescimento*", value=v_dissert, disabled=is_bloqueado, height=150)

        if not is_bloqueado:
            if st.button("Finalizar e Transmitir para o Banco de Dados", type="primary", use_container_width=True):
                if nome_input and dissert_input:
                    # Enviar strings estruturadas em JSON das notas e justificativas para o Google Sheets receber tudo em uma tacada só
                    payload_adicional = {
                        "notas_c": json.dumps(notas_colab),
                        "just_c": json.dumps(just_colab),
                        "notas_g": json.dumps(notas_gestor),
                        "just_g": json.dumps(just_gestor),
                        "dissert": str(dissert_input)
                    }
                    
                    dados_save = {"notas_c": notas_colab, "just_c": just_colab, "dissert": dissert_input, "area": area_input, "gestor": gestor_input, "periodo": periodo_input, "ano": ano_input}
                    salvar_dados_colaborador(nome_input, dados_save)
                    
                    salvar_na_planilha(nome_input, gestor_input, area_input, "Autoavaliação submetida", periodo_input, ano_input, payload_adicional)
                    enviar_email(nome_input, email_gestor_input, "https://6gxzkzhhzmceshkaojrpb7.streamlit.app/", area_input)
                    
                    st.success("Sucesso! Seus dados estão salvos em nuvem de forma permanente.")
                    time.sleep(0.5)
                    st.rerun()

        if is_bloqueado:
            if st.button("📥 Gerar e Baixar PDF de Performance"):
                cab = {"Nome": nome_input, "Area": area_input, "Gestor": gestor_input, "Periodo": periodo_input, "Ano": ano_input}
                pdf_path = gerar_pdf_final(cab, perguntas_data, notas_colab, notas_gestor, just_colab, just_gestor, dissert_input, media_colab, "Liderança")
                with open(pdf_path, "rb") as f:
                    st.download_button(label="Clique para Salvar Arquivo", data=f.read(), file_name=pdf_path, mime="application/pdf")

if __name__ == "__main__":
    main()
