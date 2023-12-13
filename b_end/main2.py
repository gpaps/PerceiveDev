import threading
from fastapi_app import app
from grpc_server import serve_grpc
import ssl

# Start gRPC server in a separate thread
threading.Thread(target=serve_grpc, daemon=True).start()

#TODO later on when the domain is specified
# for Production with a Reverse Proxy for secure HTTPS-using either nginx or apache2
#TODO for now the stand-alone Self-signed-Certificate.

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        ssl_keyfile="/home/gpaps/PycharmProjects/PerceiveDev/b_end/key.pem",
        ssl_certfile="/home/gpaps/PycharmProjects/PerceiveDev/b_end/cert.pem"

    )