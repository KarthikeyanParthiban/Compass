import requests

def get_groww_holdings(token):
    url = "https://api.groww.in/v1/holdings/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-API-VERSION": "1.0",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"

# Replace with your actual token
ACCESS_TOKEN = "eyJraWQiOiJaTUtjVXciLCJhbGciOiJFUzI1NiJ9.eyJleHAiOjE3NzY5MDQyMDAsImlhdCI6MTc3NjgzODY0NiwibmJmIjoxNzc2ODM4NjQ2LCJzdWIiOiJ7XCJ0b2tlblJlZklkXCI6XCJlNGZlZjU5Ny02MDFmLTQxNmUtYjczMC0xMjU0MDViMjdiZjlcIixcInZlbmRvckludGVncmF0aW9uS2V5XCI6XCJlMzFmZjIzYjA4NmI0MDZjODg3NGIyZjZkODQ5NTMxM1wiLFwidXNlckFjY291bnRJZFwiOlwiYzNlZWNiZGItZGU0MS00MzJmLThiYzgtMjc3ZDI0MmQ5NWNjXCIsXCJkZXZpY2VJZFwiOlwiMjBjYzdiNzgtZjNkNS01YjRhLThiZWUtYmZjMzY1ZjhhMDI3XCIsXCJzZXNzaW9uSWRcIjpcIjk3Mzc1Nzc2LWI3NjktNGM3NC04NWM0LTQ4NGViYzU5OTg3YlwiLFwiYWRkaXRpb25hbERhdGFcIjpcIno1NC9NZzltdjE2WXdmb0gvS0EwYkM4RzlLVURYRGJObE9zVXVBY1gwQWRSTkczdTlLa2pWZDNoWjU1ZStNZERhWXBOVi9UOUxIRmtQejFFQisybTdRPT1cIixcInJvbGVcIjpcIm9yZGVyLWJhc2ljLGxpdmVfZGF0YS1iYXNpYyxub25fdHJhZGluZy1iYXNpYyxvcmRlcl9yZWFkX29ubHktYmFzaWMsYmFja190ZXN0XCIsXCJzb3VyY2VJcEFkZHJlc3NcIjpcIjI0MDk6NDBmNDoxMzphNGQ6NDAwMTo4NDc6YmM3ODo5MTAsMTcyLjcwLjIxOS4yMjAsMzUuMjQxLjIzLjEyM1wiLFwidHdvRmFFeHBpcnlUc1wiOjE3NzY5MDQyMDAwMDAsXCJ2ZW5kb3JOYW1lXCI6XCJncm93d0FwaVwifSIsImlzcyI6ImFwZXgtYXV0aC1wcm9kLWFwcCJ9.j1XEPz3J8jqXaTfYcc-o3DsIRHlLGKmhzlU6dHUe-0oT0-ApJswK2hpq8JggZM3kzLuy_qzvwJDzYGn7ZKxg4g"

if __name__ == "__main__":
    holdings = get_groww_holdings(ACCESS_TOKEN)
    print(holdings)
