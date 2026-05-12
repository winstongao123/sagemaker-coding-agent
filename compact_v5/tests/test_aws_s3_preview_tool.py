from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.aws_s3_preview import _aws_s3_preview_executor


class _Body:
    def __init__(self, data: bytes):
        self._data = data

    def read(self) -> bytes:
        return self._data


class _S3:
    def __init__(self, data: bytes = b"hello\nworld\n", content_type: str = "text/plain"):
        self.calls = []
        self.data = data
        self.content_type = content_type

    def get_object(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "Body": _Body(self.data),
            "ContentType": self.content_type,
            "ContentLength": len(self.data),
            "ContentRange": "bytes 0-10/11",
        }


def test_s3_preview_reads_bounded_text_range():
    client = _S3()
    text = _aws_s3_preview_executor(
        {"bucket": "bucket-a", "key": "folder/file.txt", "max_bytes": 20},
        context={"s3_client": client},
    )

    assert client.calls[0]["Range"] == "bytes=0-19"
    assert "S3 preview for s3://bucket-a/folder/file.txt" in text
    assert "hello" in text
    assert "Content-Type: text/plain" in text


def test_s3_preview_does_not_dump_binary():
    client = _S3(data=b"\x00\x01\x02abc", content_type="application/octet-stream")
    text = _aws_s3_preview_executor(
        {"bucket": "bucket-a", "key": "bin.dat"},
        context={"s3_client": client},
    )

    assert "binary or unsupported content" in text
    assert "\x00" not in text


if __name__ == "__main__":
    test_s3_preview_reads_bounded_text_range()
    test_s3_preview_does_not_dump_binary()
    print("aws_s3_preview smoke: OK")
