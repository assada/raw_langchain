## Quick Start

1. Clone
2. `cp .env.dist .env` and fill in the required environment variables
3. `docker compose up`
4. Open your browser and go to `http://localhost:8000`

### Setup local langfuse (https://langfuse.com/self-hosting/docker-compose)

1. Clone the langfuse repository: `git clone https://github.com/langfuse/langfuse.git`
2. `cd langfuse`
3. `docker compose up`
4. Open your browser and go to `http://localhost:3000` create a new project and copy the `LANGFUSE_API_KEY` and
   `LANGFUSE_API_URL` to your `.env` file.

### Development

1. `uv sync`
2. `cd frontend`
3. `npm run build`
4. `cd ..`
5. `uv run dev`

## TODO:

- [x] Add a way to add tools to the agent
- [x] Add a way to add a database to the agent (memory, checkpoints, feedback?, etc)
- [x] Implement graph instead of simple agent
- [ ] 	~~Keep alive SSE connection until the user closes the browser tab (??)~~
- [ ] Add a way to validate the user's access token (OAuth2)
- [x] Refactor the structure of the project. We need to separate general fastapi app from the agent app.
- [x] Add more model configuration options (temperature, top_p, etc)
- [x] Add a way to get a thread history
- [ ] Store the thread history in the database (with all custom messages and metadata)
- [ ] Normalize FastApi headers/request/middleware
- [ ] Add a way to define a custom agent in config?
- [x] Add Langfuse integration
- [ ] ~~Add Langsmith integration~~
- [ ] Add tests
- [ ] Add evaluation metrics
- [ ] Add *one more* abstraction layer so the agent can use different frameworks (LangGraph, LlamaIndex, etc.)
- [ ] Add even more fucking abstractions to make it independent of observability tools (LangFuse, LangSmith, Grafana Alloy, or whatever the fuck else)
- [ ] Long-Term memory for each user. I want to add to chat application for real-time per thread prompt tuning - memory insights, response strategies, etc. But this is more about agent implementation not template core. Graph node as "addon package?" LOL! https://i.imgur.com/k1jk3cx.png here we go again!