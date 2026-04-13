from google import genai

client = genai.Client(api_key="AIzaSyCcj1m1w88NyYjqyDIpkQE5vAhFAvD2mbs")

models = client.models.list()
for m in models:
    print(m.name)