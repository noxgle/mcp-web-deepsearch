# Plan: MCP Server (Docker) — WebDeepSearchAgent

## Cel
Stworzyć serwer MCP uruchamiany w Dockerze, oparty na `scripts/WebSearchAgent.py` z repo `https://github.com/noxgle/opencode-web-deepsearch`. Serwer ma być standardowym serwerem MCP obsługującym dowolnych agentów (klientów MCP) — lokalnie (stdio) i zdalnie (streamable HTTP), z obsługą wielu równoczesnych zapytań.

## Kontekst techniczny (ustalenia wstępne)
- `WebSearchAgent.py` to samodzielny plik (stdlib + `ddgs`, `requests`, `bs4`, `aiohttp`, `lxml`) z klasą `WebDeepSearch(config)` → `execute(query, max_sources, deep_search)` zwraca dict (JSON).
- `DEFAULT_CONFIG` pozwala na per-wywołaniowe nadpisywanie parametrów (timeout, max_iterations, min_confidence, max_total_time, max_concurrent_fetches, max_content_length) — wykorzystać dla różnych agentów.
- Uwaga: `execute()` wewnętrznie woła `asyncio.run()` → handler MCP musi wywoływać go przez `asyncio.to_thread()` (inaczej RuntimeError w pętli eventów; fallback i tak przejdzie na synchroniczny requests, ale tracimy szybką ścieżkę aiohttp).
- MCP Python SDK w wersji bieżącej (>=1.12): nowe API `MCPServer` (`from mcp.server.mcpserver import MCPServer`), transport konfigurowany w `mcp.run(transport="stdio"|"streamable-http", host=..., port=..., json_response=True)`.
- Do wyboru transportu służy zmienna środowiskowa `TRANSPORT` (stdio domyślnie | http), `HOST=0.0.0.0`, `PORT=8000`.
- `WebSearchAgent.py` wersjonować do projektu (kopiowany plik, MIT, z nagłówkiem attribution), zamiast klonować repo w buildzie — deterministyczny build bez zależności od GitHub w trakcie budowy.

## Struktura projektu
```
web-deepsearch/
├── todo.md                  ← ten plan
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── README.md
└── server/
    ├── mcp_server.py        ← serwer MCP (MCPServer) + tool + info
    ├── WebSearchAgent.py    ← skopiowany z repo (źródło + licencja w headerze)
    └── requirements.txt
```

## Kroki implementacji

### 1. Pobrać i zwendrować WebSearchAgent.py
- Pobrać plik z `https://raw.githubusercontent.com/noxgle/opencode-web-deepsearch/main/scripts/WebSearchAgent.py`.
- Zapisać jako `server/WebSearchAgent.py` z dołączonym komentarzem: źródło, commit, licencja MIT.
- Nie modyfikować logiki skryptu (0 zmian w pliku).

### 2. Napisać `server/mcp_server.py`
- `MCPServer("web-deepsearch")` + `instructions` opisujące możliwości.
- Tool async `web_deepsearch`:
  - argumenty: `query: str` (wymagane), `max_sources: int = 5`, `deep_search: bool = True`
  - opcjonalne overridy configu: `max_iterations`, `min_confidence`, `timeout`, `max_total_time`, `max_concurrent_fetches`, `max_content_length`
  - wywołanie: `result = await asyncio.to_thread(agent.execute, ...)` (nowa instancja `WebDeepSearch(config)` na każde wywołanie — stan bezglobalny, bezpieczny dla wielu agentów)
  - zwraca dict wyniku (auto-serializacja JSON).
- Tool `web_deepsearch_server_info` — zwraca nazwę serwera, wersję, listę parametrów i domyślnych wartości (odkrywanie możliwości przez dowolnego agenta).
- Parsowanie `--transport` / env: `TRANSPORT` (stdio|http), `HOST`, `PORT`.
- `if __name__ == "__main__": mcp.run(transport=..., host=..., port=..., json_response=True)`.

### 3. `server/requirements.txt`
- `mcp>=1.12`
- `ddgs`
- `beautifulsoup4`
- `requests`
- `aiohttp`
- `lxml`

### 4. `Dockerfile`
- Baza: `python:3.12-slim`
- `pip install` z requirements.txt
- `WORKDIR /app`, `COPY server/ server/`
- `ENV TRANSPORT=stdio HOST=0.0.0.0 PORT=8000`
- `EXPOSE 8000`
- `ENTRYPOINT ["python", "server/mcp_server.py"]`

### 5. `docker-compose.yml`
- Serwis `web-deepsearch` budowany z Dockerfile.
- Tryb http: `environment: TRANSPORT=http`, `ports: 8000:8000` (dla zdalnych agentów).
- Tryb stdio: uruchamiany bez portów (docker run -i — lokalni agenci).

### 6. `.dockerignore`
- Wykluczyć: `__pycache__`, `.git`, `.env`, dokumentację zbędną w obrazie.

### 7. Testy (weryfikacja)
- `docker build -t web-deepsearch-mcp .`
- Smoke test stdio: uruchomić kontener z `TRANSPORT=stdio` i wysłać sekwencję JSON-RPC: `initialize` → `notifications/initialized` → `tools/list` (oczekiwane 2 narzędzia) → `tools/call` z `web_deepsearch` i realnym query (np. `max_sources: 1, deep_search: false`), zweryfikować strukturę wyniku (sources, iterations_used, source_count).
- Smoke test HTTP: kontener z `TRANSPORT=http`, `curl -X POST http://localhost:8000/mcp` z nagłówkami MCP i ręką JSON-RPC (initialize + tools/list).
- Zweryfikować konkurrencyjność: 2 równoległe `tools/call` (np. `curl` + drugi proces).
- Zweryfikować strukturę wyniku (sources, iterations_used, source_count).

### 8. `README.md`
- Opis projektu, wymagania (Docker).
- Jak uruchomić: stdio (`docker run -i`), http (`docker compose up`).
- Przykłady konfiguracji klientów MCP dla różnych agentów (OpenCode, Claude Code, inne) z adresem endpointu.
- Lista narzędzi i parametrów + przykładowy JSON wyniku.
- Uwagi: limit/ryzyko rate-limit DuckDuckGo, kontener wymaga dostępu do internetu.

## Kryteria ukończenia (Definition of Done)
- [ ] `todo.md` zapisany (ten plik).
- [ ] `server/WebSearchAgent.py` — zwendrowany, bez modyfikacji logiki.
- [ ] `server/mcp_server.py` — serwer działa, 2 narzędzia, obsługa stdio + http.
- [ ] Docker build przechodzi.
- [ ] Smoke testy stdio i HTTP przechodzą (initialize, tools/list, tools/call z realnym wyszukiwaniem).
- [ ] `docker-compose.yml` działa dla trybu http.
- [ ] README kompletne.
