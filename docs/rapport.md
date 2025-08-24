Rapport de réalisation (EDF Paris – ADF + Databricks + ADLS)
1) Contexte & objectifs

Client/Contexte : EDF – Paris, équipe Data Engineering.
Objectif : automatiser un flux d’ingestion CSV → nettoyage → curated dans un Data Lakehouse (zones Raw/Silver/Gold) avec Azure Data Factory (ADF) et Azure Databricks.
Contraintes : mise en prod rapide, simplicité → choix initial Account Key (clé de stockage) pour l’accès ADLS, en gardant une trajectoire vers MI/Access Connector si besoin.

2) Architecture cible

Stockage : ADLS Gen2 – compte stmystack4858 ; containers : raw, silver, gold.
Compute : Databricks DBR 16.4 LTS (Spark 3.5.2).
Orchestration : ADF pipeline 3 étapes en série :

Ingest_Raw (Notebook) : CSV (raw) → Delta (silver/bronze)

Clean_Data (Notebook) : bronze → silver/clean

Transform_curated (Notebook) : clean → gold/curated

Déclenchement : Trigger Storage events (Event Grid) sur raw, filtre .csv.

Paramétrage ADF (pipeline) :
storageAccount=stmystack4858, rawContainer=raw, silverContainer=silver, goldContainer=gold, fullPathAbfss (renseigné par le trigger).

Mapping du trigger → pipeline :

fullPathAbfss = @concat(triggerBody().folderPath, '/', triggerBody().fileName)


On reconstruit l’URL ABFSS complète dans l’activité Ingest.

Chemins d’écriture :

silverPath = abfss://silver@stmystack4858.dfs.core.windows.net/bronze
goldPath   = abfss://gold@stmystack4858.dfs.core.windows.net/curated

3) Détails techniques & décisions

Accès ADLS (simple & rapide) : ajout dans la config Spark du cluster :

spark.hadoop.fs.azure.account.key.stmystack4858.dfs.core.windows.net <KEY>
spark.hadoop.fs.azure.createRemoteFileSystemDuringInitialization true


✔️ Validation lecture/écriture ABFSS via dbutils.fs.ls et spark.read.csv(...).write.format("delta").

ABFSS partout (pas de wasbs: ni dbfs:/mnt) pour éviter les problèmes d’autorisations/montages.

Sanitization des noms de colonnes à l’ingest (remplacement des espaces, parenthèses, etc.) pour compatibilité Delta.

Idempotence : écriture append en bronze + overwrite contrôlé en clean/curated ; possibilité d’ajouter ensuite du merge ou de l’Auto Loader.

4) Incidents rencontrés & remédiations

❌ Invalid configuration value for fs.azure.account.key
➜ Le cluster cherchait une clé non fournie → ajout de la clé dans Spark Config + redémarrage.

❌ Paramètre vide (fullPathWasbs) en Ingest
➜ Renommage & unification en fullPathAbfss + mapping correct via trigger ou valeur manuelle en debug.

❌ Expressions ADF invalides (usage de item()?.pipelineParameters..., iif())
➜ Pour un Storage events trigger, utilisation de triggerBody() uniquement, et pas de iif() côté trigger ; reconstruction ABFSS dans l’activité.

❌ Erreur Delta sur noms de colonnes (ex. Water_(g) …)
➜ Sanitization systématique des colonnes dans le notebook Ingest.

5) Opérations, monitoring & runbook

Monitoring ADF : Trigger runs → Pipeline runs → détails par activité (Inputs/Outputs/Logs).

Vérification post-run :

Tables/chemins : silver/bronze, silver/clean, gold/curated (format Delta).

Contrôles ponctuels :

spark.read.format("delta").load("<abfss...>").show(5)


Conseils prod :

Retries (2–3) et backoff dans les activités Databricks.

Alertes ADF (mail/Teams) sur échec d’activité/pipeline.

Post-traitement : déplacer/supprimer les CSV traités dans raw/processed/ si nécessaire.

6) Résultats (à adapter à tes chiffres)

Pipeline entièrement automatisé (event-driven).

Latence moyenne < N min entre dépôt et arrivée en Gold.

N fichiers/jour traités, M colonnes normalisées, 0 opérations manuelles.
(remplace N/M par tes valeurs réelles)

7) Améliorations possibles (roadmap)

Passer l’accès ADLS à Managed Identity ou Access Connector (Unity Catalog) pour éviter la clé.

Ajouter Auto Loader + checkpoints (ingestion incrémentale robuste).

Qualité de données (Great Expectations) + tests unitaires PySpark.

Partitionnement par date (/ingest_date=YYYY-MM-DD) en Silver/Gold.

Exposition BI (Unity Catalog + tables external/volumes, Power BI).