import requests
import json

from requests.auth import HTTPBasicAuth

class AdGuardHome:
  def __init__(self, host, username, password):
    self.host = host
    self.session = requests.Session()
    self.session.auth = (username, password)

  def search_dns(self, domain):
    r = self.session.get('{}/control/rewrite/list'.format(self.host))
    rewrites = json.loads(r.text)
    rewrites = [ rewrite for rewrite in rewrites if rewrite['domain'] == domain]
    return rewrites

  def create_dns(self, domain, answer):
    rewrites = self.search_dns(domain)
    print(rewrites)
  
    if len(rewrites) == 0:
      print("Create")
      data = {
        "domain": domain,
        "answer": answer
      }
      r = self.session.post('{}/control/rewrite/add'.format(self.host), json=data)
      print(r.status_code)
    else:
      rewrite = rewrites[0]
      if rewrite['answer'] != answer:
        print("Update")
        data = {
          "target": {
            "domain": domain,
            "answer": rewrite['answer'],
          },
          "update": {
            "domain": domain,
            "answer": answer
          }
        }
        r = self.session.put('{}/control/rewrite/update'.format(self.host), json=data)
        print(r.status_code)

  def delete_dns(self, domain):
    rewrites = self.search_dns(domain)
    print("Delete")
    for rewrite in rewrites:
      data = {
        "domain": domain,
        "answer": rewrite['answer']
      }
      r = self.session.post('{}/control/rewrite/delete'.format(self.host), json=data)
      print(r.status_code)
