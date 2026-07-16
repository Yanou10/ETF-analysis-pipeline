"""
lambda_function.py — Handler AWS Lambda (Phase 2) du pipeline de suivi d'ETF.

À chaque déclenchement (planifié par EventBridge, voir template.yaml) :
  1. Télécharge le fichier Excel de suivi depuis S3 (s'il existe déjà).
  2. Recalcule les indicateurs de chaque ETF (réutilise suivi_etf.py).
  3. Réécrit le fichier Excel avec une nouvelle feuille datée et le ré-upload sur S3.
  4. Génère un résumé factuel et neutre via Claude (Bedrock, API Converse).
  5. Stocke le résumé sur S3.

La logique métier (récupération, calcul, écriture Excel, résumé) est importée
depuis suivi_etf.py, qui est packagé à la racine du projet (voir DEPLOY.md).
"""

import os
import sys

# La racine du projet (parent du dossier aws/) est ajoutée au chemin d'import
# afin que « import suivi_etf » fonctionne quel que soit le mode de packaging.
RACINE_PROJET = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RACINE_PROJET not in sys.path:
    sys.path.insert(0, RACINE_PROJET)

import boto3
from botocore.exceptions import ClientError

import suivi_etf  # logique partagée avec la Phase 1


# Codes d'erreur S3 signalant un objet absent (première exécution).
CODES_ABSENT = {"404", "NoSuchKey", "NotFound"}


def lambda_handler(event, context):
    """Point d'entrée Lambda.

    Variables d'environnement attendues (définies par le template SAM) :
      - BUCKET_SUIVI : nom du bucket S3 de stockage.
      - CLE_EXCEL    : clé S3 du fichier Excel (défaut « suivi-etf.xlsx »).
      - CLE_RESUME   : clé S3 du fichier résumé (défaut « resume-hebdomadaire.txt »).
      - MODELE_BEDROCK, SYMBOLES_ETF : utilisées par suivi_etf.

    Returns:
        dict: statut HTTP et métadonnées de l'exécution.
    """
    s3 = boto3.client("s3")
    bucket = os.environ["BUCKET_SUIVI"]
    cle_excel = os.environ.get("CLE_EXCEL", "suivi-etf.xlsx")
    cle_resume = os.environ.get("CLE_RESUME", "resume-hebdomadaire.txt")

    # /tmp est le seul répertoire inscriptible dans l'environnement Lambda.
    chemin_local = "/tmp/suivi-etf.xlsx"

    # 1. Télécharge le fichier de suivi existant (ignore l'absence au 1er run).
    try:
        s3.download_file(bucket, cle_excel, chemin_local)
        print(f"Fichier existant téléchargé depuis s3://{bucket}/{cle_excel}.")
    except ClientError as erreur:
        code = erreur.response.get("Error", {}).get("Code", "")
        if code in CODES_ABSENT:
            print("Aucun fichier de suivi existant : première exécution.")
            if os.path.exists(chemin_local):
                os.remove(chemin_local)
        else:
            raise

    # 2. Recalcule les indicateurs pour chaque ETF (logique partagée).
    snapshot = []
    for symbole in suivi_etf.SYMBOLES_ETF:
        df = suivi_etf.fetch_history(symbole)
        snapshot.append(suivi_etf.compute_indicators(symbole, df))

    # 3. Réécrit le fichier Excel (ajoute une feuille datée) puis ré-upload sur S3.
    suivi_etf.write_excel(snapshot, chemin_local)
    s3.upload_file(chemin_local, bucket, cle_excel)
    print(f"Fichier de suivi mis à jour : s3://{bucket}/{cle_excel}.")

    # 4. Génère le résumé factuel via Claude (Bedrock).
    resume = suivi_etf.summarize_with_claude(snapshot)

    # 5. Stocke le résumé sur S3.
    s3.put_object(
        Bucket=bucket,
        Key=cle_resume,
        Body=resume.encode("utf-8"),
        ContentType="text/plain; charset=utf-8",
    )
    print(f"Résumé stocké : s3://{bucket}/{cle_resume}.")

    return {
        "statusCode": 200,
        "symboles_traites": len(snapshot),
        "cle_excel": cle_excel,
        "cle_resume": cle_resume,
    }
