import threading
from fastapi_app import app
from grpc_server import serve_grpc
from uvicorn import Config, Server
# Start gRPC server in a separate thread
threading.Thread(target=serve_grpc, daemon=True).start()

if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8001)
    config = Config(app=app, host="0.0.0.0", port=8001, limit_max_request_size=50 * 1024 * 1024)
    server = Server(config)
    server.run()