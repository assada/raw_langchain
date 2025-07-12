## Quick Start

1. Clone
2. `cp .env.dist .env` and fill in the required environment variables
2. `docker compose up`
3. Open your browser and go to `http://localhost:8000`

## TODO:

 - [x] Add a way to add tools to the agent
 - [ ] Add a way to add a database to the agent (memory, checkpoints, feedback?, etc)
 - [x] Implement graph instead of simple agent
 - [ ] 	~~Keep alive SSE connection until the user closes the browser tab (??)~~
 - [ ] Add a way to validate the user's access token (OAuth2)
 - [x] Refactor the structure of the project. We need to separate general fastapi app from the agent app.
 - [ ] Add more model configuration options (temperature, top_p, etc)
 - [x] Add a way to get a thread history
 - [ ] Normalize FastApi headers/request/middleware
 - [ ] Add a way to define a custom agent in config?