# Portfolio — data science & machine learning projects

Source code and notebooks for the project write-ups on
[vollous.github.io](https://vollous.github.io/notes) by João "Chico" Viana.

Each project is self-contained in its own directory. The narrated version of
every project — methods, plots and results — lives on the site; this repo is the
code behind it.

| Project | Write-up | What it is |
|---|---|---|
| [`Project_AI_on_Students/`](Project_AI_on_Students) | [Impact of AI on Students](https://vollous.github.io/notes/impact-of-ai-on-students) | EDA, regression and threshold-tuned classification on a synthetic Kaggle dataset |
| [`Project_Anomaly_Detection/`](Project_Anomaly_Detection) | [Anomaly detection on the MVTec AD database](https://vollous.github.io/notes/anomaly-detection-on-the-mvtec-ad-database) | Zero-shot defect detection: convolutional autoencoders vs PatchCore |
| [`Project_RAG/`](Project_RAG) | [Numpy RAG powered assistant](https://vollous.github.io/notes/project-rag) | A sub-1B LLM boosted with a ChromaDB retrieval layer over the NumPy docs, deployed with Docker Compose |
| [`Project_Incendios/`](Project_Incendios) | — | Wildfire image dataset, work in progress (dataset not tracked) |

## Projects

### Impact of AI on Students — `Project_AI_on_Students/`

Notebook: `ai-impact-on-students.ipynb`. Data:
[AI impact on students](https://www.kaggle.com/datasets/laveshjadon/ai-impact-on-students)
(synthetic, from Kaggle — not included).

- EDA and encoding of the categorical / ordinal columns.
- Data cleaning: synthetic-data artefacts (excesses in `Weekly_GenAI_Hours`,
  `Traditional_Study_Hours`, `Skill_Retention_Score`) located with a per-bin
  binomial test and removed.
- Feature selection by combining `RFECV` (boosted trees, random forest) and
  tree-based feature importance.
- **Regression** on `Post_Semester_GPA` — Linear, KNN, Random Forest, Gradient
  Boosted Trees and SVR, compared with 5-fold CV on RMSE. Best model: an RBF
  SVR at RMSE ≈ 0.145 (~4% of the mean GPA).
- **Classification** of `Burnout_Risk_Level` — KNN, Random Forest, GBT, SVC and
  a small NN, with decision-threshold tuning on the `High` class to reach ≥ 0.9
  recall so at-risk students are not missed.

The `*_reports.npy` files cache the cross-validation results the notebook plots.

### Anomaly detection on the MVTec AD database — `Project_Anomaly_Detection/`

Notebooks: `bottle.ipynb`, `carpet.ipynb`, `hazelnut.ipynb` — one per category.
Zero-shot anomaly detection: train only on defect-free images, then separate
nominal from anomalous at test time.

- **Convolutional autoencoders** — six architectures (`Autoencoder_000`–`005`),
  MSE loss, Adam, 100 epochs each. Trained weights in `bottle_models/`,
  `carpet_models/`, `hazelnut_models/`.
- **PatchCore** ([arXiv:2106.08265](https://arxiv.org/abs/2106.08265)) — memory
  bank of pretrained-backbone features, with a sweep over `backbone`
  (`resnet50`, `wide_resnet50_2`), `coreset_sampling_ratio` and `num_neighbors`.
  PatchCore reaches AUC = 1 on bottle and hazelnut; CAEs perform poorly.

The [MVTec AD dataset](https://www.mvtec.com/company/research/datasets/mvtec-ad)
is not included — download it and drop the per-category folders (`bottle/`,
`carpet/`, `hazelnut/`, …) into this directory; they are git-ignored. Model
outputs land in `results/` and `openvino_cache/`.

### Numpy RAG powered assistant — `Project_RAG/`

A retrieval-augmented chat over the [NumPy 2.5 documentation](https://numpy.org/doc/2.5/),
built to make the difference RAG makes obvious by pairing it with a tiny model
([`ibm-granite/granite-4.0-h-350m`](https://huggingface.co/ibm-granite/granite-4.0-h-350m),
350M params).

```
data/data_processing.ipynb   parse the NumPy HTML docs with BeautifulSoup
                             (one <article> = one chunk) → backend/chroma.db
llm/        Dockerfile        Ollama serving ibm/granite4:350m
backend/    backend.py        FastAPI, POST /chat/, ChromaDB retrieval
                              (all-MiniLM-L6-v2 embeddings, cosine distance, top-10)
frontend/   streamlit_app.py  Streamlit UI: plain chat vs RAG chat, side by side
compose.yaml                  three containers, only port 8080 published
```

To run:

1. Generate the vector store by running `data/data_processing.ipynb` (writes
   `backend/chroma.db`).
2. Build the three images referenced by `compose.yaml`
   (`granite4_350m`, `numpyragbackend`, `numpyragfrontend`) from the Dockerfile
   in `llm/`, `backend/` and `frontend/`.
3. `docker compose -f Project_RAG/compose.yaml up`, then open
   <http://localhost:8080>.

On macOS the backend points at `host.docker.internal:11434`, so run Ollama on
the host (Docker containers can't use Metal) instead of the `ollama` container.

## Running the notebooks

The three analysis projects are Jupyter notebooks. There is no repo-wide
environment; the main dependencies are Python 3.12 with `pytorch`,
`scikit-learn`, `pandas`, `numpy`, `matplotlib`, `scipy`, `anomalib`
(PatchCore), `beautifulsoup4` and `chromadb`. `Project_RAG/` pins its own
dependencies in `backend/requirements.txt` and `frontend/requirements.txt`.

Large or third-party files — datasets, the Chroma store, some model outputs —
are git-ignored; see `.gitignore` and each section above for where to get them.
