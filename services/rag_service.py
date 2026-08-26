"""RAG local persistente con ChromaDB para manuales técnicos de planta.
Servicio de embeddings e indexación vectorial.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import chromadb

# BASE_DIR es la raíz del proyecto (predictive_IA_zyma)
BASE_DIR = Path(__file__).resolve().parent.parent

# Ruta exacta apuntando a knowledge_base en la raíz
KNOWLEDGE_FILE = BASE_DIR / "knowledge_base" / "manuales_planta.txt"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"


class RAGService:
    def __init__(self):
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = self.client.get_or_create_collection(
            name="plant_manuals",
            metadata={"hnsw:space": "cosine"}
        )
        self._initialize_documents()

    def _normalize_machine_id(self, machine_id: str) -> str:
        match = re.search(r"\d+", machine_id)
        if match:
            return f"Machine-{int(match.group()):03d}"
        return machine_id

    def _get_risk_range(self, failure_probability: float) -> str:
        if failure_probability <= 40:
            return "RIESGO 0% A 40%"
        elif failure_probability <= 80:
            return "RIESGO 41% A 80%"
        else:
            return "RIESGO 81% A 100%"

    def _initialize_documents(self):
        if self.collection.count() > 0:
            return

        documents = []
        metadatas = []
        ids = []

        if KNOWLEDGE_FILE.exists():
            try:
                with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                    content = f.read()

                # Dividir el archivo unificado por la cabecera de cada bloque [Machine-
                blocks = re.split(r"\n(?=\[Machine-)", content)
                
                for idx, block in enumerate(blocks):
                    clean_block = block.strip()
                    if clean_block:
                        machine_match = re.search(r"Machine[-_\s]*\d+", clean_block, re.IGNORECASE)
                        machine_id = self._normalize_machine_id(machine_match.group()) if machine_match else "General"

                        documents.append(clean_block)
                        metadatas.append({
                            "source": KNOWLEDGE_FILE.name,
                            "machine_id": machine_id,
                            "block_index": idx
                        })
                        ids.append(f"manuales_planta_{idx}")

            except Exception as e:
                print(f"Error cargando archivo {KNOWLEDGE_FILE}: {e}")
        else:
            print(f"⚠️ No se encontró el archivo de manuales en: {KNOWLEDGE_FILE}")

        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    def count(self) -> int:
        return self.collection.count()

    def search(self, query: str, machine_id: Optional[str] = None, limit: int = 3) -> List[Dict]:
        where_clause = None
        if machine_id:
            normalized_id = self._normalize_machine_id(machine_id)
            where_clause = {"machine_id": normalized_id}

        results = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_clause
        )

        formatted_results = []
        if results and results.get("documents"):
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else []
            distances = results["distances"][0] if results.get("distances") else []

            for i in range(len(docs)):
                formatted_results.append({
                    "content": docs[i],
                    "metadata": metas[i] if i < len(metas) else {},
                    "distance": distances[i] if i < len(distances) else None
                })

        return formatted_results

    def get_machine_manual_info(self, machine_id: str, failure_probability: float) -> Dict:
        normalized_machine_id = self._normalize_machine_id(machine_id)
        risk_range = self._get_risk_range(failure_probability)

        results = self.collection.get(where={"machine_id": normalized_machine_id})
        
        selected_content = None
        if results and results.get("documents"):
            for doc in results["documents"]:
                if risk_range.lower() in doc.lower():
                    selected_content = doc
                    break

            if not selected_content and results["documents"]:
                selected_content = results["documents"][0]

        if not selected_content:
            query = f"{normalized_machine_id} {risk_range}"
            search_res = self.search(query, machine_id=normalized_machine_id, limit=1)
            if search_res:
                selected_content = search_res[0]["content"]
            else:
                selected_content = "No hay información disponible en el manual SOP para esta máquina."

        return {
            "machine_id": normalized_machine_id,
            "equipment_name": f"Equipo {normalized_machine_id}",
            "risk_range": risk_range,
            "content": selected_content
        }