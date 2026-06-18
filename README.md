# Suivi hebdomadaire d'un panier d'ETF

Pipeline d'automatisation qui récupère les prix d'un panier d'ETF, met à jour
un fichier Excel de suivi, laisse le classeur recalculer ses indicateurs et son
classement, puis génère une analyse en langage naturel via Claude (Amazon
Bedrock).

## Fonctionnalités

- Récupération de l'historique de fin de journée via l'API **EODHD**.
- Structuration et préparation des prix avec **pandas** avant mise à jour du
  classeur de suivi.
- Mise à jour du fichier **Excel** (`openpyxl`) avec les nouveaux prix, puis
  recalcul dans Excel des indicateurs, scores et classements du panier d'ETF.
- Analyse **factuelle et neutre** via **Claude** (Amazon Bedrock, API Converse)
  pour expliquer les mouvements de prix et commenter le classement obtenu.
- **Phase 2 serverless** : fonction **AWS Lambda** déclenchée chaque semaine par
  **EventBridge**, qui lit/écrit le suivi et le résumé sur **S3**.
- **Tests unitaires** des indicateurs avec `pytest`.

## Stack technique

- Python 3.10+
- pandas, requests, openpyxl
- boto3 + Amazon Bedrock (Claude Haiku via l'API Converse)
- AWS Lambda, Amazon EventBridge, Amazon S3
- AWS SAM (infrastructure as code)
- pytest

## Prérequis

- Python 3.10 ou supérieur.
- Une clé API **EODHD** (https://eodhd.com).
- Un compte AWS avec l'**accès au modèle Claude Haiku activé** dans la console
  Amazon Bedrock de votre région.
- Pour la Phase 2 uniquement : **AWS CLI** et **AWS SAM CLI** installés.

## Installation

```bash
# Cloner le dépôt puis, à la racine du projet :
python -m venv .venv
source .venv/bin/activate        # sous Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Aucune clé ni secret n'est écrit en dur dans le code.

```bash
# Clé API EODHD (obligatoire), lue dans la variable d'environnement.
export EODHD_API_KEY="votre_cle_eodhd"

# Identifiants et région AWS (pour le résumé Bedrock).
aws configure
```

Variables d'environnement optionnelles (valeurs par défaut entre parenthèses) :

- `SYMBOLES_ETF` — symboles séparés par des virgules (`SPY.US,QQQ.US,VTI.US`).
- `MODELE_BEDROCK` — identifiant du modèle Claude Haiku
  (`anthropic.claude-3-5-haiku-20241022-v1:0`). **À vérifier dans la console
  Bedrock selon la région** (un préfixe de profil d'inférence peut être requis).
- `AWS_REGION` — région AWS (`eu-west-1` par défaut en local).
- `CHEMIN_EXCEL` — chemin du fichier Excel généré (`suivi-etf.xlsx`).

## Utilisation

```bash
python suivi_etf.py
```

Le script récupère les prix, les prépare avec pandas, met à jour le fichier
Excel, laisse le classeur recalculer les indicateurs et le classement, puis
affiche l'analyse de Claude sur les mouvements de la semaine.

## Structure

```
suivi-etf/
├── README.md
├── requirements.txt
├── .gitignore
├── suivi_etf.py            # Phase 1 : script local complet
├── aws/
│   ├── lambda_function.py  # Phase 2 : handler Lambda
│   ├── template.yaml       # infra SAM : Lambda + EventBridge + S3 + IAM
│   └── DEPLOY.md           # instructions de déploiement
└── tests/
    └── test_indicators.py  # tests unitaires des traitements automatisés
```

## Tests

Depuis la racine du projet :

```bash
python -m pytest
```

Les tests valident les traitements automatisés sur des données synthétiques et
ne réalisent aucun appel réseau.

## Feuille de route

État réel du projet :

- [x] Récupération des prix via l'API EODHD (`fetch_history`)
- [x] Préparation des prix avec pandas avant écriture dans le classeur
- [x] Mise à jour du fichier Excel avec les prix récupérés (`write_excel`)
- [x] Recalcul des indicateurs, scores et classements directement dans Excel
- [x] Résumé factuel et neutre via Claude / Bedrock Converse
      (`summarize_with_claude`)
- [x] Orchestration locale (`main`)
- [x] Tests unitaires des traitements automatisés (pytest)
- [x] Infrastructure serverless AWS SAM (Lambda + EventBridge + S3 + IAM)
- [x] Handler Lambda implémenté : lecture/écriture du suivi et du résumé sur S3
- [ ] Notification du résumé hebdomadaire (e-mail / SNS)
- [ ] Tableau de bord ou graphiques d'historique
- [ ] Gestion multi-devises et conversion
- [ ] Tests d'intégration de `fetch_history` et des accès S3 (avec mocks)
- [ ] Stockage de la clé API via AWS Secrets Manager / SSM Parameter Store
