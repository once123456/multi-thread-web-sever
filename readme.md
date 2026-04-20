# Comp 2322 Multi-threaded Web Server
Student: Huang Huakai
ID: 24101506d

## 1. Project Introduction
This is a multi-threaded HTTP web server implemented in pure Python using socket programming.
It fully complies with HTTP/1.1 specifications and supports all functions required by the project.

## 2. Features Implemented
- Multi-threaded concurrent processing
- GET method for HTML, TXT, PNG, JPG
- HEAD method (response headers only)
- 5 standard HTTP status codes: 200, 304, 400, 403, 404
- Cache control: Last-Modified / If-Modified-Since
- Persistent connection: Connection: keep-alive
- Access logging (request.log)
- Path traversal attack protection (403 Forbidden)

## 3. File Structure
```
├── server.py          # Main server code
├── README.md          # Project description
├── web_root/          # Static file directory
│   ├── index.html     # Homepage
│   ├── test.txt       # Text file test
│   └── test.png       # Image file test
└── request.log        # Auto-generated access log
```

## 4. How to Run
1. Create a folder named `web_root`
2. Put `index.html`, `test.txt`, `test.png` inside
3. Run the server:
```
python server.py
```
4. Open your browser and visit:
```
http://127.0.0.1:8080
```

## 5. Test Instructions
### 5.1 GET Request (200 OK)
- URL: http://127.0.0.1:8080/index.html
- URL: http://127.0.0.1:8080/test.txt
- URL: http://127.0.0.1:8080/test.png
- Note: Use **incognito mode** to avoid local cache

### 5.2 404 Not Found
- URL: http://127.0.0.1:8080/abc.html

### 5.3 Cache Validation (304 Not Modified)
1. Access index.html
2. Refresh **without modifying** the file
3. Server returns 304
4. Modify index.html and refresh → returns 200

### 5.4 400 Bad Request (PowerShell)
```
Invoke-WebRequest -Uri http://127.0.0.1:8080/index.html -Method POST
```

### 5.5 403 Forbidden (Path Traversal Protection)
```
Invoke-WebRequest -Uri "http://127.0.0.1:8080/../secret.txt"
problem: the server will automatically remove the ../ from the path
```

### 5.6 HEAD Method (PowerShell)
```
Invoke-WebRequest -Uri http://127.0.0.1:8080/index.html -Method HEAD
```

### 5.7 Persistent Connection (keep-alive)
1. Press F12 in browser
2. Go to Network panel
3. Check Response Headers:
```
Connection: keep-alive
```

## 6. Status Code Explanation
- 200 OK: Request succeeded
- 304 Not Modified: Content not changed (cache valid)
- 400 Bad Request: Invalid request method or format
- 403 Forbidden: Access denied (path traversal attack)
- 404 Not Found: File does not exist

## 7. Log File
All requests are logged in `request.log`:
- Timestamp
- Client IP
- Request path
- Response status code

## 8. Notes
- Browsers automatically normalize URLs, so 403 may not be triggered via browser address bar.
- Use PowerShell to test 400 and 403.
- Incognito mode is recommended for accurate 200 OK testing.
```
