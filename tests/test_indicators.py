"""
test_indicators.py — Tests unitaires de compute_indicators (pytest).

Les tests utilisent des données synthétiques et ne font aucun appel réseau.
"""

import os
import sys

# On définit une clé API factice AVANT l'import du module, par sécurité, même si
# compute_indicators ne la consomme pas (fetch_history n'est pas testé ici).
os.environ.setdefault("EODHD_API_KEY", "cle-factice-pour-les-tests")

# La racine du projet (parent de tests/) est ajoutée au chemin d'import pour que
# « from suivi_etf import ... » fonctionne quelle que soit la façon de lancer
# pytest (« pytest » ou « python -m pytest », depuis n'importe quel dossier).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from suivi_etf import compute_indicators, FENETRE_MM, FENETRE_VARIATION


def _df_depuis_prix(prix):
    """Construit un DataFrame de cours synthétique indexé par jours ouvrés.

    Args:
        prix (list[float]): suite de cours de clôture.

    Returns:
        pandas.DataFrame: colonne « close » indexée par dates croissantes.
    """
    dates = pd.date_range(end="2026-01-30", periods=len(prix), freq="B")
    return pd.DataFrame({"close": prix}, index=dates)


def test_variation_positive():
    """Une série haussière doit produire une variation positive sur 5 séances."""
    # Tendance régulièrement croissante.
    prix = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
    df = _df_depuis_prix(prix)

    indicateurs = compute_indicators("TEST.US", df)

    assert indicateurs["variation_5j_pct"] is not None
    assert indicateurs["variation_5j_pct"] > 0
    # Une série purement haussière reste au-dessus de sa moyenne mobile.
    assert indicateurs["sous_moyenne_mobile"] is False


def test_detection_sous_moyenne_mobile():
    """Une série baissière doit déclencher l'alerte « sous la moyenne mobile »."""
    # Tendance régulièrement décroissante.
    prix = [110, 108, 106, 104, 102, 100, 98, 96, 94, 92]
    df = _df_depuis_prix(prix)

    indicateurs = compute_indicators("TEST.US", df)

    assert indicateurs["sous_moyenne_mobile"] is True
    # La variation sur 5 séances est cohérente avec la tendance baissière.
    assert indicateurs["variation_5j_pct"] < 0


def test_structure_de_l_instantane():
    """L'instantané doit contenir toutes les clés attendues et le bon symbole."""
    df = _df_depuis_prix([100, 101, 102, 103, 104, 105, 106, 107])

    indicateurs = compute_indicators("ABC.US", df)

    cles_attendues = {
        "symbole",
        "date",
        "dernier_prix",
        "moyenne_mobile",
        "variation_5j_pct",
        "sous_moyenne_mobile",
    }
    assert set(indicateurs.keys()) == cles_attendues
    assert indicateurs["symbole"] == "ABC.US"
    assert indicateurs["dernier_prix"] == 107.0


def test_variation_indisponible_si_historique_court():
    """Avec trop peu de séances, la variation est None mais la MM reste définie."""
    # Strictement moins de FENETRE_VARIATION + 1 points -> variation impossible.
    prix = [100] * FENETRE_VARIATION
    df = _df_depuis_prix(prix)

    indicateurs = compute_indicators("COURT.US", df)

    assert indicateurs["variation_5j_pct"] is None
    assert indicateurs["moyenne_mobile"] == 100.0


def test_constantes_de_configuration():
    """Vérifie des valeurs de configuration cohérentes pour les indicateurs."""
    assert FENETRE_MM > 0
    assert FENETRE_VARIATION > 0
