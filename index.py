import meilisearch

client = meilisearch.Client("http://127.0.0.1:7700")

# client.create_index("phs", {
#     "primaryKey": "pflichtenheftId",
# })

index = client.index("phs")
with open("data/phs.json", "rb") as file:
    index.add_documents_json(file.read(), primary_key="pflichtenheftId")
