# BLOCK 3 — services/classifier_service.py
import json
from pathlib import Path
import joblib
from services.text_normalizer import normalizar_texto

PATH_MODELS = Path("models")
PATH_LEXICON = PATH_MODELS / "lexicon.json"
PATH_MODEL = PATH_MODELS / "classifier_v1.joblib"
PATH_VECTORIZER = PATH_MODELS / "tfidf_vectorizer_v1.joblib"

class ClassifierService:

    def __init__(self):
        # carregar lexicon
        self.lexicon = {}
        if PATH_LEXICON.exists():
            with open(PATH_LEXICON, "r", encoding="utf-8") as f:
                self.lexicon = json.load(f)

        # carregar modelo (fallback)
        self.vectorizer = None
        self.model = None

        if PATH_VECTORIZER.exists():
            self.vectorizer = joblib.load(PATH_VECTORIZER)

        if PATH_MODEL.exists():
            self.model = joblib.load(PATH_MODEL)

    def predict(self, raw_text: str) -> str:
        """
        1) Normaliza o texto
        2) Procura no lexicon — prioridade absoluta
        3) Caso não encontre → usa modelo (fallback)
        """
        if not raw_text:
            return ""

        key = normalizar_texto(raw_text)

        # PRIORIDADE MÁXIMA → se está no lexicon, retorna sempre o valor real
        if key in self.lexicon:
            return self.lexicon[key]

        # fallback com o modelo (às vezes não será necessário)
        if self.model and self.vectorizer:
            x = self.vectorizer.transform([key]).toarray()
            pred = self.model.predict(x)[0]
            return str(pred)

        return ""
