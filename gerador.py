"""Geração de questões no estilo FCC usando a API do Claude."""

import json
import re

import anthropic

MODELO_PADRAO = "claude-sonnet-5-5"

SISTEMA = """Você é elaborador de questões da banca FCC (Fundação Carlos Chagas) \
para concursos de professor de Biologia da rede estadual.

Estilo FCC que você deve seguir:
- Questões de múltipla escolha com 5 alternativas (A a E) e apenas uma correta.
- Enunciados contextualizados, claros, frequentemente com situação-problema, \
texto-base, dados, experimento ou contexto escolar/pedagógico.
- Alternativas plausíveis, de tamanho semelhante, sem pegadinhas ambíguas; \
distratores baseados em erros conceituais comuns.
- Linguagem formal, sem "todas as anteriores" nem "nenhuma das anteriores".
- Rigor científico e, nas questões pedagógicas, fidelidade à legislação e \
documentos oficiais (LDB, BNCC).
- Você NÃO reproduz questões reais de provas anteriores: crie questões inéditas.

Responda SOMENTE com JSON válido, sem texto fora do JSON."""

FORMATO = """Formato de saída:
{
  "questoes": [
    {
      "tema": "...",
      "enunciado": "...",
      "alternativas": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
      "gabarito": "A",
      "comentario": "Explicação da alternativa correta e por que cada distrator está errado."
    }
  ]
}"""


def _extrair_json(texto: str) -> dict:
    texto = texto.strip()
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto)
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError("A resposta da IA não contém JSON.")
    return json.loads(texto[inicio : fim + 1])


def _validar(q: dict) -> bool:
    alts = q.get("alternativas", {})
    return (
        isinstance(alts, dict)
        and set(alts) == set("ABCDE")
        and q.get("gabarito") in alts
        and q.get("enunciado")
    )


def gerar_questoes(
    api_key: str,
    temas: list[str],
    quantidade: int,
    nivel: str,
    modelo: str = MODELO_PADRAO,
) -> list[dict]:
    cliente = anthropic.Anthropic(api_key=api_key)
    pedido = (
        f"Gere {quantidade} questões inéditas, nível {nivel}, distribuídas de "
        f"forma equilibrada entre os temas abaixo:\n- "
        + "\n- ".join(temas)
        + "\n\nVarie a posição do gabarito entre A e E.\n\n"
        + FORMATO
    )
    resposta = cliente.messages.create(
        model=modelo,
        max_tokens=8000,
        system=SISTEMA,
        messages=[{"role": "user", "content": pedido}],
    )
    texto = "".join(b.text for b in resposta.content if b.type == "text")
    dados = _extrair_json(texto)
    questoes = [q for q in dados.get("questoes", []) if _validar(q)]
    if not questoes:
        raise ValueError("Nenhuma questão válida foi gerada. Tente novamente.")
    return questoes
