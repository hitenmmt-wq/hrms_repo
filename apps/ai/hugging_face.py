import time

import requests
from django.conf import settings


class HuggingFaceLLM:
    def __init__(self):
        self.url = "https://router.huggingface.co/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {settings.HF_API_KEY}",
            "Content-Type": "application/json",
        }

    def generate(self, prompt: str) -> tuple[str, float]:
        start = time.time()

        payload = {
            "model": settings.HF_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an HRMS assistant. "
                        "Answer ONLY using the provided context. "
                        "Do not guess or hallucinate."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "max_new_tokens": 300,
            "temperature": 0.6,
        }

        response = requests.post(
            self.url,
            headers=self.headers,
            json=payload,
            timeout=60,
        )

        duration = round(time.time() - start, 3)

        if response.status_code != 200:
            print("HF ERROR BODY:", response.text)
            raise RuntimeError(f"HF error {response.status_code}")

        data = response.json()

        # if isinstance(data, list):
        #     return data[0]["generated_text"].strip(), duration

        return data["choices"][0]["message"]["content"].strip(), duration
        # return data["generated_text"].strip(), duration
