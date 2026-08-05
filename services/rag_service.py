"""RAG local persistente con ChromaDB y embeddings deterministas sin descargas."""
from __future__ import annotations

import hashlib
import math
import os
import re
from pathlib import Path
from typing import Iterable

try:
    import chromadb
except ImportError:  # Permite ejecutar la demo antes de instalar ChromaDB
    chromadb = None


class LocalHashEmbeddingFunction:
    """Embedding liviano y reproducible para demo offline.

    Para producción puede sustituirse por OpenAI, Azure OpenAI o un modelo local.
    """

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def __call__(self, input: list[str]) -> list[list[float]]:  # Chroma protocol legacy
        return self.embed_documents(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        """Compatibilidad con ChromaDB/LangChain para indexar documentos."""
        if isinstance(input, str):
            input = [input]
        return [self._embed(str(text)) for text in input]

    def embed_query(self, input):
        """Compatibilidad con ChromaDB 1.x para consultas vectoriales.

        Algunas versiones envían una lista y otras una cadena. Se conserva
        el mismo tipo de salida esperado por cada variante.
        """
        if isinstance(input, str):
            return self._embed(input)
        return [self._embed(str(text)) for text in input]

    def name(self) -> str:
        return "local-hash-embedding-v1"

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-záéíóúñ0-9_-]+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class RAGService:
    def __init__(
        self,
        doc_path: str = "knowledge_base/manuales_planta.txt",
        persist_path: str | None = None,
    ) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self.doc_path = Path(doc_path)
        if not self.doc_path.is_absolute():
            self.doc_path = base_dir / self.doc_path

        chroma_path = persist_path or os.getenv(
            "CHROMA_PATH", str(base_dir / "data" / "chroma")
        )
        Path(chroma_path).mkdir(parents=True, exist_ok=True)
        self.embedding_function = LocalHashEmbeddingFunction()
        self.fallback_file = Path(chroma_path) / "fallback_documents.json"
        self._fallback_documents: list[dict] = []
        if chromadb is not None:
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)
            self.collection = self.chroma_client.get_or_create_collection(
                name="plant_manuals",
                embedding_function=self.embedding_function,
                metadata={"description": "Manuales técnicos y procedimientos de planta"},
            )
        else:
            self.chroma_client = None
            self.collection = None
            if self.fallback_file.exists():
                import json
                self._fallback_documents = json.loads(self.fallback_file.read_text(encoding="utf-8"))
        self._index_documents_if_needed()

    def _extract_chunks(self, content: str) -> Iterable[tuple[str, dict]]:
        pattern = r"(\[[A-Z0-9\-_]+\s*\|\s*RIESGO[^\n]+\n(?:(?!\[[A-Z0-9\-_]+\s*\|)[\s\S])*)"
        matches = re.findall(pattern, content)
        if not matches:
            matches = [chunk for chunk in content.split("\n\n") if "[" in chunk]

        for index, raw_chunk in enumerate(matches):
            chunk = re.sub(r"[-=]{5,}", "", raw_chunk).strip()
            chunk = re.sub(r"\n+MÁQUINA:.*$", "", chunk, flags=re.IGNORECASE).strip()
            if not chunk:
                continue
            header = re.search(r"\[([^|\]]+)\|\s*([^\]]+)\]", chunk)
            machine_id = header.group(1).strip() if header else "general"
            risk_range = header.group(2).strip() if header else "general"
            yield chunk, {
                "source": self.doc_path.name,
                "chunk_index": index,
                "machine_id": machine_id,
                "risk_range": risk_range,
                "document_type": "technical_manual",
            }

    def _index_documents_if_needed(self) -> None:
        if not self.doc_path.exists():
            return
        content = self.doc_path.read_text(encoding="utf-8")
        source_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if self.collection is not None:
            stored = self.collection.get(where={"source_hash": source_hash}, limit=1)
            if stored.get("ids"):
                return
        elif any(item.get("metadata", {}).get("source_hash") == source_hash for item in self._fallback_documents):
            return

        chunks = list(self._extract_chunks(content))
        if not chunks:
            return
        ids = [f"manual-{source_hash[:12]}-{idx}" for idx in range(len(chunks))]
        documents = [item[0] for item in chunks]
        metadatas = [{**item[1], "source_hash": source_hash} for item in chunks]
        if self.collection is not None:
            # Se envían los embeddings explícitamente para no depender de
            # cambios de interfaz entre versiones de ChromaDB.
            vectors = self.embedding_function.embed_documents(documents)
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=vectors,
            )
        else:
            import json
            vectors = self.embedding_function(documents)
            self._fallback_documents.extend(
                {"id": doc_id, "document": doc, "metadata": meta, "embedding": vector}
                for doc_id, doc, meta, vector in zip(ids, documents, metadatas, vectors)
            )
            self.fallback_file.write_text(json.dumps(self._fallback_documents, ensure_ascii=False), encoding="utf-8")


    def _manual_fallback_search(
        self, query: str, machine_id: str | None = None, limit: int = 4
    ) -> list[dict]:
        """Búsqueda local de respaldo si ChromaDB no puede consultar embeddings."""
        if not self.doc_path.exists():
            return []
        query_vector = self.embedding_function._embed(query)
        candidates = []
        content = self.doc_path.read_text(encoding="utf-8")
        for document, metadata in self._extract_chunks(content):
            if machine_id and metadata.get("machine_id") != machine_id:
                continue
            vector = self.embedding_function._embed(document)
            score = sum(a * b for a, b in zip(query_vector, vector))
            candidates.append((score, document, metadata))
        candidates.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "content": document,
                "metadata": metadata,
                "distance": round(1 - score, 6),
            }
            for score, document, metadata in candidates[:limit]
        ]

    @staticmethod
    def _get_risk_label(failure_probability: float) -> str:
        if failure_probability <= 25:
            return "RIESGO 0% A 25%"
        if failure_probability <= 55:
            return "RIESGO 26% A 55%"
        if failure_probability <= 80:
            return "RIESGO 56% A 80%"
        return "RIESGO 81% A 100%"

    def query_context(
        self,
        machine_id: str,
        temperature: float,
        vibration: float,
        status: str,
        failure_probability: float = 0.0,
    ) -> str:
        if self.count() == 0:
            return "No hay manuales técnicos cargados."
        risk_label = self._get_risk_label(failure_probability)
        if self.collection is not None:
            exact = self.collection.get(
                where={"$and": [{"machine_id": machine_id}, {"risk_range": risk_label}]},
                limit=1,
            )
            if exact.get("documents"):
                return exact["documents"][0]
            query_text = (
                f"{machine_id} {risk_label} temperatura {temperature:.1f} "
                f"vibración {vibration:.2f} estado {status} diagnóstico recomendaciones"
            )
            try:
                results = self.collection.query(
                    query_embeddings=[self.embedding_function._embed(query_text)],
                    n_results=3,
                )
                documents = results.get("documents", [[]])[0]
                return documents[0] if documents else "Sin información relevante encontrada."
            except Exception:
                fallback = self._manual_fallback_search(query_text, machine_id=machine_id, limit=1)
                return fallback[0]["content"] if fallback else "Sin información relevante encontrada."
        for item in self._fallback_documents:
            meta = item.get("metadata", {})
            if meta.get("machine_id") == machine_id and meta.get("risk_range") == risk_label:
                return item["document"]
        results = self.search(f"{machine_id} {risk_label} diagnóstico recomendaciones", limit=1)
        return results[0]["content"] if results else "Sin información relevante encontrada."


    def get_machine_manual_info(self, machine_id: str, failure_probability: float) -> dict:
        """Devuelve la identificación del equipo y el fragmento exacto del manual aplicable."""
        if not self.doc_path.exists():
            return {
                "machine_id": machine_id,
                "equipment_name": "Equipo sin identificar",
                "risk_range": self._get_risk_label(failure_probability),
                "source": None,
                "content": "No hay manual técnico cargado para este equipo.",
            }

        content = self.doc_path.read_text(encoding="utf-8")
        name_match = re.search(
            rf"MÁQUINA:\s*{re.escape(machine_id)}\s*\(([^\n\)]+)\)",
            content,
            re.IGNORECASE,
        )
        equipment_name = name_match.group(1).strip() if name_match else "Equipo industrial"
        risk_range = self._get_risk_label(failure_probability)

        # Para el botón de diagnóstico se prioriza una extracción determinista
        # del bloque exacto del manual. Así se evita mezclar recomendaciones
        # de equipos distintos por similitud semántica.
        section_match = re.search(
            rf"\[{re.escape(machine_id)}\s*\|\s*{re.escape(risk_range)}[^\]]*\]\s*"
            rf"(.*?)(?=\n\[{re.escape(machine_id)}\s*\||\n-{{10,}}|\Z)",
            content,
            re.IGNORECASE | re.DOTALL,
        )
        if section_match:
            manual_content = f"[{machine_id} | {risk_range}]\n{section_match.group(1).strip()}"
        else:
            manual_content = self.query_context(
                machine_id=machine_id,
                temperature=0.0,
                vibration=0.0,
                status="",
                failure_probability=failure_probability,
            )
        return {
            "machine_id": machine_id,
            "equipment_name": equipment_name,
            "risk_range": risk_range,
            "source": self.doc_path.name,
            "content": manual_content,
        }

    def search(self, query: str, machine_id: str | None = None, limit: int = 4) -> list[dict]:
        if self.collection is not None:
            where = {"machine_id": machine_id} if machine_id else None
            try:
                result = self.collection.query(
                    query_embeddings=[self.embedding_function._embed(query)],
                    n_results=limit,
                    where=where,
                )
                docs = result.get("documents", [[]])[0]
                metas = result.get("metadatas", [[]])[0]
                distances = result.get("distances", [[]])[0]
                return [{"content": doc, "metadata": meta or {}, "distance": distance} for doc, meta, distance in zip(docs, metas, distances)]
            except Exception:
                return self._manual_fallback_search(query, machine_id=machine_id, limit=limit)
        query_vector = self.embedding_function([query])[0]
        candidates = []
        for item in self._fallback_documents:
            if machine_id and item.get("metadata", {}).get("machine_id") != machine_id:
                continue
            score = sum(a * b for a, b in zip(query_vector, item["embedding"]))
            candidates.append((score, item))
        candidates.sort(key=lambda pair: pair[0], reverse=True)
        return [{"content": item["document"], "metadata": item.get("metadata", {}), "distance": round(1 - score, 6)} for score, item in candidates[:limit]]

    def count(self) -> int:
        return self.collection.count() if self.collection is not None else len(self._fallback_documents)
