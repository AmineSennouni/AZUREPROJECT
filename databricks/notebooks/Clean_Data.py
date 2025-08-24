# Databricks notebook source
# =========================
# Databricks | Clean_Data
# (bronze Delta -> silver/clean Delta)
# =========================

# --- Widgets ---
dbutils.widgets.text("silverPath", "", "Chemin Delta de bronze (dossier)")
silver = dbutils.widgets.get("silverPath").strip()
if not silver:
    raise ValueError("Veuillez renseigner 'silverPath' (ex: abfss://silver@.../bronze).")

clean_path = f"{silver}/../clean"  # écrit dans .../silver/clean

from pyspark.sql import functions as F, types as T
from pyspark.sql.window import Window

# --- Lecture bronze ---
bronze = spark.read.format("delta").load(silver)

df = bronze

# --- 1) Nettoyages simples ---
# a) trim et vides -> null (uniquement sur colonnes string)
for c, t in df.dtypes:
    if t == "string":
        df = (df
              .withColumn(c, F.trim(F.col(c)))
              .withColumn(c, F.when(F.col(c) == "", None).otherwise(F.col(c))))

# b) colonnes techniques cohérentes (si Ingest les a écrites)
#    -> rien à faire, on les garde: _src_path, _ingest_ts

# --- 2) (Optionnel) casts "best effort" si ces colonnes existent ---
casts = {
    "Energ_Kcal": T.DoubleType(),
    "Water_g":    T.DoubleType(),
    "NDB_No":     T.LongType(),
}
for c, tp in casts.items():
    if c in df.columns:
        df = df.withColumn(c, F.col(c).cast(tp))

# --- 3) Dédoublonnage (au choix) ---
# Si une clé naturelle existe, on garde la dernière occurrence par _ingest_ts
key_candidates = [c for c in ["id", "ID", "Id", "NDB_No", "ndb_no"] if c in df.columns]
if key_candidates and "_ingest_ts" in df.columns:
    w = Window.partitionBy(*key_candidates).orderBy(F.col("_ingest_ts").desc())
    df = (df.withColumn("__rn", F.row_number().over(w))
            .filter(F.col("__rn") == 1).drop("__rn"))
else:
    # sinon, on supprime juste les doublons exacts (toutes colonnes)
    df = df.dropDuplicates()

# --- 4) Écriture Delta (overwrite) ---
(df.write
   .mode("overwrite")
   .option("overwriteSchema", "true")
   .format("delta")
   .save(clean_path))

print(f"✅ Clean OK : {silver} -> {clean_path}")

