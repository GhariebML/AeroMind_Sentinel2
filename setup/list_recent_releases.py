import urllib.request, json
url = 'https://api.github.com/repos/microsoft/AirSim/releases'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        for release in data[:5]:
            print(release['tag_name'])
            for asset in release.get('assets', []):
                print(f"  {asset['name']} : {asset['size'] // (1024*1024)} MB")
except Exception as e:
    print('Error:', e)
