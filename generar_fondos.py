import os
import requests
import time

API_URL = "https://router.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
# Token de Hugging Face proporcionado por el usuario
HUGGINGFACE_TOKEN = "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"

HEADERS = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}

BACKGROUND_DIR = os.path.join(os.path.dirname(__file__), "backgrounds")


def generate_image(prompt, out_path):
    response = requests.post(
        API_URL,
        headers=HEADERS,
        json={"inputs": prompt, "options": {"wait_for_model": True}},
        timeout=120,
        verify=False  # Ignorar verificación SSL
    )
    if response.status_code == 200:
        with open(out_path, "wb") as f:
            f.write(response.content)
        print(f"Imagen guardada: {out_path}")
    else:
        try:
            err = response.json()
            if 'estimated_time' in err:
                print(f"Modelo en cola, tiempo estimado: {err['estimated_time']}s")
            elif 'error' in err:
                print(f"Error: {err['error']}")
            else:
                print(f"Error {response.status_code}: {response.text}")
        except Exception:
            print(f"Error {response.status_code}: {response.text}")


def main():
    for fname in os.listdir(BACKGROUND_DIR):
        if fname.endswith(".prompt.txt"):
            prompt_path = os.path.join(BACKGROUND_DIR, fname)
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read().replace("Prompt:", "").strip()
            out_name = fname.replace(".prompt.txt", ".jpg")
            out_path = os.path.join(BACKGROUND_DIR, out_name)
            if os.path.exists(out_path):
                print(f"Ya existe: {out_path}")
                continue
            print(f"Generando imagen para: {fname}")
            generate_image(prompt, out_path)
            time.sleep(10)  # Evita rate limit

if __name__ == "__main__":
    main()
