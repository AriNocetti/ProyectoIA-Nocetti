import google.generativeai as genai

GEMINI_API_KEY = "AIzaSyAnApugibmjV4kawBIosyKUO9r6YmLBeyE"
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-pro")

response = model.generate_content("Hola, ¿puedes responderme?")
print(response.text)
