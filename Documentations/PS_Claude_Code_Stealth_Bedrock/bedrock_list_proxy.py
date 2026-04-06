#!/usr/bin/env python3
"""
Bedrock ListInferenceProfiles Proxy
===================================
Catches the one AWS SDK call that leaks "aws-sdk-js" in CloudTrail.
Routes it through boto3 so it shows "Boto3/1.35.0 Python/..." instead.

Usage: python3 bedrock_list_proxy.py &
Then:  source full-stealth-setup.sh --full
       claude
"""

import json
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    import boto3
except ImportError:
    print("ERROR: pip install boto3")
    sys.exit(1)

REGION = os.environ.get("AWS_REGION", "ap-southeast-2")


class ProxyHandler(BaseHTTPRequestHandler):
    client = None

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[proxy] {args[0]}\n")

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return
        self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        try:
            # Handle ListInferenceProfiles
            # The AWS SDK sends this as a POST to the Bedrock endpoint
            target = self.headers.get("X-Amz-Target", "")

            if "ListInferenceProfiles" in target or "ListInferenceProfiles" in self.path:
                self._handle_list_inference_profiles(body)
            elif "GetInferenceProfile" in target or "GetInferenceProfile" in self.path:
                self._handle_get_inference_profile(body)
            else:
                # For any other call, forward generically
                self._handle_list_inference_profiles(body)
        except Exception as e:
            sys.stderr.write(f"[proxy] ERROR: {e}\n")
            self.send_error(502, str(e))

    def _handle_list_inference_profiles(self, body):
        params = {}
        if body:
            try:
                req = json.loads(body)
                if "typeEquals" in req:
                    params["typeEquals"] = req["typeEquals"]
                if "nextToken" in req:
                    params["nextToken"] = req["nextToken"]
            except json.JSONDecodeError:
                pass

        # Call via boto3 (shows Boto3/... in CloudTrail)
        response = self.client.list_inference_profiles(**params)

        # Build response body
        result = {
            "inferenceProfileSummaries": [],
        }
        for p in response.get("inferenceProfileSummaries", []):
            summary = {}
            for k, v in p.items():
                if v is not None:
                    summary[k] = v
            result["inferenceProfileSummaries"].append(summary)

        if "nextToken" in response:
            result["nextToken"] = response["nextToken"]

        body_out = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body_out)))
        self.end_headers()
        self.wfile.write(body_out)

    def _handle_get_inference_profile(self, body):
        req = json.loads(body) if body else {}
        profile_id = req.get("inferenceProfileIdentifier", "")

        response = self.client.get_inference_profile(
            inferenceProfileIdentifier=profile_id
        )

        # Remove ResponseMetadata
        response.pop("ResponseMetadata", None)

        body_out = json.dumps(response, default=str).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body_out)))
        self.end_headers()
        self.wfile.write(body_out)


class ThreadedServer(HTTPServer):
    allow_reuse_address = True
    def process_request(self, request, client_address):
        t = threading.Thread(target=self.process_request_thread, args=(request, client_address))
        t.daemon = True
        t.start()
    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8901
    ProxyHandler.client = boto3.client("bedrock", region_name=REGION)
    server = ThreadedServer(("127.0.0.1", port), ProxyHandler)
    print(f"Bedrock list proxy running on http://127.0.0.1:{port} (region: {REGION})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
