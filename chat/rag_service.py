# chat/rag_service.py (معماری نهایی و استاندارد RAG)
import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Vectara
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential

load_dotenv()

vectorstore = None
llm_client = None

# اتصال به سرویس‌ها یک بار در ابتدای برنامه
try:
    print("Connecting to Vectara and Azure AI...")
    # اتصال به Vectara
    vectorstore = Vectara(
        vectara_customer_id=os.environ.get("VECTARA_CUSTOMER_ID"),
        vectara_corpus_id=os.environ.get("VECTARA_CORPUS_ID"),
        vectara_api_key=os.environ.get("VECTARA_API_KEY")
    )
    # اتصال به Azure AI
    llm_client = ChatCompletionsClient(
        endpoint=os.environ.get("AZURE_AI_ENDPOINT"),
        credential=AzureKeyCredential(os.environ.get("AZURE_AI_TOKEN")),
    )
    print("Connections successful.")
except Exception as e:
    vectorstore = None
    llm_client = None
    print(f"Failed to initialize services: {e}")

def get_rag_response(user_query: str, chat_history: list) -> str:
    """
    پاسخ را با استفاده از معماری کلاسیک RAG (جستجو و سپس تولید) تولید می‌کند.
    """
    if not vectorstore or not llm_client:
        return "متاسفانه سرویس دانش یا مدل هوش مصنوعی در حال حاضر در دسترس نیست."

    try:
        # ۱. فقط جستجوی ساده برای پیدا کردن اسناد مرتبط از Vectara
        found_docs = vectorstore.similarity_search(query=user_query, k=5)

        # اگر هیچ سندی پیدا نشد
        if not found_docs:
            return "متاسفانه اطلاعات لازم برای پاسخ به این سوال در منابع من وجود ندارد."

        context_text = "\n\n".join([doc.page_content for doc in found_docs])
        
        print("--- Context sent to LLM ---")
        print(context_text)
        print("---------------------------")

        # ۲. ساخت پرامپت سخت‌گیرانه برای ارسال به Azure AI
        system_prompt = (
                "شما یک دستیار هوش مصنوعی مفید و کارآمد هستید. وظیفه شما اولویت‌بندی پاسخ‌ها به شکل زیر است:\n"
                "1. اولویت اول شما پاسخ به سوال بر اساس اسناد پیدا شده (context) است. اگر پاسخ در اسناد وجود دارد، آن را به صورت دقیق و خلاصه بیان کن.\n"
                "2. اگر پاسخ سوال در اسناد پیدا نشد، از دانش عمومی خودت برای پاسخ به سوال استفاده کن.\n"
                "3. اگر به طور کلی قادر به پاسخگویی نیستی، مودبانه بگو که اطلاعات کافی نداری."
         
        )

        # ۳. آماده‌سازی پیام‌ها
        messages = [
            SystemMessage(content=system_prompt),
            SystemMessage(content=f"بافت ارائه شده:\n{context_text}")
        ]
        # اضافه کردن تاریخچه چت برای درک بهتر مکالمه
        for message in chat_history:
            if message['message_type'] == 'user':  # <--- تغییر از 'type' به 'message_type'
                messages.append(UserMessage(content=message['content']))
            elif message['message_type'] == 'bot': # <--- تغییر از 'type' به 'message_type'
                messages.append(AssistantMessage(content=message['content']))
# ...
        
        # اضافه کردن سوال فعلی کاربر اگر در تاریخچه نبود
        if not any(isinstance(msg, UserMessage) and msg.content == user_query for msg in messages):
            messages.append(UserMessage(content=user_query))

        # ۴. ارسال درخواست به مدل Azure AI و دریافت پاسخ نهایی
        response = llm_client.complete(
            messages=messages,
            model="gpt-4.1",
            temperature=0.2
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"An error occurred in RAG service: {e}")
        return "متاسفانه در پردازش درخواست شما خطایی رخ داد."