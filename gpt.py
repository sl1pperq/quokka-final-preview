import requests

url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Api-Key ТОКЕН"
}

prompt = {
    "modelUri": "gpt://b1g8do94md8m2addo5f7/yandexgpt-lite",
    "completionOptions": {
        "stream": False,
        "temperature": 0.6,
        "maxTokens": "750"
    },
    "messages": [
        {
            "role": "system",
            "text": "Ты - учитель, который знает все предметы и проверяет различные ответы учеников, также может составлять планы школьных квизов и проверять вопросы квизов на качество"
        }
    ]
}


def create_prompt(user_text):
    prompt['messages'].append({
        'role': 'user',
        'text': user_text
    })
    response = requests.post(url, headers=headers, json=prompt).json()
    answer = response['result']['alternatives'][0]['message']['text']
    prompt['messages'].append({
        'role': 'assistant',
        'text': answer
    })
    return answer
