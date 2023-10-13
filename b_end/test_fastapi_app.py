from fastapi.testclient import TestClient
from fastapi_app import app

client = TestClient(app)


def test_read_file():
    # For the purpose of this test, let's assume there's a path "sample.txt" in your Nextcloud.
    # Replace this with any file you know exists.
    response = client.get("/file/Readme.md")

    assert response.status_code == 200
    # Additional assertions based on your expected response can be added.


def test_upload_file():
    # This will test uploading a sample file.
    # Place a sample image in the root directory for this test.
    with open("Photos/Gorilla_cv.jpg", "rb") as image_file:
        response = client.post("/upload/", files={"file": image_file})

    assert response.status_code == 200
    assert response.json() == {"status": "success",
                               "message": "Processed file saved to Nextcloud at Photos/sample_image.png"}


def test_get_image():
    # For the purpose of this test, let's assume there's an image "sample_image.png" in your Nextcloud's Photos folder.
    response = client.get("/Photos/Steps.jpg")

    assert response.status_code == 200
    # Additional assertions based on your expected response can be added.
