import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

# Configurar la API de Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("❌ No se encontró la API Key. Verifica tu archivo .env.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

# Configurar la app en Streamlit
st.set_page_config(page_title="SmartSupport AI - Aritti", page_icon="🛍️", layout="centered")

st.title("🛍️ SmartSupport AI para Aritti")
st.write("Bienvenido! Soy tu asistente virtual y estoy aquí para ayudarte con tus dudas sobre talles, disponibilidad de productos, envíos y cambios.")

# 📌 Preguntas Frecuentes
with st.expander("📌 Preguntas Frecuentes"):
    st.write("""
    **1️⃣ ¿Cómo elegir el talle correcto?**  
    - Puedes revisar nuestra guía de talles en la web o preguntar en el chat.

    **2️⃣ ¿Cuánto tarda en llegar mi pedido?**  
    - Los envíos nacionales demoran entre 3 a 7 días hábiles.

    **3️⃣ ¿Cómo puedo hacer un cambio o devolución?**  
    - Tienes hasta 30 días para cambiar un producto presentando tu factura.

    **4️⃣ ¿Hay descuentos o promociones activas?**  
    - ¡Sí! Pregunta en el chat para conocer nuestras ofertas actuales.
    """)

# Prompt personalizado para el chatbot
prompt_inicial = """
Eres un asistente virtual especializado en atención al cliente para Aritti, una tienda ecommerce de ropa.
Tu tarea es responder preguntas frecuentes de los clientes de manera clara y precisa, ofreciendo información relevante sobre:
- Talles de ropa y recomendaciones de ajuste.
- Disponibilidad de productos en el catálogo.
- Tiempos de envío según ubicación del cliente.
- Políticas de cambio y devolución.

Asegúrate de proporcionar respuestas detalladas y útiles. Si no tienes información sobre una consulta específica, sugiere al cliente visitar la web oficial o contactar con soporte humano.
"""

# Historial de chat (para mantener conversaciones previas)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Mostrar historial
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

# Input del usuario
user_input = st.chat_input("Escribe tu mensaje aquí...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    
    try:
        # Llamada a Gemini AI
        mensaje_completo = f"{prompt_inicial}\n\nCliente: {user_input}\nAsistente:"
        response = model.generate_content(mensaje_completo)
        bot_response = response.text if hasattr(response, "text") else "No tengo una respuesta en este momento."
    
    except Exception as e:
        bot_response = f"❌ Error en la IA: {str(e)}"
    
    with st.chat_message("assistant"):
        st.markdown(bot_response)
    
    # Guardar en historial
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
