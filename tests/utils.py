def csrf_token_for(client, path: str) -> str:
    page = client.get(path).data.decode("utf-8")
    needle = 'name="csrf_token" value="'
    start = page.find(needle) + len(needle)
    end = page.find('"', start)
    return page[start:end]
