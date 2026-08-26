from pathlib import Path
import shutil
from services.rag_service import RAGService

def main():
    print("Reconstruyendo la base de datos vectorial ChromaDB...")
    
    # 1. Eliminar carpeta física para limpiar la caché vectorial
    chroma_dir = Path("data/chroma_db")
    if chroma_dir.exists():
        shutil.rmtree(chroma_dir)
        print("🗑️ Carpeta data/chroma_db eliminada.")

    # 2. Inicializar RAGService (forzará la lectura de data/manuals/*.txt)
    rag = RAGService()
    
    total = rag.count()
    print(f"\n✅ Proceso finalizado. Total de bloques indexados en ChromaDB: {total}\n")

    # 3. Mostrar resumen de lo que quedó guardado
    data = rag.collection.get()
    metas = data.get("metadatas", [])
    docs = data.get("documents", [])

    print("==================================================")
    print("      RESUMEN DE DOCUMENTOS INDEXADOS            ")
    print("==================================================")
    for i, meta in enumerate(metas):
        m_id = meta.get("machine_id", "N/A")
        src = meta.get("source", "N/A")
        snippet = docs[i][:100].replace("\n", " ") if i < len(docs) else ""
        print(f"[{i+1}] Machine ID: {m_id} | Fuente: {src}")
        print(f"    Texto: {snippet}...\n")

if __name__ == "__main__":
    main()