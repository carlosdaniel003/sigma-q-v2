# services/classifier_service.py
# SIGMA-Q V2 — Serviço oficial

import joblib
import logging
from config.config import PATH_MODELS, PATH_SPACY_MODEL
from services.text_cleaner import clean_text
from services.text_normalizer import normalizar_texto

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClassifierService:

    def __init__(self):
        self.model = joblib.load(PATH_MODELS / "classifier_v1.joblib")
        self.vectorizer = joblib.load(PATH_MODELS / "tfidf_vectorizer_v1.joblib")

    def preprocess(self, texto: str):
        texto = clean_text(texto)
        texto = normalizar_texto(texto)
        return texto

    def predict(self, texto: str):
        texto_proc = self.preprocess(texto)
        vetor = self.vectorizer.transform([texto_proc])
        pred = self.model.predict(vetor)[0]
        return pred
