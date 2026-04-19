import socket
import threading
import os
from datetime import datetime, timezone

class Server:
    """
    Standard HTTP Server (Clean Version)
    """
    def __init__(self, host="127.0.0.1", port=8080):
        print("Initializing HTTP server...")
        self.host = host
        self.port = port
        self.web_root = "./web_root"
        self.log_lock = threading.Lock()
        self.setup_socket()
        print(f"Server is running on {self.host}:{self.port}")
        self.accept()

    def setup_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)

    def accept(self):
        while True:
            client, address = self.socket.accept()
            th = threading.Thread(target=self.handle_client, args=(client, address))
            th.start()

    def handle_client(self, client, address):   
        client.settimeout(10) #timeout 10 seconds
        while True:
            try:
                request_data = client.recv(4096).decode('utf-8')
            except socket.timeout:
                break
            if not request_data:
                break
            
            print(f"Received request from {address}")
            method, path, version, request_headers = self.parse_request(request_data)
            status_code, response = self.handle_method(method, path, version, request_headers)
            client.sendall(response)
            self.write_log(address, path, status_code)
            
            if request_headers.get("Connection") == "close": #if no long connection
                break
        client.close()

    def parse_request(self, request):
        lines = request.split('\r\n')
        request_headers = {}
        
        first_line = lines[0].strip()
        parts = first_line.split()
        if len(parts) < 3: #invalid request
            return None, None, None, request_headers
        
        method = parts[0]
        path = parts[1]
        version = parts[2]
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            if ':' not in line:
                continue
            key, value = line.split(':', 1)
            request_headers[key.strip()] = value.strip()
        
        return method, path, version, request_headers

    def handle_method(self, method, path, version, request_headers):
        print(f"path: {path}")

        # security check 403
        if ".." in path:
            return self.build_response(403, "Forbidden", version, request_headers)
        
        if method not in ["GET", "HEAD"]:
            return self.build_response(400, "Bad Request", version, request_headers)

        if method == "GET":
            return self.get_request(path, version, request_headers, is_head=False)
        
        elif method == "HEAD":
            return self.get_request(path, version, request_headers, is_head=True)
        
        return self.build_response(400, "Bad Request", version, request_headers)

    def build_response(self, status_code, content, version, request_headers=None, response_headers=None, body=b''):
        res = ResponseBuilder(version)
        res.set_status(status_code, content)
        
        # automatically handle Connection negotiation (HTTP standard)
        conn = "keep-alive"
        if request_headers:
            conn = request_headers.get("Connection", "keep-alive")
        res.add_header("Connection", conn)
        
        # add custom response headers
        if response_headers:
            for k, v in response_headers.items():
                res.add_header(k, v)
        
        res.set_body(body)
        return status_code, res.build()

    def get_request(self, path, version, request_headers, is_head=False):
        if path == "/":
            path = "/index.html"
                
        file_path = os.path.join(self.web_root, path.lstrip("/"))
        if not os.path.isfile(file_path):
            return self.build_response(404, "Not Found", version, request_headers)
        
        # file type
        if file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
            content_type = "image/jpeg"
        elif file_path.endswith(".png"):
            content_type = "image/png"
        else:
            content_type = "text/html"

        content_len = os.path.getsize(file_path)

        # 304 cache check
        is_modified, last_modified = self.handle_is_modified(path, request_headers)
        if is_modified:
            resp_h = {
                "Last-Modified": last_modified
            }
            return self.build_response(304, "Not Modified", version, request_headers, resp_h)
        
        # normal 200 response headers
        resp_h = {
            "Content-Type": content_type,
            "Content-Length": content_len,
            "Last-Modified": last_modified
        }

        if is_head:
            return self.build_response(200, "OK", version, request_headers, resp_h)
        else:
            body = self.read_file(path)
            return self.build_response(200, "OK", version, request_headers, resp_h, body)
        
    def handle_is_modified(self, path, request_headers):
        mtime = os.path.getmtime(os.path.join(self.web_root, path.lstrip('/')))
        dt = datetime.fromtimestamp(mtime, timezone.utc)
        last_modified = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        ims = request_headers.get("If-Modified-Since")
        if ims and ims == last_modified:
            return True, last_modified
        return False, last_modified

    def read_file(self, path):
        try:
            with open(os.path.join(self.web_root, path.lstrip('/')), "rb") as f:
                return f.read()
        except FileNotFoundError:
            return b"<h1>404 Not Found</h1>"

    def write_log(self, address, path, status_code):
        ip = address
        t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{t}] {ip} | {path} | {status_code}\n"
        with self.log_lock: #lock the log file to avoid race condition
            with open("request.log", "a", encoding="utf-8") as f:
                f.write(log_message)

class ResponseBuilder:
    def __init__(self, version="HTTP/1.1"):
        self.version = version
        self.status_line = ""
        self.headers = {}
        self.body = b""

    def set_status(self, code, reason):
        self.status_line = f"{self.version} {code} {reason}"

    def add_header(self, key, value):
        self.headers[key] = value

    def set_body(self, body_bytes):
        self.body = body_bytes

    def build(self):
        res = self.status_line + "\r\n"
        for k, v in self.headers.items():
            res += f"{k}: {v}\r\n"
        res += "\r\n"
        return res.encode("utf-8") + self.body

if __name__ == "__main__":
    server = Server()