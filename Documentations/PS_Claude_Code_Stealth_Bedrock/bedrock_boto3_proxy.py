#!/usr/bin/env python3
"""
Bedrock Boto3 Proxy — Level 2 Stealth for Claude Code
======================================================
Sits between Claude Code and AWS Bedrock. Claude Code sends
requests to this proxy (localhost:8900), and the proxy re-sends
them to Bedrock via boto3 — making the TLS fingerprint, HTTP
patterns, and User-Agent 100% identical to native boto3.

Usage:
    python3 bedrock_boto3_proxy.py                    # Default: us-east-1, port 8900
    python3 bedrock_boto3_proxy.py --region us-west-2 # Custom region
    python3 bedrock_boto3_proxy.py --port 9000        # Custom port

Then in another terminal:
    source full-stealth-setup.sh --proxy
    claude

Architecture:
    Claude Code --HTTP--> localhost:8900 --boto3/TLS--> bedrock-runtime.{region}.amazonaws.com

What AWS sees:
    User-Agent: Boto3/1.35.0 Python/3.11.9 Linux/... Botocore/1.35.0
    TLS: Python's ssl module (not Node.js)
    Everything else: Standard boto3 InvokeModel call
"""

import argparse
import json
import sys
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

try:
    import boto3
    from botocore.config import Config as BotoConfig
except ImportError:
    print("ERROR: boto3 is required. Install with: pip install boto3")
    sys.exit(1)


class BedrockProxyHandler(BaseHTTPRequestHandler):
    """Proxies Bedrock API calls from Claude Code through boto3."""

    # Shared boto3 client (set by main)
    bedrock_client = None
    bedrock_streaming_client = None
    request_count = 0
    lock = threading.Lock()

    def log_message(self, fmt, *args):
        """Custom log format."""
        with self.lock:
            BedrockProxyHandler.request_count += 1
            count = BedrockProxyHandler.request_count
        # Minimal logging — just method + path + count
        sys.stderr.write(f"[proxy #{count}] {args[0]}\n")

    def do_GET(self):
        """Health check endpoint."""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "proxy": "bedrock-boto3-proxy",
                "requests_served": BedrockProxyHandler.request_count,
            }).encode())
            return
        self.send_error(404)

    def do_POST(self):
        """Forward POST requests to Bedrock via boto3."""
        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # Parse model ID from URL path
        # Expected paths from AnthropicBedrock SDK:
        #   /model/{modelId}/invoke
        #   /model/{modelId}/invoke-with-response-stream
        #   /model/{modelId}/converse
        #   /model/{modelId}/converse-stream
        path = self.path.strip("/")
        parts = path.split("/")

        if len(parts) < 3 or parts[0] != "model":
            # Fallback: try to extract model from body
            try:
                body_json = json.loads(body)
                model_id = body_json.get("model", "unknown")
            except (json.JSONDecodeError, KeyError):
                self.send_error(400, "Cannot determine model ID from path or body")
                return
            action = parts[-1] if parts else "invoke"
        else:
            # /model/MODEL_ID/ACTION
            model_id = "/".join(parts[1:-1])  # Handle model IDs with slashes
            action = parts[-1]

        is_stream = "stream" in action

        try:
            if is_stream:
                self._handle_streaming(model_id, body)
            else:
                self._handle_invoke(model_id, body)
        except Exception as e:
            sys.stderr.write(f"[proxy] ERROR: {e}\n")
            self.send_error(502, str(e))

    def _handle_invoke(self, model_id, body):
        """Non-streaming invoke via boto3."""
        response = self.bedrock_client.invoke_model(
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        result = response["body"].read()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(result)))
        # Forward Bedrock response headers that Claude Code expects
        if "ResponseMetadata" in response:
            request_id = response["ResponseMetadata"].get("RequestId", "")
            if request_id:
                self.send_header("x-amzn-RequestId", request_id)
        self.end_headers()
        self.wfile.write(result)

    def _handle_streaming(self, model_id, body):
        """Streaming invoke via boto3."""
        response = self.bedrock_streaming_client.invoke_model_with_response_stream(
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )

        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.amazon.eventstream")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()

        try:
            for event in response["body"]:
                if "chunk" in event:
                    chunk_bytes = event["chunk"]["bytes"]
                    # Send as HTTP chunked transfer encoding
                    chunk_header = f"{len(chunk_bytes):x}\r\n".encode()
                    self.wfile.write(chunk_header)
                    self.wfile.write(chunk_bytes)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()

            # End chunked transfer
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except Exception as e:
            sys.stderr.write(f"[proxy] Streaming error: {e}\n")


class ThreadedHTTPServer(HTTPServer):
    """Handle each request in a new thread for concurrent Claude Code calls."""
    allow_reuse_address = True

    def process_request(self, request, client_address):
        thread = threading.Thread(target=self.process_request_thread,
                                  args=(request, client_address))
        thread.daemon = True
        thread.start()

    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


def main():
    parser = argparse.ArgumentParser(
        description="Bedrock boto3 proxy — makes Claude Code invisible to AWS"
    )
    parser.add_argument("--port", type=int, default=8900, help="Port to listen on (default: 8900)")
    parser.add_argument("--region", type=str,
                        default=os.environ.get("AWS_REGION", "us-east-1"),
                        help="AWS region (default: AWS_REGION env or us-east-1)")
    args = parser.parse_args()

    # Create boto3 clients with explicit config
    boto_config = BotoConfig(
        region_name=args.region,
        retries={"max_attempts": 3, "mode": "adaptive"},
        read_timeout=600,      # Match Claude Code's 10-minute timeout
        connect_timeout=10,
    )

    print(f"Creating boto3 Bedrock clients (region: {args.region})...")
    BedrockProxyHandler.bedrock_client = boto3.client(
        "bedrock-runtime", config=boto_config
    )
    BedrockProxyHandler.bedrock_streaming_client = boto3.client(
        "bedrock-runtime", config=boto_config
    )

    # Start server
    server = ThreadedHTTPServer(("127.0.0.1", args.port), BedrockProxyHandler)
    print(f"")
    print(f"============================================")
    print(f"  Bedrock Boto3 Proxy — RUNNING")
    print(f"============================================")
    print(f"  Listening: http://127.0.0.1:{args.port}")
    print(f"  Region:    {args.region}")
    print(f"  Health:    http://127.0.0.1:{args.port}/health")
    print(f"")
    print(f"  In another terminal:")
    print(f"    source full-stealth-setup.sh --proxy")
    print(f"    claude")
    print(f"")
    print(f"  AWS will see: Boto3 + Python TLS")
    print(f"============================================")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
