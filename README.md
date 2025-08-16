# TCC ChatGPT Browser Automation

## 📌 Visão Geral

Este projeto automatiza a interação com o ChatGPT via navegador, permitindo processar artigos científicos em PDF de forma **semiautomática** ou **totalmente automática**.  
O programa abre o navegador, aguarda você concluir login/captcha, envia PDFs para o ChatGPT com diferentes estratégias de prompt (Zero-Shot, Few-Shot e Chain-of-Thought), e salva as respostas no formato JSON consolidado.  

A ferramenta foi desenvolvida para apoiar o TCC, cujo objetivo é comparar as respostas da IA com gabaritos humanos e analisar a ocorrência de **alucinações** na extração de informações.

---

## ⚙️ Funcionamento

1. O programa abre o navegador via **Playwright** e acessa a página inicial do ChatGPT.
2. Ele **aguarda login/captcha manual** até detectar o campo de mensagem.
3. Cada PDF é:
   - Anexado à conversa (se configurado para trabalhar com anexos).
   - Um **prompt** (escolhido pelo usuário) é enviado ao ChatGPT.
   - A resposta é capturada, validada em formato **JSON** e salva em disco.
4. Os resultados são gravados em:
   - `outputs/json/` → JSON estruturados por artigo.
   - `outputs/summaries.md` → arquivo consolidado com todos os resumos.
   - `outputs/debug/` → respostas cruas e prompts (quando ativado o modo DEBUG).

O fluxo continua até processar todos os PDFs definidos na execução.

---

## 📂 Estrutura de Pastas

```
tcc-chatgpt-browser/
│── PDF/                  # Coloque aqui os artigos em PDF
│── prompts/              # Pasta com variantes de prompt (cot, zero, few)
│   ├── cot_with_attachment.txt
│   ├── cot_without_attachment.txt
│   ├── zero_with_attachment.txt
│   ├── zero_without_attachment.txt
│   ├── few_with_attachment.txt
│   ├── few_without_attachment.txt
│   └── fix_json.txt
│── outputs/
│   ├── json/             # Resultados individuais em JSON
│   ├── summaries.md      # Consolidação dos resumos
│   └── debug/            # Logs de debug (opcional)
│── src/                  # Código-fonte principal
│── run.py                # Script principal de execução
│── README.md             # Este arquivo
```

---

## 🚀 Passo a Passo de Uso

### 1. Clonar o repositório e instalar dependências
```bash
git clone <repo-url>
cd tcc-chatgpt-browser
python -m venv .venv
.venv\Scripts\activate   # (Windows PowerShell)
pip install -r requirements.txt
playwright install
```

> ⚠️ Se aparecer erro de execução de script no Windows (`Activate.ps1` bloqueado), use:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

---

### 2. Escolher a variante de prompt
Você pode usar **variáveis de ambiente** ou alterar direto no código:

- **Zero-Shot** → `PROMPT_VARIANT=zero`
- **Few-Shot** → `PROMPT_VARIANT=few`
- **Chain-of-Thought** → `PROMPT_VARIANT=cot` (padrão)

No Windows PowerShell:
```powershell
$env:PROMPT_VARIANT="cot"
```

---

### 3. Colocar os PDFs na pasta correta
Copie os artigos para a pasta (a pasta deve ser criada caso seja a primeira execução):
```
PDF/
```

---

### 4. Rodar o programa
Processar **1 PDF por vez** (padrão):
```bash
python run.py
```

Processar **N PDFs de uma vez**:
```bash
python run.py --count 3   # para 3 PDFs
python run.py --count 10  # para 10 PDFs
```

O programa vai:
- Pausar para login/captcha.
- Assim que o usuário terminar o login/captcha, deve apertar enter no terminal para o programa executar
- Anexar cada PDF e enviar o prompt.
- Salvar automaticamente os resultados.

---

### 5. Consultar os resultados
- Resultados individuais → `outputs/json/*.json`
- Consolidação em Markdown → `outputs/summaries.md`
- Logs de debug (se ativados) → `outputs/debug/`

---

## 🔧 Variáveis Úteis

- `PROMPT_VARIANT` → Escolhe estratégia de prompt (`cot`, `zero`, `few`).
- `MAX_ARTIGOS_POR_EXECUCAO` → Limita PDFs por execução (sobreposto por `--count`).
- `WAIT_AFTER_SEND_SEC` → Tempo de espera entre envios (padrão: 5s).
- `DEBUG_PROMPT=1` → Salva os prompts enviados em `outputs/debug/`.

---

## 📊 Aplicação no TCC

Este projeto permite:
- Comparar **Zero-Shot**, **Few-Shot** e **Chain-of-Thought** em grupos de 3 e 10 artigos.
- Avaliar **consistência das respostas** e **ocorrência de alucinações**.
- Garantir **reprodutibilidade** com prompts versionados em arquivos externos.

---
