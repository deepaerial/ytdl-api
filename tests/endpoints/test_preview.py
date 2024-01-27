import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=NcBjx_eyvxc",
        "https://www.youtube.com/watch?v=TNhaISOUy6Q",
        "https://www.youtube.com/watch?v=QXeEoD0pB3E&list=PLsyeobzWxl7poL9JTVyndKe62ieoN-MZ3&index=1"
    ],
)
def test_get_preview(app_client: TestClient, url: str):
    response = app_client.get("/api/preview", params={"url": url})
    assert response.status_code == 200
    json_response = response.json()
    assert all(
        field in json_response
        for field in [
            "url",
            "title",
            "thumbnailUrl",
            "duration",
            "mediaFormats",
            "audioStreams",
            "videoStreams",
        ]
    )
