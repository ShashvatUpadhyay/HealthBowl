import os
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

# --- STEP 1: SECURE KEY LOADING ---
# This finds the .env file in the same folder as this script
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / '.env')

# Verify key loading (Only prints to your terminal)
if not os.getenv("GROQ_API_KEY"):
    print("❌ ERROR: GROQ_API_KEY not found in .env file.")
    print(f"Check if .env exists in: {BASE_DIR}")
else:
    print("✅ Cloud Connection Secure (Key Loaded)")

# --- STEP 2: DJANGO DATABASE CONNECTION ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HLIFE.settings')
django.setup()

from store.models import Product

def build_local_health_bowl_bot():
    print("🚀 Booting Health Bowl AI (Llama 3.1 via Groq)...")
    
    # --- STEP 3: LIVE MENU DATA ---
    products = Product.objects.all()
    live_menu_text = "Health Bowl Menu & Pricing:\n"
    for item in products:
        live_menu_text += f"- {item.name}: ₹{item.price}.\n"
    
    live_menu_text += "\nPolicy: No returns on fresh food. Contact support for delivery issues."
    docs = [Document(page_content=live_menu_text)]

    # --- STEP 4: LOCAL SEARCH ENGINE (FAISS) ---
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(docs)

    # Lightweight local embedding librarian
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(splits, embeddings)
    retriever = vectorstore.as_retriever()

    # --- STEP 5: PERSONALITY & PROMPT ---
    system_prompt = (
        "You are a friendly, concise assistant for 'Health Bowl'. "
        "Use the provided context to answer. "
        "Rules: Max 15 words. If greeted, be social. No fake info."
        "\n\nContext: {context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # --- STEP 6: GROQ CLOUD BRAIN ---
    # Security: No hardcoded key!
    llm = ChatGroq(
        temperature=0,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant"
    )
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # The Chain
    rag_chain = (
        {"context": retriever | format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain

# --- TERMINAL TEST ---
if __name__ == "__main__":
    try:
        bot = build_local_health_bowl_bot()
        print("\n--- Cloud Test ---")
        print(f"Bot: {bot.invoke('hii')}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")