import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_groq import ChatGroq
# from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from src.ai.tools import get_all_tools
from src.ai.prompts import get_agent_prompt

load_dotenv()

def get_llm():
    """
    Pilih LLM berdasarkan API key yang tersedia di .env.
    """
    if os.getenv("GROQ_API_KEY"):
        return ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.2,
            api_key=os.getenv("GROQ_API_KEY")
        )
    # elif os.getenv("OPENAI_API_KEY"):
    #     return ChatOpenAI(
    #         model="gpt-4o-mini",
    #         temperature=0.2,
    #         api_key=os.getenv("OPENAI_API_KEY")
    #     )
    else:
        raise ValueError(
            "Tidak ada API key ditemukan! "
        )

def create_saku_agent():
    """Membuat LangChain agent dengan semua tools SAKU."""
    llm = get_llm()
    tools = get_all_tools()
    prompt = get_agent_prompt()

    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,           # Tampilkan reasoning agent di terminal
        handle_parsing_errors=True,
        max_iterations=5        # Cegah infinite loop
    )

def format_chat_history(messages: list[dict]) -> list:
    """
    Konversi format chat history dari Streamlit ke format LangChain.
    
    Args:
        messages: List pesan dari st.session_state.messages
                  format: [{"role": "user/assistant", "content": "..."}]
    """
    history = []
    for msg in messages:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history.append(AIMessage(content=msg["content"]))
    return history

def run_agent(user_input: str, chat_history: list[dict]) -> str:
    """
    Jalankan agent dengan input user dan riwayat chat.
    
    Args:
        user_input: Pesan terbaru dari user
        chat_history: Riwayat percakapan sebelumnya
        
    Returns:
        String respons dari agent
    """
    try:
        agent = create_saku_agent()
        history = format_chat_history(chat_history)

        result = agent.invoke({
            "input": user_input,
            "chat_history": history
        })

        return result.get("output", "Maaf, aku tidak bisa memproses permintaan itu.")

    except Exception as e:
        return f"❌ Terjadi error: {str(e)}"