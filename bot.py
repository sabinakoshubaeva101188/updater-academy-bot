response = requests.get(
    f"{API_URL}/getUpdates",
    params=params,
    timeout=35
)

result = response.json()

print("GET UPDATES:", result)

return result
