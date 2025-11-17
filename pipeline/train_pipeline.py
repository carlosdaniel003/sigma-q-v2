# pipeline/train_pipeline.py
# SIGMA-Q V2 — Fase 3
# Pipeline completo: processamento -> treino -> avaliação -> export -> testes rápidos.

import logging
from training.train_classifier import (
    carregar_base,
    carregar_tfidf,
    preparar_features,
    treinar_baseline,
    salvar_modelo,
    registrar_versao
)
from utils.metrics import compute_metrics
from sklearn.model_selection import train_test_split


logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


def testar_modelo(model, X_test, y_test):
    """Testa a integridade e desempenho do modelo antes de liberar."""
    logger.info("🔍 Executando testes internos do modelo...")

    try:
        y_pred = model.predict(X_test)
        metrics = compute_metrics(y_test, y_pred)

        logger.info(f"[TESTE] F1-Macro: {metrics['f1_macro']:.4f}")
        logger.info(f"[TESTE] Acurácia: {metrics['accuracy']:.4f}")

        if metrics["f1_macro"] < 0.40:
            logger.warning("⚠️ ATENÇÃO: F1-Macro abaixo de 0.40! Verificar dados.")
        else:
            logger.info("✔️ Teste de desempenho aprovado.")

        return metrics

    except Exception as e:
        logger.error(f"❌ ERRO durante teste do modelo: {e}")
        raise


def run():
    logger.info("========== INICIANDO PIPELINE COMPLETA — FASE 3 ==========")

    # 1) Carregar dados
    df = carregar_base()

    # 2) Carregar TF-IDF (Fase 2)
    vectorizer = carregar_tfidf()

    # 3) Gerar X e y
    X, y = preparar_features(df, vectorizer)

    # 4) Split estratificado
    logger.info("➡️ Aplicando split estratificado (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )

    # 5) Treinar modelo
    model = treinar_baseline(X_train, y_train)

    # 6) Testes do modelo (obrigatório)
    metrics = testar_modelo(model, X_test, y_test)

    # 7) Salvar modelo + vetorizador
    salvar_modelo(model, vectorizer)

    # 8) Atualizar VERSIONS.md
    registrar_versao(metrics)

    logger.info("========== PIPELINE FINALIZADA COM SUCESSO ==========")


if __name__ == "__main__":
    run()
