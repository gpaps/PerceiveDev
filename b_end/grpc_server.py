from concurrent import futures
import grpc
from nextcloud_pb2_grpc import add_NextcloudServiceServicer_to_server, NextcloudServiceServicer
from nextcloud_pb2 import FileResponse as NextcloudFileResponse, UploadFileResponse
from utils import get_file_from_nextcloud, upload_file_to_nextcloud


class NextcloudService(NextcloudServiceServicer):

    def GetFile(self, request, context):
        content = get_file_from_nextcloud(request.path)
        return NextcloudFileResponse(content=content)

    def UploadFile(self, request, context):
        status, message = upload_file_to_nextcloud(request.filename, request.content)
        return UploadFileResponse(status=status, message=message)


def serve_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_NextcloudServiceServicer_to_server(NextcloudService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()
