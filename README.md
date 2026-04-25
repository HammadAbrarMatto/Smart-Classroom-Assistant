# 🎓 Smart Classroom Assistant

An AI-powered classroom tool that converts **speech, text, and online content** into simplified, translated, and spoken output.

---

## 🚀 Features

* 🎙️ **Speech-to-Text**

  * Single-shot and real-time live listening
* 🌐 **Multi-language Translation**

  * Supports 100+ languages
* 🔊 **Text-to-Speech (TTS)**

  * Converts processed text into audio
* 📄 **Content Extraction**

  * Fetch from URLs or upload PDF, DOCX, TXT
* 💡 **Text Simplification**

  * Converts complex content into easy language
* 📋 **Session History**

  * Track and export past interactions

---

## 🧠 Tech Stack

* **Frontend/UI:** Streamlit
* **Backend:** Python
* **Speech Recognition:** SpeechRecognition + PyAudio
* **Translation:** deep-translator
* **TTS:** gTTS
* **Web Scraping:** BeautifulSoup
* **File Processing:** pdfplumber, python-docx

---

## 📂 Project Structure

```
Smart-Classroom-Assistant/
│
├── app.py
├── speech_module.py
├── translation_module.py
├── simplification_module.py
├── content_fetcher.py
├── tts_module.py
├── requirements.txt
├── README.md
```

---

## ▶️ How to Run

### 1. Clone Repository

```
git clone https://github.com/yourusername/smart-classroom-assistant.git
cd smart-classroom-assistant
```

### 2. Create Virtual Environment

```
python -m venv venv
venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

### 4. Run the App

```
streamlit run app.py
```

---

## ⚠️ Requirements

* Python 3.9+
* Working Microphone (for speech mode)
* Internet connection (for translation & TTS)

---

## 📌 Example Use Cases

* Classroom lecture transcription
* Language translation assistant
* Study material simplification
* Voice-based learning system

---

## 👨‍💻 Author

**Hammad Abrar**
