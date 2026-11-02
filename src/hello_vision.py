import base64, os, sys
from dotenv import load_dotenv
from groq import Groq

load_dotenv()  # loads the values from .env into the environment
client = Groq(api_key=os.environ["GROQ_API_KEY"])
model = os.environ["GROQ_MODEL"]

image_path = sys.argv[1]  # the image filename you give on the command line
with open(image_path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()  # image -> text the API accepts

response = client.chat.completions.create(
    model=model,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text",
             "text": "Read this receipt. List the shop name, date, each item with its amount, and the total."},
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        ],
    }],
)
print(response.choices[0].message.content)