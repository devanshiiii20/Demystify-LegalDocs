import os
from google.cloud import documentai_v1 as documentai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import vertexai
from textwrap import wrap
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.api_core import exceptions
from google.oauth2 import service_account

# Project info
PROJECT_ID = "demystifying-legal-docs"
LOCATION = "us"
PROCESSOR_ID = "cc201b11f66615f5"
VERTEX_AI_LOCATION = "us-central1"

SERVICE_ACCOUNT_KEY_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_KEY_PATH)
vertexai.init(project=PROJECT_ID, location=VERTEX_AI_LOCATION, credentials=credentials)

def extract_text_from_document(content):
    print("Starting text extraction from document...")
    client = documentai.DocumentProcessorServiceClient.from_service_account_file(
        SERVICE_ACCOUNT_KEY_PATH
    )
    name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}"
    raw_document = {"content": content, "mime_type": "application/pdf"}
    request = {"name": name, "raw_document": raw_document}
    response = client.process_document(request=request)
    print("Text extraction completed.")
    return response.document.text

def simplify_text(prompt, max_retries=5, initial_delay=1):
    print("Starting text simplification...")
    model = GenerativeModel("gemini-2.0-flash-lite")
    generation_config = GenerationConfig(max_output_tokens=512)
    delay = initial_delay
    for i in range(max_retries):
        try:
            resp = model.generate_content(
                f"""Summarize the following legal text in plain professional English.
                RULES:
                - Use only full sentences in paragraph form.
                - Do not use bullets, numbering, stars, or markdown formatting.
                - Do not use casual phrases like 'okay', 'let’s break this down', etc.
                - Do not repeat the same information more than once.
                - Keep it concise: no more than three short paragraphs.
                - The style must be clear, formal and explanatory.

                Text to simplify:
                {prompt}
                """,
                generation_config=generation_config
            )
            print("Text simplification completed.")
            return resp.text.strip()
        except exceptions.ResourceExhausted as e:
            if i < max_retries - 1:
                print(f"ResourceExhausted error: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"ResourceExhausted error: {e}. Max retries reached.")
                raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2
    return ""

def simplify_long_text(text, chunk_size=800):
    print("Starting long text simplification...")
    chunks = wrap(text, chunk_size)
    parts = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_chunk = {executor.submit(simplify_text, chunk): i for i, chunk in enumerate(chunks)}
        for future in as_completed(future_to_chunk):
            index = future_to_chunk[future]
            try:
                simplified_chunk = future.result()
                parts.append((index, simplified_chunk))
                print(f"Processed chunk {index+1}/{len(chunks)}...")
            except Exception as exc:
                print(f'Chunk {index+1} generated an exception: {exc}')
                parts.append((index, f"Error processing chunk {index+1}"))

    parts.sort(key=lambda x: x[0])
    return " ".join([part[1] for part in parts])

def explain_jargon(text, max_retries=5, initial_delay=1):
    print("Starting jargon explanation...")
    model = GenerativeModel("gemini-2.0-flash-lite")
    generation_config = GenerationConfig(max_output_tokens=600)
    delay = initial_delay
    for i in range(max_retries):
        try:
            prompt = f"""
           You are a legal assistant.
            Read the legal text below and explain every legal term or jargon in clear, simple English.

            Rules:
            - Do NOT use markdown or symbols like **, *, -, >, #.
            - Present each explanation as a plain sentence or numbered item.
            - Avoid repeating the same explanation.
            - Be concise but clear.

            Text:
            {text}
            """
            resp = model.generate_content(prompt, generation_config=generation_config)
            cleaned = re.sub(r"\*+", "", resp.text)
            cleaned = re.sub(r"#+", "", cleaned)
            cleaned = re.sub(r"•", "-", cleaned)
            print("Jargon explanation completed.")
            return cleaned.strip()
        except exceptions.ResourceExhausted as e:
            if i < max_retries - 1:
                print(f"ResourceExhausted error: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"ResourceExhausted error: {e}. Max retries reached.")
                raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2
    return ""

def simplify_long_text_sequential(text, chunk_size=800, delay_between_chunks=5):
    print("Starting sequential long text simplification...")
    chunks = wrap(text, chunk_size)
    parts = []
    for i, c in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        simplified_chunk = simplify_text(c)
        parts.append(simplified_chunk)
        time.sleep(delay_between_chunks)
    return " ".join(parts)
