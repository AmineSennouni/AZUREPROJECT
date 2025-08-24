# Databricks notebook source
# ================================
# Databricks | Transform_curated
# (silver/clean Delta -> gold/curated Delta)
# ================================

# --- Widgets ---
dbutils.widgets.text("silverPath", "", "Chemin Delta de bronze (dossier)")
dbutils.widgets.text("goldPath",   "", "Chemin Delta de curated (dossier)")

silver = dbutils.widgets.get("silverPath").strip()
gold   = dbutils.widgets.get("goldPath").strip()
if not silver or not gold:
    raise ValueError("Veuillez renseigner 'silverPath' ET 'goldPath'.")

clean_path = f"{silver}/../clean"

from pyspark.sql import functions as F

# --- Lecture clean ---
clean = spark.read.format("delta").load(clean_path)

# --- Logique métier simple & sûre ---
# Cas 1 : si colonnes calories dispo -> un exemple de vue "top 20"
if {"Energ_Kcal", "Shrt_Desc"}.issubset(set(clean.columns)):
    curated = (clean
               .select("Shrt_Desc", "Energ_Kcal")
               .orderBy(F.col("Energ_Kcal").desc_nulls_last())
               .limit(20))
# Cas 2 : sinon, on publie clean tel quel (pass-through)
else:
    curated = clean

# --- Écriture Delta (overwrite) ---
(curated.write
    .mode("overwrite")
    .format("delta")
    .save(gold))

print(f"✅ Curated OK : {clean_path} -> {gold}")
