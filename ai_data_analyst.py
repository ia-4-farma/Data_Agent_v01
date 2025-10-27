# ai_data_analyst.py
# ---------------------------------------------------------
# Aplicação Streamlit que:
# 1. Recebe um arquivo de dados (CSV ou Excel)
# 2. Limpa e prepara os dados
# 3. Carrega esses dados em DuckDB
# 4. Usa IA (OpenAI) para gerar consultas SQL automaticamente
# 5. Mostra a resposta para o usuário
#
# Requisitos principais:
# - Python 3.x
# - requirements.txt instalado
# - Arquivo Keys.env com OPENAI_API_KEY e OPENAI_MODEL
# ---------------------------------------------------------


# -------------------------
# IMPORTAÇÕES DE BIBLIOTECAS
# -------------------------
import os
import json
import csv
import re
import tempfile
import streamlit as st
import pandas as pd
from dotenv import load_dotenv  # Para ler variáveis de ambiente de Keys.env

from agno.models.openai import OpenAIChat  # Modelo de linguagem (LLM) da OpenAI
from phi.agent.duckdb import DuckDbAgent   # Agente que conversa com DuckDB e gera SQL
from agno.tools.pandas import PandasTools # Ferramentas auxiliares p/ pandas (ativadas via tools_enabled)


# -------------------------
# CARREGAMENTO DE CREDENCIAIS / CONFIGURAÇÃO INICIAL
# -------------------------
# Carrega as variáveis definidas em "Keys.env" para dentro do ambiente
# Esperado no Keys.env:
#   OPENAI_API_KEY="sua_chave_aqui"
#   OPENAI_MODEL="nome_do_modelo"
load_dotenv("Keys.env")

# Lê as variáveis do ambiente (já disponíveis após load_dotenv)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")


# -------------------------
# FUNÇÃO: PREPARAR E SALVAR O ARQUIVO ENVIADO
# -------------------------
def preprocess_and_save(file):
    """
    Lê o arquivo enviado pelo usuário (CSV ou Excel), faz alguns tratamentos
    e salva uma cópia temporária em CSV (com aspas em todos os campos de texto)
    para consumo pelo DuckDbAgent.

    Retorna:
        temp_path (str): caminho do arquivo CSV temporário já tratado
        columns (list[str]): lista com os nomes das colunas
        df (pd.DataFrame): dataframe carregado
    Em caso de erro, retorna (None, None, None)
    """
    try:
        # 1. Leitura do arquivo em DataFrame
        if file.name.endswith('.csv'):
            df = pd.read_csv(
                file,
                encoding='utf-8',
                na_values=['NA', 'N/A', 'missing']  # trata valores ausentes
            )
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(
                file,
                na_values=['NA', 'N/A', 'missing']
            )
        else:
            st.error("Formato não suportado. Envie um arquivo CSV ou Excel (.xlsx).")
            return None, None, None

        # 2. Tratamento de colunas texto: garantir aspas corretas
        #    - Substitui aspas duplas internas por aspas duplas duplicadas
        for col in df.select_dtypes(include=['object']):
            df[col] = (
                df[col]
                .astype(str)
                .replace({r'"': '""'}, regex=True)
            )

        # 3. Tentativa de conversão automática de datas e números
        #    - Colunas que parecem datas -> datetime
        #    - Colunas 'object' que parecem número -> numeric
        for col in df.columns:
            # Heurística simples: se o nome da coluna contém "date", tenta converter p/ data
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')

            # Se ainda é 'object', tenta converter para número (quando possível)
            elif df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    # Se não der pra virar número, deixa como texto
                    pass

        # 4. Salva o DataFrame limpo em um arquivo CSV temporário
        #    - quoting=csv.QUOTE_ALL força todos os campos a ficarem entre aspas
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".csv"
        ) as temp_file:
            temp_path = temp_file.name
            df.to_csv(
                temp_path,
                index=False,
                quoting=csv.QUOTE_ALL
            )

        # Retorna caminho do CSV tratado, lista de colunas e o próprio df
        return temp_path, df.columns.tolist(), df

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
        return None, None, None


# -------------------------
# INTERFACE PRINCIPAL (STREAMLIT)
# -------------------------
st.title("📊 Data Analyst Agent")
st.write(
    "Envie uma planilha, faça perguntas em linguagem natural "
    "e receba a análise automaticamente gerada via SQL."
)


# -------------------------
# SIDEBAR (CONFIGURAÇÃO / STATUS)
# -------------------------
with st.sidebar:
    st.header("Configurações")

    # Verificação básica da chave antes de liberar o app
    # - Se a chave não existir ou não tiver cara de chave válida, paramos execução
    if OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-"):
        st.success("Chave da OpenAI carregada com sucesso!")
        st.info(f"Modelo em uso: `{OPENAI_MODEL}`")
    else:
        st.error("Chave da OpenAI não encontrada ou inválida no arquivo Keys.env.")
        # st.stop() interrompe o Streamlit imediatamente
        st.stop()


# -------------------------
# UPLOAD DO ARQUIVO DE DADOS
# -------------------------
uploaded_file = st.file_uploader(
    "Envie um arquivo CSV ou Excel",
    type=["csv", "xlsx"]
)


# Só continuamos se o usuário já fez upload
if uploaded_file is not None:

    # 1. Lê e prepara o arquivo enviado
    temp_path, columns, df = preprocess_and_save(uploaded_file)

    # 2. Se deu tudo certo no preprocess
    if temp_path and columns and df is not None:

        # ---- Visualização básica dos dados enviados ----
        st.subheader("Pré-visualização dos dados enviados")
        st.dataframe(df)  # tabela interativa
        st.caption("Visualização inicial dos dados carregados.")

        # Lista de colunas detectadas
        st.write("Colunas encontradas no arquivo:")
        st.code(columns, language="python")

        # ---- Monta o 'semantic_model' para o DuckDbAgent ----
        # Esse modelo informa ao agente:
        # - Nome lógico da tabela ("uploaded_data")
        # - Descrição
        # - Caminho físico do CSV temporário gerado
        semantic_model = {
            "tables": [
                {
                    "name": "uploaded_data",
                    "description": "Tabela temporária contendo os dados enviados pelo usuário.",
                    "path": temp_path,
                }
            ]
        }

        # -------------------------
        # CONFIGURAÇÃO DO AGENTE (DuckDbAgent)
        # -------------------------
        # O DuckDbAgent é quem:
        # - Lê o semantic_model
        # - Recebe a pergunta do usuário em texto livre
        # - Usa o modelo da OpenAI (LLM) para gerar uma query SQL
        # - Executa a query em DuckDB
        # - Retorna o resultado
        #
        # Parâmetros importantes:
        # - llm: qual modelo de linguagem usar (id = nome do modelo; api_key = chave)
        # - tools_enabled=True: habilita utilitários tipo PandasTools
        # - system_prompt: instruções de "como" o agente deve responder
        duckdb_agent = DuckDbAgent(
            llm=OpenAIChat(
                id=OPENAI_MODEL,
                api_key=OPENAI_API_KEY
            ),
            semantic_model=json.dumps(semantic_model),
            tools_enabled=True,          # ativa ferramentas auxiliares
            markdown=True,               # formata resposta em Markdown
            add_history_to_messages=False,
            followups=False,
            read_tool_call_history=False,
            system_prompt=(
                "You are an expert data analyst. "
                "Generate SQL queries to solve the user's query. "
                "Return only the SQL query, enclosed in ```sql ``` and give the final answer."
            ),
        )

        # -------------------------
        # ESTADO DE SESSÃO (PARA GUARDAR RESPOSTAS)
        # -------------------------
        # Caso no futuro a gente queira reaproveitar a última resposta gerada,
        # podemos armazenar no session_state.
        if "generated_code" not in st.session_state:
            st.session_state.generated_code = None

        # -------------------------
        # ENTRADA DE PERGUNTA DO USUÁRIO
        # -------------------------
        st.subheader("Faça uma pergunta sobre os dados")
        user_query = st.text_area(
            "Exemplo: 'Quais são os 5 produtos com maior faturamento em 2024?'"
        )

        # Dica para o usuário acompanhar logs no terminal
        st.info(
            "💡 Dica técnica: verifique também o terminal onde você rodou o Streamlit "
            "para ver logs detalhados da execução do agente."
        )

        # Botão para enviar a pergunta
        if st.button("Enviar pergunta"):
            if user_query.strip() == "":
                st.warning("Por favor, escreva uma pergunta antes de enviar.")
            else:
                try:
                    with st.spinner("Analisando sua pergunta..."):

                        # 1. Executa a pergunta no agente
                        #    O agente normalmente retorna um objeto complexo (RunResponse)
                        response1 = duckdb_agent.run(user_query)

                        # 2. Extrai o texto útil de dentro do objeto retornado
                        if hasattr(response1, "content"):
                            response_content = response1.content
                        else:
                            response_content = str(response1)

                        # 3. Gera uma versão 'bonitinha' para exibição (stream=True)
                        #    Observação: print_response escreve também no terminal.
                        duckdb_agent.print_response(
                            user_query,
                            stream=True,
                        )

                    # 4. Mostra o resultado final para o usuário na interface
                    st.markdown(response_content)

                except Exception as e:
                    # Tratamento de erro amigável:
                    # - Pode acontecer por sintaxe SQL inválida
                    # - Coluna digitada errada, etc.
                    st.error(f"Erro ao gerar a resposta: {e}")
                    st.error(
                        "Tente reformular a pergunta ou verifique se o arquivo possui "
                        "as colunas necessárias."
                    )