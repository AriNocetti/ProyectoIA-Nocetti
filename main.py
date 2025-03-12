import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# Cargar credenciales desde Streamlit Secrets
firebase_config = st.secrets["FIREBASE"] 
cred = credentials.Certificate(json.loads(str(st.secrets["FIREBASE"])))

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.set_page_config(page_title="SmartSupport AI - Aritti", page_icon="🛍️", layout="centered")

# Cargar variables de entorno
load_dotenv()

# Configurar la API de Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("❌ No se encontró la API Key. Verifica tu archivo .env.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro")

# Configurar Firebase
firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS")
cred = credentials.Certificate(firebase_credentials_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Obtener productos desde Firebase
@st.cache_data
def obtener_productos():
    productos_ref = db.collection("productosRopa")
    docs = productos_ref.stream()
    return [doc.to_dict() for doc in docs]

productos = obtener_productos()

# Generar contexto detallado de los productos
productos_texto = "\n".join([
    f"{p['title']} - {p['price']} - Stock: {p.get('stock', 'N/A')} - Categoría: {p.get('category', 'N/A')} - "
    f"Color: {p.get('color', 'N/A')} - Material: {p.get('fabric', 'N/A')} - Talles: {', '.join(p.get('size', []))}"
    for p in productos
])

# # Función para verificar stock
# def obtener_stock(producto_buscado):
#     productos_ref = db.collection("productosRopa")  # Asegúrate de que la colección es la correcta
#     query = productos_ref.where("title", "==", producto_buscado).stream()
    
#     stock_total = sum([int(doc.to_dict().get("stock", 0)) for doc in query])  # Convertir stock a entero
#     return stock_total

# Prompt inicial mejorado
prompt_inicial = f"""
Eres un asistente virtual exclusivo de **Aritti**, una tienda de ropa online. 
Tu objetivo es responder preguntas de clientes sobre:

- Disponibilidad de productos y stock.
- Precios y características de los artículos.
- Tiempos de envío y política de cambios.

Aquí tienes información actualizada de los productos en stock:

{productos_texto}

Si un cliente pregunta por un producto específico, revisa la información proporcionada y responde con datos precisos. 
Si un producto está agotado, informa al cliente y sugiere opciones similares. No hagas preguntas innecesarias.
"""
# Función para verificar stock
def obtener_stock(producto_buscado):
    productos_ref = db.collection("productosRopa")
    query = productos_ref.where("title", "==", producto_buscado).stream()
    stock_total = sum([int(doc.to_dict().get("stock", 0)) for doc in query])
    return stock_total

# Configurar la app en Streamlit
st.title("🛍️ SmartSupport AI para Aritti")
st.write("Bienvenido! Soy tu asistente virtual y estoy aquí para ayudarte con tus dudas sobre talles, disponibilidad de productos, envíos y cambios.")

# Mostrar productos disponibles
if st.checkbox("📦 Ver productos disponibles"):
    for producto in productos:
        st.write(f"**{producto['title']}** - {producto['price']} - Stock: {producto.get('stock', 'Desconocido')} - "
                f"Categoría: {producto.get('category', 'N/A')} - Color: {producto.get('color', 'N/A')} - "
                f"Material: {producto.get('fabric', 'N/A')} - Talles: {', '.join(producto.get('size', []))}")

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

# Historial de chat (para mantener conversaciones previas)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

# Input del usuario
user_input = st.chat_input("Escribe tu mensaje aquí...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    
    user_input_lower = user_input.lower()  # Asegurar que solo se define si hay entrada
    bot_response = ""

    # Si el usuario pregunta por stock, buscar en Firebase
    if "stock" in user_input_lower:
        producto_buscado = next((p["title"] for p in productos if p["title"].lower() in user_input_lower), None)
        if producto_buscado:
            stock_disponible = obtener_stock(producto_buscado)
            if stock_disponible > 0:
                bot_response = f"Actualmente, tenemos **{stock_disponible} unidades** del **{producto_buscado}** en stock."
            else:
                bot_response = f"Lo siento, el **{producto_buscado}** está agotado en este momento."
        else:
            bot_response = "No encontré ese producto en nuestro catálogo. Por favor, revisa nuestra web para más detalles."

    # Si no es una pregunta sobre stock, procesar con IA
    else:
        try:
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
