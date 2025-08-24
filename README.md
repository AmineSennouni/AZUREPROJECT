EDF Paris — ADF + Databricks + ADLS (Lakehouse Raw/Silver/Gold)
Objet

Automatiser l’ingestion CSV → nettoyage → curated (Delta) via Azure Data Factory (event-driven) et notebooks Azure Databricks.

Architecture (résumé)

Stockage : ADLS Gen2 stmystack4858 (containers : raw, silver, gold)

Compute : Databricks DBR 16.4 LTS (Spark 3.5.2)

Orchestration : ADF (3 notebooks en série), trigger Event Grid sur .csv

Arborescence

adf/
arm_template/ — export ARM de la factory
artifacts/ — JSON ADF si connecté à Git
databricks/
notebooks/ — notebooks .py (format SOURCE)
configs/ — conf spark/cluster (sans secrets)
jobs/ — définitions de jobs
config/
dev.yaml — paramètres non sensibles
docs/
rapport.md — ton rapport
scripts/
export_dbx.sh — (optionnel) export CLI Databricks

Déploiement (idée générale)

ADF : déployer l’ARM (adf/arm_template) avec paramètres d’env.

Databricks : importer databricks/notebooks et créer job/pipeline.

Secrets : Key Vault / Databricks Secrets (pas de clés en clair).

Opérations

Event-driven : dépôt CSV → bronze/silver/gold

Monitoring : ADF (runs/activités), Databricks (job runs), contrôles Delta

Sécurité

Ne pas commiter de secrets (clé ADLS, tokens). Utiliser Key Vault / Managed Identity / Access Connector.