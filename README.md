# 📊 Data Analyst Agent

Assistente de análise de dados local, simples e direto.

Você envia uma planilha (CSV ou Excel), faz perguntas em português (“Quais são os 5 produtos que mais vendem?”, “Qual o total de pacientes únicos em 2024?”), e ele devolve a resposta analisada.
Por trás disso, a IA escreve a consulta SQL necessária, executa essa consulta localmente e mostra o resultado pra você.

---

## 1. O que essa aplicação faz

* Lê sua base de dados (CSV/XLSX).
* Tenta entender o que você quer saber em linguagem normal.
* Gera automaticamente uma query SQL para responder.
* Executa essa query localmente usando DuckDB.
* Mostra a resposta na tela.

Exemplo real de uso:

* Pergunta:

  > "Quais são os 10 hospitais com maior volume em 2024?"
* O agente:

  * Gera SQL sozinho.
  * Executa sobre sua planilha.
  * Te mostra o ranking.

Você não precisa saber SQL.
Você não precisa saber Python.

---

## 2. Para quem isso foi feito

* Área de negócios / acesso / inteligência de mercado que quer resposta rápida.
* Pessoas que trabalham com Excel, mas não com programação.
* Quem precisa testar hipóteses com base em dados internos sem depender de outra equipe.

---

## 3. Arquivos importantes do projeto

### `ai_data_analyst.py`

Aplicação principal (frontend e backend ao mesmo tempo).
Esse arquivo:

* Sobe uma interface web usando Streamlit.
* Recebe o upload da planilha.
* Limpa e prepara os dados.
* Carrega os dados em uma tabela chamada `uploaded_data`.
* Usa IA para gerar a query SQL.
* Executa e mostra o resultado.

Principais blocos dentro dele:

1. Importações e configuração (`dotenv`, `streamlit`, `DuckDbAgent`, etc.).
2. Função `preprocess_and_save()`:

   * Lê o arquivo enviado.
   * Converte datas e números.
   * Trata aspas.
   * Salva um CSV temporário pronto para consulta.
3. Montagem do `semantic_model`:

   * Diz para o agente: “você tem uma tabela chamada `uploaded_data`, que está neste caminho aqui”.
4. Instancia o agente (`DuckDbAgent`) com o modelo da OpenAI configurado.
5. Interface para o usuário:

   * Preview da planilha.
   * Caixa de pergunta.
   * Botão “Enviar pergunta”.
   * Retorno da análise.

---

### `Keys.env`

Arquivo que guarda suas credenciais e configurações do modelo de IA.

Exemplo de conteúdo:

```env
OPENAI_API_KEY="sk-sua_chave_aqui"
OPENAI_MODEL="gpt-4o-mini"
```

Notas importantes:

* `OPENAI_API_KEY` é a chave que você pega na OpenAI.
* O app só roda se essa variável existir e começar com `sk-`.
* Esse arquivo NÃO deve ir para GitHub público. Adicione ao `.gitignore` se for repositório aberto.

---

### `requirements.txt`

Lista tudo que precisa ser instalado em Python para rodar o projeto.

Você vai usar esse arquivo no comando `pip install -r requirements.txt`.

---

## 4. Requisitos para rodar

* Windows com Python instalado.
* Acesso à internet (só para a IA gerar a consulta).
* Uma chave de API válida da OpenAI.
* Um arquivo CSV ou Excel para análise.

Observação: abaixo está o passo a passo pensado para Windows sem criar ambiente virtual (venv). É direto no Python instalado na máquina.

---

## 5. Como rodar (passo a passo no Windows, sem venv)

### Passo 1. Instalar o Python (se ainda não tiver)

* Baixe e instale o Python pelo site oficial.
* Durante a instalação, marque a opção “Add Python to PATH”.

Para confirmar que deu certo, abra o PowerShell e rode:

```powershell
python --version
```

ou

```powershell
py --version
```

Se aparecer a versão (por exemplo `Python 3.11.x`), está ok.

---

### Passo 2. Baixar o projeto

Você precisa ter estes arquivos na mesma pasta:

* `ai_data_analyst.py`
* `requirements.txt`
* `Keys.env` (você cria esse manualmente, veja próximo passo)

Exemplo de pasta:

```text
C:\DataAnalystAgent\
    ai_data_analyst.py
    requirements.txt
    Keys.env
```

Abra o PowerShell nessa pasta.

Dica rápida:
No Explorer do Windows, vá até a pasta, clique na barra de endereço, digite `powershell` e aperte Enter.
Isso já abre o PowerShell exatamente na pasta certa.

---

### Passo 3. Criar o arquivo `Keys.env`

Crie um arquivo de texto chamado `Keys.env` dentro dessa mesma pasta e coloque o conteúdo:

```env
OPENAI_API_KEY="sk-a-sua-chave-da-openai-aqui"
OPENAI_MODEL="gpt-4o-mini"
```

Ajuste os valores:

* Troque `"sk-a-sua-chave-da-openai-aqui"` pela sua chave real.
* Se quiser usar outro modelo que sua conta suporta, troque `"gpt-4o-mini"`.

Salve.

---

### Passo 4. Instalar as dependências

No PowerShell, ainda dentro da pasta do projeto, rode:

```powershell
pip install -r requirements.txt
```

Isso instala todas as bibliotecas necessárias (Streamlit, DuckDbAgent, etc).

Se o comando `pip` não funcionar, tente:

```powershell
python -m pip install -r requirements.txt
```

ou

```powershell
py -m pip install -r requirements.txt
```

---

### Passo 5. Executar a aplicação

Ainda no PowerShell:

```powershell
py -m streamlit run ai_data_analyst.py
```

Após alguns segundos, o navegador (Chrome, Edge, etc.) vai abrir automaticamente com a interface do app.
Se não abrir sozinho, copie e cole no navegador o endereço que aparece no terminal (geralmente `http://localhost:8501`).

Pronto. A aplicação está rodando.

---

## 6. Como usar a interface

1. **Enviar o arquivo**

   * No campo “Envie um arquivo CSV ou Excel”, faça o upload do seu arquivo.
   * Formatos aceitos: `.csv` e `.xlsx`.

2. **Visualizar os dados**

   * A aplicação mostra uma amostra da tabela carregada.
   * Mostra também os nomes das colunas detectadas.

3. **Fazer perguntas**

   * Você verá uma caixa de texto com algo como:

     > Exemplo: "Quais são os 5 produtos com maior faturamento em 2024?"
   * Você escreve sua pergunta e clica em “Enviar pergunta”.

4. **Ler a resposta**

   * A IA gera uma consulta SQL, executa localmente e devolve o resultado.
   * A resposta aparece na própria página.

5. **Checar log técnico (avançado)**

   * No PowerShell onde você rodou o `streamlit run`, aparecem mensagens de log mais técnicas.
     Isso é útil se você estiver validando o SQL gerado ou depurando erro.

---

## 7. O que acontece nos bastidores (resumido)

1. O arquivo que você enviou é carregado em um `DataFrame` do pandas.
2. O código tenta:

   * Converter colunas de data em datas.
   * Converter números que estão como texto em número de verdade.
   * Padronizar aspas e salvar um CSV temporário limpo.
3. Esse CSV temporário vira uma tabela chamada `uploaded_data`.
4. O agente de IA recebe:

   * Sua pergunta em linguagem natural.
   * A informação de que existe uma tabela `uploaded_data` com tais colunas.
5. O agente escreve uma consulta SQL com base nisso.
6. Essa consulta roda localmente no DuckDB.
7. O resultado é devolvido pra você.

Importante:

* A lógica de segurança básica impede rodar se não houver chave válida da OpenAI no `Keys.env`.
* O dado em si é processado localmente.
  Mas a sua pergunta e o contexto do esquema da tabela são enviados ao modelo da OpenAI para que ele consiga montar a query SQL.

Se você trabalha com dado sensível, avalie a política interna antes de usar.

---

## 8. Limitações conhecidas

* Planilhas muito “sujas” (cabeçalho em várias linhas, células combinadas, subtotais manuais no meio da tabela etc.) podem confundir a análise.
* Perguntas vagas demais podem resultar em SQL inválido (por exemplo: “mostra tudo de tudo”).
* A IA não “adivinha” o que uma coluna significa se o nome estiver genérico ou confuso (ex.: `x1`, `coluna_sem_nome_2`).
  Quanto mais claros forem os nomes das colunas, melhor a resposta.
* Atualmente o app trabalha 1 tabela por vez. Se você tiver fato + dimensão e precisar de JOIN, precisa estar tudo já junto no mesmo arquivo antes do upload.

---

## 9. Próximos passos possíveis (roadmap)

* Exportar os resultados direto em CSV/XLSX.
* Mostrar gráficos automáticos (barras, linha, participação %).
* Salvar o histórico das perguntas do usuário.
* Suporte a múltiplas tabelas no mesmo upload.
* Versão corporativa integrada ao Teams / copilot interno / RLS.
* Opção de rodar com LLM privado ou modelo local (sem enviar contexto para OpenAI).

---

## 10. Suporte / evolução

Este projeto foi pensado como um ponto de partida.
Ele já resolve o básico: “manda planilha, faz pergunta, recebe análise”.
A partir daqui você pode adaptar para seu cenário, por exemplo:

* Fixar filtros de negócio (ex.: “considere só pacientes ativos”, “somente linha SUS”, etc.).
* Criar perguntas guiadas (“Top 10 hospitais”, “Evolução mensal por UF”, etc.).
* Integrar em dashboards para diretoria.

Se você recebeu este código, pode usar internamente, adaptar e evoluir.
