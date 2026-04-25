
from typing import List
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnablePassthrough,
    RunnableLambda,
)
from langchain_core.messages import HumanMessage, AIMessage
from config import Config


class RAGChain:
    """LCEL RAG chain. Compatible with langchain 1.2.15."""

    def __init__(self, embeddings_manager, memory_manager):
        self.em = embeddings_manager
        self.mm = memory_manager
        self._llm = None
        self._chain = None
        self._retriever = None
        self._initialize()

    def _initialize(self) -> None:
        key = Config.GOOGLE_API_KEY
        if not key or key == "your_google_api_key_here":
            return
        try:
            self._llm = ChatGoogleGenerativeAI(
                model=Config.MODEL_NAME,
                google_api_key=key,
                temperature=Config.TEMPERATURE,
                max_output_tokens=Config.MAX_OUTPUT_TOKENS,
                convert_system_message_to_human=True,
            )
            self._retriever = self.em.get_retriever()
            if self._retriever:
                self._chain = self._build_chain()
                logger.info("RAG chain ready!")
        except Exception as e:
            logger.error(f"RAG init failed: {e}")

    def _build_chain(self):
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a personal knowledge assistant.\n"
                "Answer ONLY using the context below.\n"
                "Always cite: [filename, Page X]\n"
                "If not found say: "
                "I could not find this in your documents.\n\n"
                "Context:\n{context}"
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ])

        def retrieve(inputs: dict) -> dict:
            docs = self._retriever.invoke(
                inputs["question"]
            )
            parts = []
            for d in docs:
                fn = d.metadata.get(
                    "filename",
                    d.metadata.get("source", "Unknown")
                )
                pg = d.metadata.get("page", "N/A")
                parts.append(
                    f"[{fn} Page {pg}]\n{d.page_content}"
                )
            inputs["context"] = "\n\n".join(parts)
            inputs["_docs"] = docs
            return inputs

        chain = (
            RunnableLambda(retrieve)
            | RunnablePassthrough.assign(
                answer=(
                    RunnableLambda(
                        lambda x: {
                            "context": x["context"],
                            "chat_history": x.get(
                                "chat_history", []
                            ),
                            "question": x["question"],
                        }
                    )
                    | prompt
                    | self._llm
                    | StrOutputParser()
                )
            )
        )
        return chain

    def rebuild_chain(self) -> None:
        self._retriever = self.em.get_retriever()
        if self._retriever and self._llm:
            self._chain = self._build_chain()
            logger.info("Chain rebuilt!")

    def reinitialize(self) -> None:
        self._llm = None
        self._chain = None
        self._retriever = None
        self._initialize()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
    )
    def get_response(self, question: str) -> dict:
        if not question or not question.strip():
            return {
                "answer": "Please enter a question.",
                "sources": [],
                "error": True,
            }
        if self._chain is None:
            return {
                "answer": (
                    "Please upload documents first!"
                ),
                "sources": [],
                "error": True,
            }
        try:
            history = []
            for m in self.mm.get_history_messages():
                if isinstance(m, HumanMessage):
                    history.append(
                        HumanMessage(content=m.content)
                    )
                elif isinstance(m, AIMessage):
                    history.append(
                        AIMessage(content=m.content)
                    )
            history = history[-10:]
            result = self._chain.invoke({
                "question": question,
                "chat_history": history,
            })
            answer = result.get("answer", "No answer")
            docs = result.get("_docs", [])
            return {
                "answer": answer,
                "sources": self._fmt(docs),
                "error": False,
            }
        except Exception as e:
            logger.error(f"Response error: {e}")
            err = str(e)
            if "API Key" in err or "INVALID_ARGUMENT" in err:
                return {
                    "answer": (
                        "API key error. "
                        "Re-enter your key in the sidebar."
                    ),
                    "sources": [],
                    "error": True,
                }
            return {
                "answer": f"Error: {err[:200]}",
                "sources": [],
                "error": True,
            }

    def _fmt(self, docs: List[Document]) -> List[dict]:
        seen, out = set(), []
        for d in docs:
            m = d.metadata
            fn = m.get("filename", m.get("source", "?"))
            pg = m.get("page", "N/A")
            k = f"{fn}_{pg}"
            if k not in seen:
                seen.add(k)
                out.append({
                    "filename": fn,
                    "page": pg,
                    "preview": d.page_content[:200] + "...",
                    "file_type": m.get("file_type", "doc"),
                })
        return out
