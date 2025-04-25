import requests

url = "https://clinicaltrials.gov/api/v2/studies"
params = {
    "query.cond": "diabetes",
    "pageSize": 5,
    "format": "json"
}
response = requests.get(url, params=params)
print(response.json())
