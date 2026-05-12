import urllib.request, json
url = 'https://api.github.com/repos/microsoft/AirSim/releases/tags/v1.8.1'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        for asset in data.get('assets', []):
            print(f"{asset['name']} : {asset['size'] // (1024*1024)} MB")
except Exception as e:
    print('Error:', e)
