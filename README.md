
# 📜 DocuTranslateAI – AI-Powered Document Translator  

🚀 **DocuTranslateAI** is an advanced **AI-driven document translation tool** that seamlessly translates **DOCX and PDF** files into multiple languages using **Google Gemini AI**. Designed for **accurate, efficient, and professional** document translation, it ensures **context-aware** and **high-quality** output.

---

## 🌟 Features  

✅ **Supports DOCX & PDF** – Extracts text and translates entire documents  
✅ **AI-Powered Translation** – Uses **Gemini AI** for high-quality, context-aware translations  
✅ **Multi-Language Support** – Translate between **30+ languages**  
✅ **Preserves Formatting** – Keeps document structure intact  
✅ **DOCX & PDF Output** – Generate bilingual or translated-only documents  
✅ **Automatic Summarization** – AI-generated document summaries for context  
✅ **Retry Mechanism** – Handles API errors and rate limits gracefully  
✅ **User-Friendly & Efficient** – No need for manual copying, upload and translate!  

---

## 📌 Use Cases  

- **Business & Legal** – Translate contracts, reports, and corporate documents.  
- **Education & Research** – Convert academic papers, essays, and research materials.  
- **Global Communication** – Enable multilingual collaboration and document exchange.  
- **Government & NGOs** – Translate policies, reports, and official documents.  

---

## 📥 Installation  

### **1️⃣ Clone the repository**  
```sh
git clone https://github.com/yourusername/DocuTranslateAI.git
cd DocuTranslateAI
```

### **2️⃣ Install dependencies**  
Ensure you have Python installed, then install required packages:

```sh
pip install -r requirements.txt
```

### **3️⃣ Set up API Key**  
DocuTranslateAI uses **Google Gemini AI** for translation. Set up your API key:

```sh
export GEMINI_API_KEY="your-api-key-here"
```

Or, in Windows PowerShell:

```sh
$env:GEMINI_API_KEY="your-api-key-here"
```

Alternatively, you can set it inside the script manually (not recommended for production).

---

## 🔧 Usage  

### **Run the script**  

```sh
python main.py
```

### **Upload your document**  
- **DOCX or PDF** files are supported.  
- Select **Source Language** and **Target Language**.  
- Click **Translate** and let AI handle the rest!  

### **Output Formats**  
- **Bilingual DOCX & PDF** (original + translated text)  
- **Translated-only DOCX & PDF**  
- **AI-generated document summary**  

---

## 🏗️ Project Structure  

```bash
📂 DocuTranslateAI/
│── 📜 main.py              # Core translation script
│── 📜 requirements.txt     # Required dependencies
│── 📜 README.md            # Project documentation
│── 📂 utils/               # Helper functions for text processing
│── 📂 examples/            # Sample translated documents
│── 📂 output/              # Generated DOCX & PDF files
```

---

## 🛠️ Dependencies  

- `python-docx` – For handling DOCX files  
- `PyMuPDF` – Extract text from PDFs  
- `google-generativeai` – Gemini AI for translation  
- `pandas` – Data handling  
- `reportlab` – PDF generation  
- `nltk` – Natural Language Processing  
- `ipywidgets` – Interactive UI elements (for notebooks)  

Install all dependencies with:

```sh
pip install -r requirements.txt
```

---

## 📜 License  

This project is licensed under the **MIT License** – feel free to use, modify, and contribute!  

---

## 👨‍💻 Contributing  

We welcome contributions! To contribute:  

1. **Fork the repo**  
2. **Create a new branch** (`feature-xyz`)  
3. **Commit your changes** (`git commit -m "Added XYZ feature"`)  
4. **Push to your fork** (`git push origin feature-xyz`)  
5. **Submit a pull request** 🚀  

---

## 🤝 Support  

For issues or feature requests, please **open an issue** on GitHub.  

💡 **Let's make document translation smarter and more accessible!** 🚀  
