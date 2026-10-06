# 🧬 Simulados SEDUC-MA (FCC) com IA

App em Streamlit que gera simulados inéditos de Biologia no estilo da banca FCC, corrige na hora e mostra seu desempenho por tema.

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edite o secrets.toml com sua ANTHROPIC_API_KEY
streamlit run app.py
```

## Publicar (GitHub + Streamlit Community Cloud)

```bash
git init
git add .
git commit -m "Simulados SEDUC-MA"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/simulados-seduc-ma.git
git push -u origin main
```

1. Acesse https://share.streamlit.io e conecte seu GitHub.
2. Escolha o repositório, branch `main` e arquivo `app.py`.
3. Em **Advanced settings > Secrets**, cole: `ANTHROPIC_API_KEY = "sk-ant-..."`.
4. Deploy.

**Nunca** suba o `secrets.toml` (já está no `.gitignore`).

## Estrutura

- `app.py` – interface Streamlit
- `gerador.py` – prompt estilo FCC + chamada à API
- `conteudo.py` – áreas e tópicos (ajuste conforme o edital)
- `historico.json` – desempenho (criado automaticamente, ignorado pelo git)

## Próximos passos

- Atualizar `conteudo.py` com o conteúdo programático do edital quando sair.
- Persistir o histórico em banco (ex.: Supabase) para não perder no deploy.
- Exportar simulado em PDF.

> As questões são geradas por IA: confira pontos duvidosos em fontes oficiais.
