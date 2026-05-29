# 📄 PDF Plumber Extractor

Ferramenta para extração automatizada de dados de **laudos de Análise de Risco (HRN/APR)** em formato PDF, convertendo as tabelas em arquivos **JSON estruturados** e armazenando tudo em um banco de dados **SQLite** para consulta e integração.

---

## 🧠 O que o projeto faz

A partir de uma pasta com um ou mais PDFs, o sistema:

1. Percorre todas as páginas de cada PDF e identifica as tabelas de risco
2. Extrai e mapeia automaticamente os campos: `Tipo/Grupo`, `Perigo`, `Risco/Consequência`, `P`, `F`, `GPL`, `NP`, `Avaliação`, `Medidas de Controle`, `Foto`, entre outros
3. Extrai o cabeçalho de cada laudo (técnico responsável, equipamento, fabricante, etc.)
4. Gera um arquivo `.json` individual por PDF
5. Importa todos os JSONs para um banco de dados SQLite, evitando duplicatas

---

## 📋 Pré-requisitos

- **Python 3.9+** instalado na máquina
- Gerenciador de pacotes `pip`

> Para verificar se você já tem o Python instalado, rode no terminal:
> ```bash
> python --version
> ```

---

## 📁 Estrutura esperada do projeto

Antes de executar, certifique-se de que a estrutura de pastas esteja assim:

```
pdfplumber_extractor/
│
├── pdfs/                        ← 📂 CRIE ESTA PASTA e coloque seus PDFs aqui
│   ├── laudo_maquina_01.pdf
│   ├── laudo_maquina_02.pdf
│   └── ...
│
├── database/                    ← criada automaticamente pelo script
├── main.py
├── extractor.py
├── estrutura_db.py
├── header.py
├── requirements.txt
└── README.md
```

> ⚠️ **A pasta `pdfs/` não é criada automaticamente.** Você precisa criá-la manualmente antes de rodar o projeto, vamos consertar isso futuramente.

---

##  Guia de execução passo a passo

### 1. Clone o repositório

```bash
git clone https://github.com/raffaela09/pdfplumber_extractor.git
cd pdfplumber_extractor
```

### 2. (Recomendado) Crie um ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Crie a pasta `pdfs` e adicione seus arquivos

```bash
# Windows
mkdir pdfs

# Linux / macOS
mkdir pdfs
```

Em seguida, copie ou mova todos os arquivos `.pdf` que deseja processar para dentro da pasta `pdfs/`.

### 5. Execute o projeto

```bash
python main.py
```

---

## 📦 Dependências (`requirements.txt`)

| Pacote | Versão | Finalidade |
|---|---|---|
| `pdfplumber` | 0.11.9 | Extração de texto e tabelas de PDFs |
| `pdfminer.six` | 20251230 | Backend de leitura de PDF (usado pelo pdfplumber) |
| `pillow` | 12.2.0 | Processamento de imagens extraídas |
| `pypdfium2` | 5.8.0 | Renderização de páginas PDF |
| `cryptography` | 48.0.0 | Suporte a PDFs protegidos |
| `cffi` | 2.0.0 | Interface C para bibliotecas nativas |
| `charset-normalizer` | 3.4.7 | Detecção de encoding de texto |
| `pycparser` | 3.0 | Dependência do cffi |

> Para extrair imagens dos PDFs, o projeto também utiliza **`fitz` (PyMuPDF)**, que pode ser instalado separadamente:
> ```bash
> pip install pymupdf
> ```

---

## 📂 O que é gerado após a execução

Após rodar `python main.py`, as seguintes pastas e arquivos serão criados automaticamente:

```
pdfs/
├── resultados_json/             ← um .json por PDF com os riscos extraídos
│   ├── laudo_maquina_01.json
│   └── laudo_maquina_02.json
│
└── resultados_json_cabecalhos/  ← um .json por PDF com os dados do cabeçalho
    ├── laudo_maquina_01_cabecalho.json
    └── laudo_maquina_02_cabecalho.json

hst_database.sqlite.txt          ← banco de dados SQLite com todos os dados
```

---

## ❓ Problemas comuns

**`ModuleNotFoundError: No module named 'pdfplumber'`**
> Certifique-se de que instalou as dependências com `pip install -r requirements.txt` e que o ambiente virtual está ativo.

**`Nenhum arquivo PDF encontrado`**
> Verifique se a pasta `pdfs/` existe na raiz do projeto e se há arquivos `.pdf` dentro dela.

**O JSON gerado está vazio ou com poucos dados**
> O extrator foi desenvolvido para um formato específico de laudo HRN. PDFs com estrutura de tabela muito diferente podem não ser reconhecidos corretamente.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Para sugerir melhorias ou reportar problemas, abra uma [issue](https://github.com/raffaela09/pdfplumber_extractor/issues) no repositório.

---


