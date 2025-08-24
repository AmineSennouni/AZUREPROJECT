PROJECT Lakehouse ADF + Databricks + ADLS (Raw/Silver/Gold)

Statut : dépôt public de démonstration — aucun secret, infra non active (subscription Azure désactivée).

🎯 Résumé

Automatisation de bout en bout d’un flux CSV → Delta dans un Data Lakehouse (zones Raw/Silver/Gold) avec Azure Data Factory (ADF) pour l’orchestration et Azure Databricks pour le traitement.
Déclenchement event-driven (Storage Events), nettoyage & normalisation, idempotence et monitoring.

✨ Points forts

Event-driven : dépôt d’un .csv ⇒ pipeline ADF auto.

Delta Lake partout (silver/gold) pour fiabilité & ACID.

Nommage colonnes sanitizé (compat Delta) ✅

Idempotence : append en bronze, overwrite contrôlé en clean/curated.

Infra simple → trajectoire Managed Identity / Access Connector.

Observabilité : ADF Monitor (triggers, activities) + contrôles Spark.

🏗️ Architecture (vue rapide)
graph LR
A[ADLS Gen2 - Container RAW] -- Storage Event (.csv) --> T[Event Grid]
T --> P[Azure Data Factory - Pipeline]
P --> N1[Databricks Notebook - Ingest_Raw]
N1 --> B[Silver/bronze (Delta)]
P --> N2[Databricks Notebook - Clean_Data]
N2 --> S[Silver/clean (Delta)]
P --> N3[Databricks Notebook - Transform_curated]
N3 --> G[Gold/curated (Delta)]


Compute : Databricks DBR 16.4 LTS (Spark 3.5.2)
Stockage : stmystack4858 (containers raw, silver, gold)
Déclenchement : Event Grid (filtre *.csv sur raw/)

🗂️ Contenu du dépôt
adf/
  arm_template/
    ARMTemplateForFactory.json
    ARMTemplateParametersForFactory.json
databricks/
  notebooks/
    Ingest_Raw.py
    Clean_Data.py
    Transform_curated.py
config/
  dev.yaml                     # Paramètres non sensibles (ex: chemins abfss)
docs/
  rapport.md                   # Contexte, archi, incidents & runbook
  deploiement.md               # (si présent) guide de déploiement
.gitattributes, .gitignore, .editorconfig, LICENSE (si présent)
adf/arm_template/parameters.local.json.example  # Exemple (pas de secrets)

🔧 Détails clés
ADF — Paramètres & mapping du trigger

Paramètres pipeline : storageAccount, rawContainer, silverContainer, goldContainer, fullPathAbfss.

Mapping Storage Events → pipeline :

@concat(triggerBody().folderPath, '/', triggerBody().fileName)


Écriture :

abfss://silver@.../bronze

abfss://gold@.../curated

Databricks — Notebooks

Ingest_Raw : lecture CSV (raw) → sanitization colonnes → Delta (silver/bronze)

Clean_Data : bronze → transformations “clean” (types, nulls, qualité)

Transform_curated : clean → agrégations / business rules → gold/curated

Exemple de sanitization (extrait) :

def sanitize_col(c: str) -> str:
    return (c.strip()
             .lower()
             .replace(" ", "_")
             .replace("(", "")
             .replace(")", "")
             .replace("/", "_"))

df = df.toDF(*[sanitize_col(c) for c in df.columns])

🔒 Sécurité (repo public)

Aucun secret dans Git (tokens, clés). Les fichiers sensibles sont exclus (.gitignore) et remplacés par des placeholders (parameters.local.json.example).

Secret scanning / Dependabot activés sur GitHub (recommandé).

📊 Résultats (exemple à adapter)

Pipeline entièrement automatisé (event-driven)

Latence moyenne < N minutes entre dépôt et gold

N fichiers/jour traités, M colonnes normalisées, 0 opérations manuelles

Remplacer N/M par vos métriques réelles.

🛣️ Roadmap

Accès ADLS via Managed Identity / Access Connector (UC)

Auto Loader + checkpoints (ingestion incrémentale robuste)

Data Quality (Great Expectations) + tests PySpark

Partitionnement par date (/ingest_date=YYYY-MM-DD) en Silver/Gold

Exposition BI : Unity Catalog (tables externes/volumes) + Power BI

📚 Pour en savoir plus

docs/rapport.md : Contexte & objectifs, archi cible, incidents & remédiations, runbook.

docs/deploiement.md : Guide de déploiement ARM + import notebooks (si présent).

👤 Auteur

Amine S. — Data Engineer
Projet vitrine : Azure Data Factory • Databricks • ADLS • Delta Lake • Event-driven pipelines
