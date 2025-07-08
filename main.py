import uvicorn
from app.app.config import get_config
from app.app.app_factory import create_app
from app.utils.logger import setup_logger

config = get_config()
setup_logger()
app = create_app(config)


def main():
    uvicorn.run(
        "main:app",
        host=config.host, 
        port=config.port, 
        reload=config.reload,
        server_header=False
    )

if __name__ == "__main__":
    main()
