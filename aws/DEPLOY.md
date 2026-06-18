# Déploiement (Phase 2) avec AWS SAM

Ce dossier contient l'infrastructure serverless du pipeline : une fonction
Lambda déclenchée chaque semaine par EventBridge, qui lit et écrit le fichier de
suivi et le résumé sur S3.

## Prérequis

- **AWS CLI** installé et configuré (`aws configure`).
- **AWS SAM CLI** installé.
- **Docker** (recommandé pour `sam build --use-container`, afin de compiler
  pandas pour l'environnement Lambda).
- L'**accès au modèle Claude Haiku activé** dans la console Amazon Bedrock de la
  région de déploiement.
- Une **clé API EODHD**.

## Packaging

Le template (`aws/template.yaml`) définit `CodeUri: ../`, c'est-à-dire la
**racine du projet**. Le module partagé `suivi_etf.py` est ainsi packagé avec le
handler et reste importable (`Handler: aws.lambda_function.lambda_handler`). Les
dépendances sont installées depuis le `requirements.txt` de la racine.

## Étapes

Depuis le dossier `aws/` :

```bash
# 1. Construire l'artefact de déploiement.
#    --use-container compile les dépendances natives (pandas) pour Lambda.
sam build --use-container

# 2. Déployer en mode guidé (première fois).
sam deploy --guided
```

Lors du `sam deploy --guided`, renseignez notamment :

- **Stack Name** : ex. `suivi-etf`.
- **AWS Region** : la région où Bedrock et le modèle Haiku sont disponibles.
- **Parameter EodhdApiKey** : votre clé API EODHD (paramètre `NoEcho`, non
  versionné, jamais affiché en clair par CloudFormation).
- **Parameter ModeleBedrock** : laissez la valeur par défaut ou indiquez
  l'identifiant exact relevé dans la console Bedrock de votre région.
- **Parameter SymbolesEtf** : liste de symboles séparés par des virgules.
- Confirmez la création de rôles IAM (`CAPABILITY_IAM`).

Les déploiements suivants peuvent se faire simplement avec :

```bash
sam deploy
```

(les paramètres sont relus depuis `samconfig.toml` généré au premier déploiement ;
la clé API étant `NoEcho`, il peut être nécessaire de la re-fournir).

## Vérifier / tester

```bash
# Invocation manuelle de la fonction (sans attendre le lundi).
aws lambda invoke --function-name suivi-etf-hebdomadaire reponse.json
cat reponse.json

# Récupérer le résumé produit (le nom du bucket figure dans les Outputs du stack).
aws s3 cp s3://<NOM_DU_BUCKET>/resume-hebdomadaire.txt -
```

Le nom du bucket et de la fonction sont disponibles dans les **Outputs** du
stack (console CloudFormation ou `sam list stack-outputs`).

## Planification

La règle EventBridge déclenche la fonction **tous les lundis à 08h00 UTC**
(`cron(0 8 ? * MON *)`). Ajustez l'expression `Schedule` dans `template.yaml`
pour changer l'horaire ou le fuseau de référence (l'expression est en UTC).

## Suppression

```bash
sam delete
```

> Remarque : si le bucket S3 contient des objets, videz-le avant la suppression
> du stack (`aws s3 rm s3://<NOM_DU_BUCKET> --recursive`).
