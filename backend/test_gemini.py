import os
import google.generativeai as genai
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        try:
            model = genai.GenerativeModel(m.name)
            response = model.generate_content("hello")
            print(f"{m.name} success")
            break
        except Exception as e:
            print(f"{m.name} error: {e}")
