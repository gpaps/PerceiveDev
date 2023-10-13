import threading
from fastapi_app import app
from grpc_server import serve_grpc

# Start gRPC server in a separate thread
threading.Thread(target=serve_grpc, daemon=True).start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
