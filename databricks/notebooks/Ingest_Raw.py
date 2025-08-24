# Databricks notebook source
display(dbutils.fs.ls("dbfs:/FileStore/shared_uploads/karima.aouada@gmail.com/"))
# test commit

# COMMAND ----------

display(dbutils.fs.ls("dbfs:/FileStore/shared_uploads/"))


# COMMAND ----------

# =========================
# Databricks | Ingest_Raw
# (CSV -> Delta "bronze")
# =========================

# --- Widgets (ADF remplit fullPathAbfss et silverPath) ---
dbutils.widgets.text("fullPathAbfss", "", "Chemin ABFSS du CSV dans raw")
dbutils.widgets.text("silverPath",     "", "Chemin Delta de bronze (dossier)")
# Optionnel: utile en test manuel seulement
dbutils.widgets.text("input_csv",      "", "Chemin CSV local (dbfs:/...)")

# --- Récupération paramètres ---
src = dbutils.widgets.get("fullPathAbfss").strip()
if not src:  # fallback pour run manuel
    src = dbutils.widgets.get("input_csv").strip()

dst = dbutils.widgets.get("silverPath").strip()

if not src:
    raise ValueError("Veuillez renseigner 'fullPathAbfss' (ou 'input_csv' pour test manuel).")
if not dst:
    raise ValueError("Veuillez renseigner 'silverPath' (ex: abfss://silver@.../bronze).")

# --- Lecture CSV ---
from pyspark.sql import functions as F
import re

df = (spark.read
      .format("csv")
      .option("header", "true")
      .option("inferSchema", "true")
      .load(src)
      .withColumn("_src_path", F.lit(src))
      .withColumn("_ingest_ts", F.current_timestamp())
     )

# --- Sanitize des noms de colonnes pour Delta ---
def _sanitize(name: str) -> str:
    # remplace tout caractère non [A-Za-z0-9_] par _
    n = re.sub(r'[^A-Za-z0-9_]', '_', name or "")
    # compresse les "__" et retire les "_" de début/fin
    n = re.sub(r'_+', '_', n).strip('_')
    # ne pas commencer par un chiffre
    if re.match(r'^\d', n):
        n = f"c_{n}"
    return n or "col"

clean_names = [_sanitize(c) for c in df.columns]

# gère les doublons éventuels après nettoyage
seen = {}
final_names = []
for n in clean_names:
    if n not in seen:
        seen[n] = 1
        final_names.append(n)
    else:
        seen[n] += 1
        final_names.append(f"{n}_{seen[n]}")

df = df.toDF(*final_names)

# --- Écriture Delta (append) vers bronze ---
(df.write
   .mode("append")          # on accumule les arrivées
   .format("delta")
   .save(dst))

print(f"✅ Ingest OK : {src} -> {dst}")



# COMMAND ----------

# MAGIC %fs ls /FileStore/raw
# MAGIC

# COMMAND ----------

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Lecture du CSV uploadé
df = spark.read.csv(
    "dbfs:/FileStore/shared_uploads/karima.aouada@gmail.com/fake_edf_data-1.csv",
    header=True,
    inferSchema=True
)

# Vérification rapide
df.show(5)
df.printSchema()

# Écriture en Parquet pour l'étape suivante
df.write.mode("overwrite").parquet("dbfs:/mnt/raw/processed/fake_edf_data")

