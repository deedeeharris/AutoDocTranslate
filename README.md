
# AI Document Translator

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://autodoctranslate.streamlit.app/)  

This Streamlit application uses Google's Gemini 2.0 Flash model to translate documents from a source language to a target language. It supports `.docx` files. The app provides a combined translation (showing both source and target text) and a translated-only version, both downloadable as a single ZIP archive.

## Features

*   **Document Translation:** Translates `.docx` documents using the Gemini 2.0 Flash model.
*   **Language Support:** Supports a wide range of languages for both source and target.  See the language selection dropdown in the app for the full list.
*   **Summary Generation:** Generates a summary of the document in the target language.
*   **Combined and Translated-Only Output:**  Produces two DOCX files:
    *   A combined version with a table showing paragraph IDs, source text, and translated text.
    *   A translated-only version containing just the translated paragraphs.
*   **ZIP Download:** Packages both output DOCX files into a single ZIP archive for easy download.
*   **Progress Bar:** Displays a progress bar during translation using `tqdm`.
*   **Right-to-Left (RTL) Support:** Correctly handles RTL languages (e.g., Hebrew, Arabic) in the output DOCX files, including table and paragraph alignment.
*   **Error Handling:** Includes robust error handling for API issues, invalid API keys, and file processing errors.
*   **API Key Management:** Securely handles the Gemini API key using Streamlit secrets (or an optional input field).
*   **Streamlit UI:** Provides a clean and user-friendly interface built with Streamlit.

## Requirements

*   Python 3.9+
*   `streamlit`
*   `google-generativeai`
*   `python-docx`
*   `pandas`
*   `tqdm`
*   `zipfile` (part of the Python standard library)
*   A valid Google Gemini API key.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/deedeeharris/AutoDocTranslate.git
    cd AutoDocTranslate
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your Gemini API Key:**

    *   **Recommended: Using Streamlit Secrets:**
        *   Create a `.streamlit/secrets.toml` file in your project directory.
        *   Add your API key to the `secrets.toml` file:

            ```toml
            GEMINI_API_KEY = "your-api-key-here"
            ```

    *   **Alternative (Less Secure): Using an Input Field:**
        *   The application includes an optional text input field in the sidebar where you can enter your API key.  This is less secure than using secrets, especially if you deploy your app publicly.

5. **Run the application:**
    ```
    streamlit run main.py
    ```

## Usage

1.  **Upload a Document:**  Use the "Choose a file" button to upload a `.docx` file.
2.  **Select Languages:** Choose the source and target languages from the dropdown menus.
3.  **Translate:** Click the "Translate" button.
4.  **View Progress:**  A progress bar will show the translation progress.
5.  **Download Results:** Once the translation is complete, a "Download All Files (ZIP)" button will appear.  Click it to download a ZIP archive containing the combined and translated DOCX files.
6. **View Summary:** You can view the generated summary in the target language by expanding the "Show Summary in Target Language" section.

## Project Structure

*   **`main.py`:** The main Streamlit application file.  Contains the UI, translation logic, and file handling.
*   **`requirements.txt`:**  Lists the required Python packages.
*   **`.streamlit/secrets.toml`:** (Recommended) Stores your Gemini API key securely.
*   **`translator_image.png`:** (Optional) An image file for the sidebar. You can replace this with your own image or remove the image-related code if you don't need it.

## `requirements.txt`

```
streamlit
google-generativeai
python-docx
pandas
tqdm
```

## Important Notes

*   **API Key:**  You *must* have a valid Google Gemini API key to use this application.  Obtain one from the Google Cloud Console.
*   **Rate Limits:**  Be aware of the Gemini API's rate limits.  The code includes a 10-second delay between paragraph translations to help avoid exceeding these limits.  You may need to adjust this delay depending on your usage and the API's current limits.
*   **Error Handling:** The application includes error handling for common issues, but it's not exhaustive.  For production use, consider adding more comprehensive error handling and logging.
*   **Demo Project:** This is a demonstration project and may have limitations.  For critical translations, always consult a professional human translator.

## Contributing

Contributions are welcome!  Please feel free to submit pull requests or open issues to suggest improvements or report bugs.

