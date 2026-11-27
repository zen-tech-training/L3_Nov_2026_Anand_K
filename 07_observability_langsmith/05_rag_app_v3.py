# pip install -U langchain langchain-openai langchain-community faiss-cpu pypdf python-dotenv langsmith

import os
from dotenv import load_dotenv

from langsmith import traceable

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

KB_PATH = "knowledge_base.txt"  # <- change to your file

# ----------------- helpers (not traced individually) -----------------
@traceable(name="load_kb")
def load_kb(path: str):
    loader = TextLoader(path)
    return loader.load()  # list[Document]

@traceable(name="split_documents")
def split_documents(docs, chunk_size=100, chunk_overlap=20):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    return splitter.split_documents(docs)

@traceable(name="build_vectorstore")
def build_vectorstore(splits):
    emb = OllamaEmbeddings(model="nomic-embed-text")
    return FAISS.from_documents(splits, emb)

# ----------------- parent setup function (traced) -----------------
@traceable(name="setup_pipeline", tags=["setup"], metadata={"pipeline_id": "my_first_rag_pipeline"})
def setup_pipeline(kb_path: str, chunk_size=100, chunk_overlap=20):
    # ✅ These three steps are “clubbed” under this parent function
    docs = load_kb(kb_path)
    splits = split_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    vs = build_vectorstore(splits)
    return vs

# ----------------- model, prompt, and run -----------------
llm = ChatOllama(model="llama3.2", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer ONLY from the provided context. If not found, say you don't know."),
    ("human", "Question: {question}\n\nContext:\n{context}")
])

def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)

# ----------------- one top-level (root) run -----------------
@traceable(name="kb_rag_full_run")
def setup_pipeline_and_query(kb_path: str, question: str):
    # Parent setup run (child of root)
    vectorstore = setup_pipeline(kb_path, chunk_size=100, chunk_overlap=20)

    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})

    parallel = RunnableParallel({
        "context": retriever | RunnableLambda(format_docs),
        "question": RunnablePassthrough(),
    })

    chain = parallel | prompt | llm | StrOutputParser()

    # This LangChain run stays under the same root (since we're inside this traced function)
    lc_config = {"run_name": "kb_rag_query"}
    return chain.invoke(question, config=lc_config)

# ----------------- CLI -----------------
if __name__ == "__main__":
    print("KB RAG ready. Ask a question (or Ctrl+C to exit).")
    q = input("\nQ: ").strip()
    ans = setup_pipeline_and_query(KB_PATH, q)
    print("\nA:", ans)
