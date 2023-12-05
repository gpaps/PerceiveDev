import threading
from fastapi_app import app
from grpc_server import serve_grpc
import ssl

cert_file = '/home/gpaps/PycharmProjects/PerceiveDev/b_end/cert.pem'
keyfile = '/home/gpaps/PycharmProjects/PerceiveDev/b_end/key.pem'

# Start gRPC server in a separate thread
threading.Thread(target=serve_grpc, daemon=True).start()

if __name__ == "__main__":
    import uvicorn

    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # ssl_context.load_cert_chain('/home/gpaps/PycharmProjects/PerceiveDev/b_end/cert.pem',
    #                             keyfile='/home/gpaps/PycharmProjects/PerceiveDev/b_end/key.pem')
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        # reload=True,
        # ssl_keyfile="/home/gpaps/PycharmProjects/PerceiveDev/b_end/cert.pem",
        # ssl_certfile='/home/gpaps/PycharmProjects/PerceiveDev/b_end/key.pem'
    )

