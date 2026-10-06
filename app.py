import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import streamlit as st

from conteudo import NIVEIS, TEMAS
from gerador import MODELO_PADRAO, gerar_questoes

st.set_page_config(page_title="Simulados SEDUC-MA | FCC", page_icon="🧬", layout="centered")

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
    return st.secrets.get("ANTHROPIC_API_KEY", "") or st.session_state.get("api_key", "")


# ---------- Estado ----------
st.session_state.setdefault("questoes", [])
st.session_state.setdefault("respostas", {})
st.session_state.setdefault("finalizado", False)

# ---------- Barra lateral ----------
with st.sidebar:
    st.header("⚙️ Configuração")
    if not st.secrets.get("ANTHROPIC_API_KEY", ""):
        st.text_input("Chave da API Anthropic", type="password", key="api_key")
    modelo = st.text_input("Modelo", value=st.secrets.get("MODELO", MODELO_PADRAO))

    areas = st.multiselect("Áreas", list(TEMAS), default=list(TEMAS)[:2])
    topicos = [t for a in areas for t in TEMAS[a]]
    escolhidos = st.multiselect("Tópicos (vazio = todos das áreas)", topicos)
    nivel = st.select_slider("Nível", NIVEIS, value="Médio")
    qtd = st.slider("Nº de questões", 3, 15, 5)

    if st.button("🎯 Gerar simulado", type="primary", use_container_width=True):
        if not chave_api():
            st.error("Informe a chave da API.")
        elif not areas:
            st.error("Escolha ao menos uma área.")
        else:
            with st.spinner("Elaborando questões no estilo FCC..."):
                try:
                    st.session_state.questoes = gerar_questoes(
                        chave_api(), escolhidos or topicos, qtd, nivel, modelo
                    )
                    st.session_state.respostas = {}
                    st.session_state.finalizado = False
                except Exception as e:  # noqa: BLE001
                    st.error(f"Erro ao gerar: {e}")

# ---------- Abas ----------
aba_simulado, aba_desempenho = st.tabs(["📝 Simulado", "📊 Desempenho"])

with aba_simulado:
    st.title("🧬 Simulado – Professor de Biologia")
    st.caption("SEDUC-MA · Estilo FCC · Questões inéditas geradas por IA")

    questoes = st.session_state.questoes
    if not questoes:
        st.info("Configure na barra lateral e clique em **Gerar simulado**.")
    else:
        for i, q in enumerate(questoes):
            st.markdown(f"**Questão {i + 1}** · _{q.get('tema', '')}_")
            st.write(q["enunciado"])
            opcoes = list(q["alternativas"])
            st.radio(
                "Alternativas",
                opcoes,
                index=None,
                format_func=lambda k, q=q: f"{k}) {q['alternativas'][k]}",
                key=f"resp_{i}",
                disabled=st.session_state.finalizado,
                label_visibility="collapsed",
            )
            if st.session_state.finalizado:
                marcada = st.session_state.get(f"resp_{i}")
                if marcada == q["gabarito"]:
                    st.success(f"✅ Correto! Gabarito: {q['gabarito']}")
                else:
                    st.error(f"❌ Você marcou: {marcada or '—'} · Gabarito: {q['gabarito']}")
                with st.expander("Comentário"):
                    st.write(q.get("comentario", ""))
            st.divider()

        if not st.session_state.finalizado:
            if st.button("✔️ Finalizar e corrigir", type="primary"):
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
            st.metric("Resultado", f"{acertos}/{len(questoes)}", f"{acertos / len(questoes):.0%}")

with aba_desempenho:
    hist = carregar_historico()
    if not hist:
        st.info("Faça um simulado para ver seu desempenho.")
    else:
        total_ac = sum(h["acertos"] for h in hist)
        total_q = sum(h["total"] for h in hist)
        st.metric("Aproveitamento geral", f"{total_ac / total_q:.0%}", f"{total_q} questões")
        st.line_chart([h["acertos"] / h["total"] for h in hist])

        agregado = defaultdict(lambda: [0, 0])
        for h in hist:
            for tema, (a, t) in h["por_tema"].items():
                agregado[tema][0] += a
                agregado[tema][1] += t
        st.subheader("Por tema (do mais fraco ao mais forte)")
        for tema, (a, t) in sorted(agregado.items(), key=lambda x: x[1][0] / x[1][1]):
            st.progress(a / t, text=f"{tema}: {a}/{t}")
        st.caption("Obs.: no Streamlit Cloud o histórico em arquivo pode ser apagado ao reiniciar o app.")
