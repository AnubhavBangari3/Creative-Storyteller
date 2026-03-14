# Creative-Storyteller
Creative Storyteller

https://creative-storyteller-vercel1.vercel.app/

An AI-powered **multimodal storytelling agent** that transforms a simple idea into a cinematic story using **Gemini, AI-generated images, and voice narration**.

Creative Storyteller acts like an **AI Creative Director**, orchestrating text generation, visual imagery, and narration into a seamless storytelling experience.

---

# ✨ Features

- 🧠 **AI Story Generation** using Gemini
- 🎨 **AI Image Generation** for each story scene
- 🎙 **Voice Narration** using Google Cloud Text-to-Speech
- 📖 **Scene-based Story Structure**
- 🎥 **Automatic Story Playback**
- ☁️ **Cloud Storage** for generated media
- ⚡ **Scalable backend deployed on Google Cloud Run**

Users simply provide:

- Topic
- Tone
- Language
- Audience
- Duration

The system generates a **multi-scene cinematic story** with narration, visuals, and audio.

---

# 🧠 How It Works

1️⃣ User enters story parameters in the frontend  
2️⃣ Backend calls **Gemini API** to generate story scenes  
3️⃣ Each scene includes:
- narration text
- visual prompt
- audio cue

4️⃣ Images are generated using AI  
5️⃣ Narration audio is generated using **Google Text-to-Speech**  
6️⃣ Media assets are stored in **Google Cloud Storage**  
7️⃣ Frontend plays the story scene-by-scene

---

# 🏗 System Architecture

![System Architecture](Architecture.png)

---

# 🛠 Tech Stack

### Frontend
- Next.js
- React
- TypeScript
- TailwindCSS

### Backend
- Python
- Django
- Django REST Framework

### AI & Cloud
- Gemini (Google GenAI SDK)
- Google Vertex AI
- Google Cloud Run
- Google Cloud Storage
- Google Cloud Text-to-Speech

### DevOps
- Docker
- Vercel

---


