import hrequests

url = "https://studio-api.prod.suno.com/api/project/default"

headers = {
    "Host": "studio-api.prod.suno.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://suno.com/",
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImNhdCI6ImNsX0I3ZDRQRDExMUFBQSIsImtpZCI6Imluc18yT1o2eU1EZzhscWRKRWloMXJvemY4T3ptZG4iLCJ0eXAiOiJKV1QifQ.eyJhdWQiOiJzdW5vLWFwaSIsImF6cCI6Imh0dHBzOi8vc3Vuby5jb20iLCJleHAiOjE3NDgwNzQyNTQsImZ2YSI6WzQzLC0xXSwiaHR0cHM6Ly9zdW5vLmFpL2NsYWltcy9jbGVya19pZCI6InVzZXJfMngydkdXVEpwNXlCOXVjeXY1b1E0c3BQZG45IiwiaHR0cHM6Ly9zdW5vLmFpL2NsYWltcy9lbWFpbCI6InBibmoxc3puYzJnckBnbWFpbC5jb20iLCJodHRwczovL3N1bm8uYWkvY2xhaW1zL3Bob25lIjpudWxsLCJpYXQiOjE3NDgwNzQxOTQsImlzcyI6Imh0dHBzOi8vY2xlcmsuc3Vuby5jb20iLCJqdGkiOiIwNmVkOWVjYzJhMzE0YjgxYzA0MiIsIm5iZiI6MTc0ODA3NDE4NCwic2lkIjoic2Vzc18yeFg1UndENHVvTVR0Q1JDRWZTOXJydk1GdlIiLCJzdWIiOiJ1c2VyXzJ4MnZHV1RKcDV5Qjl1Y3l2NW9RNHNwUGRuOSJ9.Ztc4AJbbRY6q5KGFx_eTvuaFEDamv7dWT3lfBGI1awQtZX2uvxxz2eirAFJ-SG1dNGVidnBXTGLlD7hcULa5eXu-8I8IqtqkUCkHYn8rAqN-ppdstq8leMnPYnaCNXpT3n22yeNA-z99i7wYL0Id30UvW4BI0JGe46TrYcBW-cfWuHU3klHRCxcYmy_QDqw7g8yIiKQov1ME7yXLemD3f4Fut4V2O6SB8HyCoyWqyKpnh4TN2bCofq4z4mLW5bw1MpyJSK_XVDdbqlD9kjHs-CXnWzwo__08QtXlDJTaUZsoQvJy6slCgCUpGyt1Vfo6uAmf303Y2W-vfrmQxZxPtA",
    "Affiliate-Id": "undefined",
    "Device-Id": "5d054b03-3c82-48dc-813f-7d4e83276e13",
    "Browser-Token": '{"token":"eyJ0aW1lc3RhbXAiOjE3NDgwNzQyMzM5OTh9"}',
    "Origin": "https://suno.com",
    "Dnt": "1",
    "Sec-Gpc": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Priority": "u=4",
    "Te": "trailers",
}

response = hrequests.get(url, headers=headers)

print(response.text)
print(response.status_code)
print(response.headers)
