# model_mapping.py
# Mapa oficial de equivalências entre MODELO (defeitos) → MODELO (produção)

MAPEAMENTO_MODELOS = {
    # --------- TORRES DE SOM / TW ---------
    "ALTO FALANTE 10POL TW": "TORRE DE SOM AWS-T2W-02 BIVOLT BLUETOOTH",

    # --------- CAIXAS CM ---------
    "ALTO FALANTE 8 3 OHMS CM-250": "CAIXA AMPLIFICADA CM-250 BIVOLT",
    "CAIXA AMPLIFICADA CM-400 BIVOLT": "ALTO FALANTE 12POL. 6 OHMS CM-400/CM-550",
    "CAIXA AMPLIFICADA CM-550 BIVOLT": "ALTO FALANTE 12POL. 6 OHMS CM-400/CM-550",

    # --------- MICROONDAS ---------
    "MICRO-ONDAS MO-01-21-E 127V/60HZ": "MICRO-ONDAS MO-01-21-E 220V/60HZ",
    "MICROONDAS MO-01-21-W": "MICRO-ONDAS MO-01-21-W 220V/60HZ",
}

def aplicar_mapeamento(df):
    """Aplica o mapeamento de modelos na coluna MODELO."""
    df["MODELO"] = df["MODELO"].replace(MAPEAMENTO_MODELOS)
    return df
