# 🎓 SchemeSathi (स्कीम साथी)
### AI-Powered Government Scholarship & Welfare Scheme Finder for Indian Students & Citizens

[![License: CC BY 4.0](https://img.shields.io/badge/Dataset%20License-CC%20BY%204.0-blue.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Qdrant Vector DB](https://img.shields.io/badge/Vector%20DB-Qdrant-DC2626.svg?logo=qdrant&logoColor=white)](https://qdrant.tech)
[![Streamlit App](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Sentence Transformers](https://img.shields.io/badge/Embeddings-MiniLM--L6--v2-orange.svg)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

SchemeSathi is an open-source, AI-powered scholarship and government welfare discovery engine designed to assist Indian students, parents, and citizens in identifying schemes for which they are genuinely eligible. By marrying **deterministic demographic rule filtering** with **dense vector semantic search (Qdrant)** and **lexical keyword matching (BM25)**, SchemeSathi prevents LLM hallucinations and provides verified official links for every recommendation.

---

## 🌟 Key Highlights

- 📦 **Real Knowledge Base**: Built upon **4,693 verified government schemes** from Central Ministries, 28 States, and 8 Union Territories (sourced via *myScheme.gov.in* under CC BY 4.0).
- 🎯 **8-Dimension Demographic Matching**: Evaluates State/UT domicile, education level, annual family income, social category (SC/ST/OBC/EWS/General), gender, residence (rural/urban), BPL status, and disability status.
- 🗄️ **Dual Storage Architecture**:
  - **SQLite**: Sub-millisecond exact demographic pre-filtering.
  - **Qdrant**: Persistent local dense vector semantic similarity search using Sentence Transformers (`all-MiniLM-L6-v2` with Apple Silicon `mps` acceleration).
- 🔍 **Hybrid Retrieval Engine**: Blends dense semantic retrieval with sparse BM25 lexical ranking via **Reciprocal Rank Fusion (RRF)** for acronyms like *NSP, AICTE Pragati, PM-YASASVI, CSSS*.
- 🛡️ **Zero-Hallucination Guardrails**: Hard deterministic checks run *before* context reaches the LLM. If an income cap or eligibility condition is violated, the scheme is dropped.
- 🔗 **Full Provenance & Citations**: Direct links to official guidelines (`official_url`) and direct application forms (`apply_url`) for every scheme card.
- 💬 **Configurable LLM Generation**: Powered by Google Gemini API (`gemini-1.5-flash` at temperature 0.1) with intelligent local deterministic fallback when running offline.

---

## 🏗️ System Architecture

```
[ User Query + 8-Dimension Profile ]
                 │
                 ▼
      [ SQLite Pre-Filter ] (State, Income, Caste, Gender, BPL, PwD, Education)
                 │ (Candidate Scheme Slugs)
                 ▼
 ┌────────────────────────────────────────────────────────┐
 │            Hybrid Search & Rank Fusion                 │
 │  • Dense Semantic Search (Qdrant Cosine Similarity)    │
 │  • Sparse Lexical Search (BM25Okapi Keyword Matching)  │
 │  • Reciprocal Rank Fusion (RRF Scoring)                │
 └────────────────────────────────────────────────────────┘
                 │
                 ▼
  [ Deterministic Rule Engine ] (Hard Boolean Compliance Check)
                 │ (Top-K Verified Schemes)
                 ▼
  [ Grounded LLM Generation ] (Gemini API with Strict Grounding Prompt)
                 │
                 ▼
  [ Verified Output & Scheme Cards ] (Official URLs, Benefits, Deadlines Disclaimer)
```

---

## 📊 Dataset Provenance & Inspection

The project uses the Hugging Face dataset [`smartduketech/indian-government-schemes-2025`](https://huggingface.co/datasets/smartduketech/indian-government-schemes-2025) licensed under **CC BY 4.0**:

- **Total Records**: 4,693 schemes
- **Columns Available (24)**: `slug`, `name`, `description`, `ministry`, `department`, `state`, `category`, `beneficiary_type`, `benefits`, `eligibility_text`, `application_process`, `documents_required`, `apply_url`, `official_url`, `eligibility_age_min`, `eligibility_age_max`, `eligibility_gender`, `eligibility_caste`, `eligibility_income_max`, `eligibility_residence`, `eligibility_state`, `eligibility_disability`, `eligibility_bpl`, `scraped_at`.
- **Central Schemes**: 684
- **State-Specific Schemes**: 4,009
- **Official URLs**: 100% available
- **Application Portal URLs**: 99.8% available
- **Raw Parquet File**: Preserved untouched at `data/raw/schemes_raw.parquet`.

---

## 📈 Empirical Evaluation Results

Evaluated across **32 real-world questions** spanning all categories, income brackets, educational levels, and states (stored in `evaluation/test_questions.json`):

| Evaluation Metric | Measured Result | Benchmark Standard |
|---|:---:|:---:|
| **Eligibility Rule Compliance** | **100.0%** | Zero disqualified schemes returned |
| **Official Citation Integrity** | **100.0%** | All schemes link to verified government sources |
| **State Scope Precision** | **100.0%** | 0% cross-state leakage |
| **Retrieval Relevance (Hit@5)** | **96.9%** | Matches exact domain keywords |
| **Mean Retrieval Latency** | **~513 ms** | Fast local Qdrant + BM25 hybrid search |

*Actual empirical logs and raw evaluation payloads are stored in `evaluation/evaluation_results.json`.*

---

## 📂 Project Directory Structure

```
SchemeSathi/
├── app/
│   ├── main.py                     # Main Streamlit web application
│   └── components/
│       ├── sidebar.py              # 8-field user profile filter UI
│       ├── chat.py                 # Chat history and quick-prompt pills
│       ├── scheme_card.py          # Interactive cards with benefits & links
│       └── disclaimer.py          # Provenance and freshness notice
├── data/
│   ├── raw/
│   │   └── schemes_raw.parquet    # Preserved original Hugging Face dataset
│   └── processed/
│       ├── schemes_clean.csv       # Cleaned, normalized dataset
│       ├── schemes.db             # SQLite indexed database
│       └── embeddings.npy         # Precomputed dense vector cache
├── ingestion/
│   ├── download_dataset.py         # Downloads raw dataset from Hugging Face
│   ├── clean_data.py               # Cleans records, extracts education levels
│   ├── chunking.py                 # Builds rich semantic chunk templates
│   ├── embeddings.py               # Sentence Transformers vector encoder
│   ├── index_qdrant.py             # Local Qdrant collection upsert
│   ├── sqlite_index.py             # SQLite schema and exact pre-filter engine
│   └── run_ingestion.py            # Master end-to-end ingestion orchestrator
├── rag/
│   ├── retrieval.py                # Hybrid RRF search (SQLite + Qdrant + BM25)
│   ├── generation.py               # Grounded Gemini LLM answer generation
│   └── citations.py                # Source attribution & official link builder
├── eligibility/
│   └── matching.py                 # Deterministic rule-based validation engine
├── evaluation/
│   ├── test_questions.json         # 32 benchmark test scenarios
│   ├── evaluate.py                 # Automated empirical evaluation harness
│   └── evaluation_results.json     # Generated benchmark metrics
├── tests/
│   ├── test_cleaning.py            # Unit tests for data cleaning & extraction
│   ├── test_eligibility.py         # Unit tests for eligibility criteria rules
│   └── test_retrieval.py           # Integration tests for Qdrant & BM25
├── qdrant_storage/                 # Persistent local vector database files
├── .env.example                    # Environment variable template
├── .gitignore                      # Safe Git exclusions
├── requirements.txt                # Python dependencies
└── README.md                       # Documentation
```

---

## 🚀 Quickstart & Setup Guide

### 1. Clone & Set Up Virtual Environment

```bash
cd SchemeSathi
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```
Edit `.env` to configure your API key (optional):
```ini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
QDRANT_COLLECTION_NAME=schemes
QDRANT_LOCAL_PATH=./qdrant_storage
EMBEDDING_MODEL=all-MiniLM-L6-v2
```
*(Note: If `GEMINI_API_KEY` is not provided, SchemeSathi operates seamlessly using its built-in deterministic structured response generator!)*

### 3. Run the Ingestion Pipeline

To populate the databases from scratch:

```bash
# 1. Download raw Hugging Face dataset (preserves schemes_raw.parquet)
python ingestion/download_dataset.py

# 2. Clean, normalize, and extract structured fields
python ingestion/clean_data.py

# 3. Populate SQLite, compute embeddings, and index into Qdrant
python ingestion/run_ingestion.py
```

### 4. Launch the Streamlit Web Application

```bash
streamlit run app/main.py
```

Open `http://localhost:8501` in your browser.

---

## 🧪 Running the Test & Evaluation Suites

### Run Pytest Unit Tests
```bash
PYTHONPATH=. pytest tests
```
*Expected: 10/10 tests passing across cleaning, eligibility logic, and vector retrieval.*

### Run Empirical 32-Question Benchmark
```bash
python evaluation/evaluate.py
```

---

## ⚖️ Ethical Design & Disclaimers

1. **Non-Guarantee Clause**: SchemeSathi is an informational discovery engine and **never** guarantees eligibility or admission to any government program.
2. **Dynamic Quotas & Deadlines**: Scholarship application windows and budget quotas change throughout the financial year. Users are directed to official `.gov.in` and `.nic.in` portals for active circulars.
3. **Privacy First**: No demographic or user identity data is logged or transmitted to third parties.

---

## 📜 License & Acknowledgments

- **Dataset**: [smartduketech/indian-government-schemes-2025](https://huggingface.co/datasets/smartduketech/indian-government-schemes-2025) licensed under **CC BY 4.0** (Attribution to [myScheme.gov.in](https://myscheme.gov.in), Government of India).
- **Codebase**: MIT License.

