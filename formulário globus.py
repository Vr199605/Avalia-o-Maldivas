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

# Importação necessária para o Dashboard do Gestor
import pandas as pd

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

# URL DO SEU GOOGLE APPS SCRIPT ATUALIZADA COM SUCESSO
URL_GOOGLE_SHEETS_API = "https://script.google.com/macros/s/AKfycbzHfMAGGNCCZlGya-qtunExpLxW9wbqyIl7gVvd7V8MsKeZ4ZZpL13_LwG8qmPbI104/exec"

os.makedirs(PASTA_DADOS, exist_ok=True)
os.makedirs(PASTA_FONTES, exist_ok=True)

# ========== PALETA DE CORES (fonte única de verdade) ==========
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

# Cores semânticas por faixa de nota
COR_BAIXO = colors.HexColor("#DC2626")    # 1-2 vermelho
COR_MEDIO = colors.HexColor("#D97706")    # 3 âmbar
COR_ALTO = colors.HexColor("#16A34A")     # 4-5 verde

def cor_da_nota(n):
    if n <= 2:
        return COR_BAIXO
    if n == 3:
        return COR_MEDIO
    return COR_ALTO

# ========== FONTES (embutidas, com fallback p/ Helvetica) ==========
FONTES_LATO = {
    "Lato": "Lato-Regular.ttf",
    "Lato-Bold": "Lato-Bold.ttf",
    "Lato-Black": "Lato-Black.ttf",
    "Lato-Italic": "Lato-Italic.ttf",
}
_BASE_FONTE_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/lato/"

# Nomes efetivamente usados (preenchidos por configurar_fontes)
F_REGULAR = "Helvetica"
F_BOLD = "Helvetica-Bold"
F_BLACK = "Helvetica-Bold"
F_ITALIC = "Helvetica-Oblique"

def configurar_fontes():
    """Baixa (se preciso) e registra a família Lato. Fallback silencioso p/ Helvetica."""
    global F_REGULAR, F_BOLD, F_BLACK, F_ITALIC
    try:
        for nome, arq in FONTES_LATO.items():
            caminho = os.path.join(PASTA_FONTES, arq)
            if not os.path.exists(caminho):
                urllib.request.urlretrieve(_BASE_FONTE_URL + arq, caminho)
            pdfmetrics.registerFont(TTFont(nome, caminho))
        F_REGULAR, F_BOLD, F_BLACK, F_ITALIC = "Lato", "Lato-Bold", "Lato-Black", "Lato-Italic"
    except Exception:
        # mantém Helvetica
        pass

# ========== FUNÇÕES DE SISTEMA ==========
def _slug(nome):
    nfkd = unicodedata.normalize("NFKD", nome)
    sem_acento = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return sem_acento.replace(" ", "_").lower()

def salvar_dados_colaborador(nome, dados):
    text_slug = _slug(nome)
    caminho = os.path.join(PASTA_DADOS, f"{text_slug}.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False)

def carregar_dados_colaborador(nome):
    if not nome:
        return None
    text_slug = _slug(nome)
    caminho = os.path.join(PASTA_DADOS, f"{text_slug}.json")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def listar_avaliacoes_pendentes():
    arquivos = glob.glob(os.path.join(PASTA_DADOS, "*.json"))
    nomes = [os.path.basename(f).replace(".json", "").replace("_", " ").title() for f in arquivos]
    return sorted(nomes)

def salvar_na_planilha(colaborador, lideranca, departamento, feedback_gestor, periodo, ano):
    """Envia os dados usando urlencode para garantir o mapeamento de parâmetros aceito pelo Google Sheets."""
    payload = {
        "colaborador": str(colaborador),
        "lideranca": str(lideranca),
        "departamento": str(departamento),
        "periodo": str(periodo),
        "ano": str(ano)
    }
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

# ========== GERAÇÃO DO GRÁFICO RADAR (matplotlib) ==========
def gerar_radar(pilares, vals_colab, vals_gestor, caminho_png, modo_gestor=False):
    """Radar exibindo a autoavaliação por pilar (Unificado devido à remoção de notas da liderança)."""
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

    ax.plot(angulos, vc, color="#2563EB", linewidth=2, label="Autoavaliação")
    ax.fill(angulos, vc, color="#2563EB", alpha=0.15)

    ax.legend(loc="upper right", bbox_to_anchor=(1.15, 1.12), frameon=False, fontsize=10)
    plt.tight_layout()
    fig.savefig(caminho_png, dpi=150, transparent=True, bbox_inches="tight")
    plt.close(fig)

# ========== HELPERS DE DESENHO NO PDF ==========
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

def texto_multilinha(c, texto, x, y, largura_chars, leading, fonte, tamanho, cor,
                     contexto, min_y=70):
    if not texto:
        return y
    for linha in wrap(texto, width=largura_chars):
        if y < min_y:
            y = contexto["nova_pagina"]()
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
        if i == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    c.drawPath(p, stroke=1, fill=0)
    c.setFillColor(COR_BRANCO)
    c.setFont(F_BLACK, raio * 0.7)
    c.drawCentredString(cx, cy - raio * 0.22, f"{score:.2f}")
    c.setFillColor(COR_CINZA_CLARO)
    c.setFont(F_REGULAR, 11)
    c.drawCentredString(cx, cy - raio * 0.55, "de 5.00")

# ========== GERAR PDF ==========
def gerar_pdf_final(dados_cabecalho, perguntas_data, n_colab, n_gestor,
                    j_colab, j_gestor, dissert, m_final, cargo_avaliador, modo_gestor=False):
    name_limpo = _slug(dados_cabecalho["Nome"])
    suffix = "GESTOR" if modo_gestor else "COLABORADOR"
    arquivo_pdf = f"AVALIACAO_{name_limpo}_{suffix}.pdf"
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

    # ---------- PÁGINA 1: CAPA ----------
    c.setFillColor(COR_FUNDO_ESCURO)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    if os.path.exists(ARQUIVO_LOGO):
        try:
            logo = ImageReader(ARQUIVO_LOGO)
            c.drawImage(logo, width / 2 - 90, height - 150, width=180,
                        preserveAspectRatio=True, mask="auto")
        except Exception:
            pass

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
    c.setFont(F_REGULAR, 9)
    c.setFillColor(COR_CINZA)
    c.drawCentredString(width / 2, 50, f"Relatório gerado em {time.strftime('%d/%m/%Y às %H:%M')}")

    y = nova_pagina()

    # ---------- PÁGINAS DE CONTEÚDO: AGRUPADO POR PILAR ----------
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
        if y < 170:
            y = nova_pagina()

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
            if y < 150:
                y = nova_pagina()

            y = texto_multilinha(
                c, f"{i+1}. {perguntas_data[i]['pergunta']}", 50, y,
                largura_chars=108, leading=13,
                fonte=F_BOLD, tamanho=9.5, cor=COR_TEXTO, contexto=ctx,
            )
            y -= 6

            c.setFont(F_BOLD, 8)
            c.setFillColor(COR_CINZA)
            c.drawString(64, y, "Autoavaliação")
            barra(c, 150, y - 1, 120, n_colab[i], COR_CINZA)
            c.setFillColor(cor_da_nota(n_colab[i]))
            c.setFont(F_BOLD, 9)
            c.drawString(278, y, str(n_colab[i]))
            y -= 16

            if j_colab[i]:
                y = texto_multilinha(
                    c, f"Just. colaborador: {j_colab[i]}", 64, y,
                    largura_chars=118, leading=11,
                    fonte=F_ITALIC, tamanho=8, cor=COR_CINZA, contexto=ctx,
                )
            
            if modo_gestor and j_gestor[i]:
                y = texto_multilinha(
                    c, f"Obs {cargo_avaliador}: {j_gestor[i]}", 64, y,
                    largura_chars=118, leading=11,
                    fonte=F_ITALIC, tamanho=8, cor=COR_PRIMARIA, contexto=ctx,
                )
            y -= 14

    # ---------- RADAR DOS PILARES ----------
    radar_png = os.path.join(PASTA_DADOS, f"_radar_{name_limpo}.png")
    vals_colab = [sum(n_colab[i] for i in grupos[p]) / len(grupos[p]) for p in pilares_ordem]
    vals_gestor = vals_colab
    try:
        gerar_radar(pilares_ordem, vals_colab, vals_gestor, radar_png, modo_gestor=modo_gestor)
        y = nova_pagina()
        c.setFillColor(COR_TEXTO)
        c.setFont(F_BOLD, 14)
        c.drawString(50, y, "VISÃO GERAL POR PILAR")
        c.setFillColor(COR_CINZA)
        c.setFont(F_REGULAR, 9)
        c.drawString(50, y - 16, "Acompanhamento de notas por pilar estratégico.")
        img = ImageReader(radar_png)
        iw, ih = img.getSize()
        disp_w = 380
        disp_h = disp_w * ih / iw
        c.drawImage(img, (width - disp_w) / 2, y - 40 - disp_h, width=disp_w,
                    height=disp_h, mask="auto")
        y = y - 60 - disp_h
    except Exception:
        pass

    # ---------- SEÇÃO DISSERTATIVA ----------
    if y < 220:
        y = nova_pagina()
    c.setFillColor(COR_CARD)
    altura_box = 14 + len(wrap(dissert or "", 100)) * 12 + 20
    c.roundRect(50, y - altura_box, width - 100, altura_box, 6, fill=1, stroke=0)
    c.setFillColor(COR_TEXTO)
    c.setFont(F_BOLD, 11)
    c.drawString(64, y - 18, "VISÃO ESTRATÉGICA E APOIO")
    y -= 40
    y = texto_multilinha(
        c, dissert or "Não informado.", 64, y,
        largura_chars=100, leading=12,
        fonte=F_REGULAR, tamanho=9, cor=COR_TEXTO_SUAVE, contexto=ctx, min_y=80,
    )

    _rodape(c, width, estado["pagina"])
    c.save()

    if os.path.exists(radar_png):
        os.remove(radar_png)
    return arquivo_pdf

def enviar_email(nome, email_gestor, link_app, departamento):
    senha_setor = SENHA_FINANCEIRO if departamento == "Financeiro" else SENHA_BENEFICIOS
    
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ORIGEM
    msg["To"] = email_gestor
    msg["Subject"] = f"🎯 Avaliação de Desempenho Pendente: {nome}"
    corpo = (
        f"Olá,\n\nO colaborador {nome} concluiu a autoavaliação de desempenho.\n"
        f"Para visualizar as respostas, adicionar seus feedbacks e baixar os relatórios, acesse o portal pelo link abaixo:\n\n"
        f"{link_app}\n\n"
        f"🔑 Sua Credencial de Acesso para o setor {departamento} é: {senha_setor}"
    )
    msg.attach(MIMEText(corpo, "plain"))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
        server.ehlo()
        server.starttls()
        server.login(EMAIL_ORIGEM, SENHA_APP.replace(" ", ""))
        server.send_message(msg)
        server.quit()
        return True
    except (smtplib.SMTPException, OSError) as e:
        st.error(f"Erro no envio de e-mail de notificação para o gestor: {e}")
        return False

# ========== DADOS DAS PERGUNTAS ==========
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
perguntas = [item["pergunta"] for item in perguntas_data]
num_total = len(perguntas)

escala_nomes = {
    1: "1 = Muito abaixo do esperado",
    2: "2 = Abaixo do esperado",
    3: "3 = Atende plenamente",
    4: "4 = Supera expectativas",
    5: "5 = Destaque",
}

# ========== FUNÇÃO ADICIONAL: DASHBOARD DE PONTOS FORTES/FRACOS DO TIME ==========
def renderizar_dashboard_gestao(setor_atual):
    st.markdown(f
