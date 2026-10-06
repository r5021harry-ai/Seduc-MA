import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import streamlit as st

from conteudo import NIVEIS, TEMAS
from gerador import MODELO_PADRAO, gerar_questoes

# Configuração da página com layout amplo
st.set_page_config(
    page_title="Simulados SEDUC-MA | FCC",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

HISTORICO = Path("historico.json")


def carregar_historico() -> list:
    if HISTORICO.exists():
        try:
            return json.loads(HISTORICO.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def salvar_resultado(resultado: dict) -> None:
    hist = carregar_historico()
    hist.append(resultado)
    HISTORICO.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")


def chave_api() -> str:
    return st.secrets.get("GEMINI_API_KEY", "") or st.session_state.get("api_key", "")


# ---------- Estado ----------
st.session_state.setdefault("questoes", [])
st.session_state.setdefault("respostas", {})
st.session_state.setdefault("finalizado", False)

# ---------- Barra lateral ----------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/dna.png", width=64)
    st.title("Configurações")

    with st.expander("🔑 Credenciais & Modelo", expanded=True):
        if not st.secrets.get("GEMINI_API_KEY", ""):
            st.text_input("Chave da API Gemini", type="password", key="api_key", help="Cole sua API Key do Google AI Studio")
        
        modelo = st.selectbox(
            "Modelo Gemini",
            options=["gemini-2.5-flash", "gemini-2.5-pro"],
            index=0 if st.secrets.get("MODELO", MODELO_PADRAO) == "gemini-2.5-flash" else 1,
            help="gemini-2.5-flash é mais rápido; gemini-2.5-pro oferece raciocínio mais profundo."
        )

    st.subheader("🎯 Conteúdo do Simulado")
    areas = st.multiselect("Áreas de Biologia", list(TEMAS), default=list(TEMAS)[:2])
    topicos = [t for a in areas for t in TEMAS[a]]
    escolhidos = st.multiselect("Tópicos Específicos (vazio = todos)", topicos)
    
    st.divider()
    nivel = st.select_slider("Nível de Dificuldade", NIVEIS, value="Médio")
    qtd = st.slider("Quantidade de Questões", 3, 15, 5)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Gerar Simulado", type="primary", use_container_width=True):
        if not chave_api():
            st.error("Informe a Chave da API Gemini.")
        elif not areas:
            st.error("Escolha ao menos uma área temática.")
        else:
            with st.spinner("✨ Gemini está elaborando suas questões no estilo FCC..."):
                try:
                    st.session_state.questoes = gerar_questoes(
                        chave_api(), escolhidos or topicos, qtd, nivel, modelo
                    )
                    st.session_state.respostas = {}
                    st.session_state.finalizado = False
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"Erro ao gerar questões: {e}")

# ---------- Interface Principal ----------
col_main_left, col_main_right = st.columns([0.8, 0.2])

aba_simulado, aba_desempenho = st.tabs(["📝 Simulado Ativo", "📊 Painel de Desempenho"])

with aba_simulado:
    st.title("🧬 Simulado – Professor de Biologia")
    st.caption("Foco: SEDUC-MA · Banca: FCC · Questões inéditas geradas via Google Gemini")

    questoes = st.session_state.questoes
    if not questoes:
        st.info("👈 Ajuste os parâmetros na barra lateral e clique em **Gerar Simulado** para começar.")
    else:
        for i, q in enumerate(questoes):
            # Cartão visual para cada questão
            with st.container(border=True):
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.subheader(f"Questão {i + 1}")
                with col2:
                    st.caption(f"🏷️ `{q.get('tema', 'Geral')}`")

                st.markdown(q["enunciado"])
                st.markdown("<br>", unsafe_allow_html=True)
                
                opcoes = list(q["alternativas"])
                st.radio(
                    "Selecione uma alternativa:",
                    opcoes,
                    index=None,
                    format_func=lambda k, q=q: f"**{k})** {q['alternativas'][k]}",
                    key=f"resp_{i}",
                    disabled=st.session_state.finalizado,
                    label_visibility="collapsed",
                )

                if st.session_state.finalizado:
                    st.divider()
                    marcada = st.session_state.get(f"resp_{i}")
                    gabarito = q["gabarito"]
                    
                    if marcada == gabarito:
                        st.success(f"✅ **Correto!** Resposta: **{gabarito}**")
                    else:
                        st.error(f"❌ **Incorreto.** Você marcou **{marcada or 'Nenhuma'}** | Gabarito correto: **{gabarito}**")
                    
                    with st.expander("💡 Comentário e Explicação Pedagógica", expanded=True):
                        st.write(q.get("comentario", "Sem comentário disponível."))

        st.markdown("<br>", unsafe_allow_html=True)
        if not st.session_state.finalizado:
            if st.button("✔️ Finalizar e Corrigir Simulado", type="primary", use_container_width=True):
                acertos, por_tema = 0, defaultdict(lambda: [0, 0])
                for i, q in enumerate(questoes):
                    ok = st.session_state.get(f"resp_{i}") == q["gabarito"]
                    acertos += ok
                    por_tema[q.get("tema", "Geral")][1] += 1
                    por_tema[q.get("tema", "Geral")][0] += ok
                
                salvar_resultado(
                    {
                        "data": datetime.now().isoformat(timespec="seconds"),
                        "acertos": acertos,
                        "total": len(questoes),
                        "por_tema": dict(por_tema),
                    }
                )
                st.session_state.finalizado = True
                st.rerun()
        else:
            acertos = sum(
                st.session_state.get(f"resp_{i}") == q["gabarito"]
                for i, q in enumerate(questoes)
            )
            pct = acertos / len(questoes)
            
            st.divider()
            col_res1, col_res2, col_res3 = st.columns(3)
            col_res1.metric("Pontuação Total", f"{acertos} / {len(questoes)}")
            col_res2.metric("Aproveitamento", f"{pct:.0%}")
            col_res3.metric("Status", "Aprovado 🎉" if pct >= 0.7 else "Necessita Revisão 📚")

with aba_desempenho:
    hist = carregar_historico()
    if not hist:
        st.info("Realize pelo menos um simulado para registrar estatísticas de desempenho.")
    else:
        total_ac = sum(h["acertos"] for h in hist)
        total_q = sum(h["total"] for h in hist)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Média Geral de Acertos", f"{total_ac / total_q:.0%}")
        m2.metric("Total de Questões Respondidas", f"{total_q}")
        m3.metric("Simulados Concluídos", f"{len(hist)}")

        st.markdown("### 📈 Evolução de Rendimento")
        st.line_chart([h["acertos"] / h["total"] for h in hist])

        agregado = defaultdict(lambda: [0, 0])
        for h in hist:
            for tema, (a, t) in h["por_tema"].items():
                agregado[tema][0] += a
                agregado[tema][1] += t
                
        st.markdown("### 🧬 Desempenho por Tema")
        st.caption("Classificado do tema com maior necessidade de revisão ao mais dominado:")
        
        for tema, (a, t) in sorted(agregado.items(), key=lambda x: x[1][0] / x[1][1]):
            aproveitamento = a / t
            col_t1, col_t2 = st.columns([0.7, 0.3])
            with col_t1:
                st.progress(aproveitamento, text=f"**{tema}** ({a}/{t} acertos)")
            with col_t2:
                st.caption(f"Taxa de acerto: **{aproveitamento:.0%}**")

        st.caption("💡 *Nota: No Streamlit Cloud, arquivos locais de histórico podem ser redefinidos ao reiniciar a aplicação.*")
