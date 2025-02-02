import os
import docker
import re
from adguardhome import AdGuardHome
import traceback

stack_dns_map = {}
adguard = None
dns_answer = os.environ['ADGUARD_ANSWER']
adguard_host = os.environ['ADGUARD_HOST']
adguard_username = os.environ['ADGUARD_USERNAME']
adguard_password = os.environ['ADGUARD_PASSWORD']

def poll_existing_services():
  try:
    # Initialize Docker client
    docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    print("Polling existing services...")
    # Get a list of all services
    services = docker_client.services.list()

    for service in services:
      service_name = service.attrs.get('Spec', {}).get('Name', 'Unknown')
      labels = service.attrs.get('Spec', {}).get('Labels', {})
      print(service_name)

      if labels:
        for key, value in labels.items():
          if re.match(r"traefik\.http\.routers\..*\.rule", key):
            match = re.search(r"Host\(`(.+?)`\)", value)
            if not match:
              continue
            stack_dns_map[service_name] = match.group(1)
            if match.group(1) == dns_answer:
                continue
            adguard.create_dns(match.group(1), dns_answer)

    print(stack_dns_map)

  except Exception as e:
    print(f"Error polling existing services: {e}")

def listen_to_events():
  try:
    # Initialize Docker client
    client = docker.APIClient(base_url='unix://var/run/docker.sock')
    docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    # Listen to Docker events
    for event in client.events(decode=True):
      if event.get('Type') == 'service':
        action = event.get('Action', 'unknown')
        actor = event.get('Actor', {})
        service_name = actor.get('Attributes', {}).get('name', 'unknown')
  
        print(f"Service Event: {action}")
        print(f"  Service Name: {service_name}")

        if action == 'create' or action == 'update':

          service_id = actor.get('ID', 'unknown')
          try:
            # Fetch service details to get labels
            service = docker_client.services.get(service_id)
            labels = service.attrs.get('Spec', {}).get('Labels', {})
  
            if not labels:
              continue
            for key, value in labels.items():
              if re.match(r"traefik\.http\.routers\..*\.rule", key):
                match = re.search(r"Host\(`(.+?)`\)", value)
                if not match:
                  continue
                stack_dns_map[service_name] = match.group(1)
                if match.group(1) == dns_answer:
                  continue
                adguard.create_dns(match.group(1), dns_answer)
          except Exception as e:
            print(f"  Error fetching service details: {e}")

        elif action == 'remove':
          dns = stack_dns_map.pop(service_name, None)
          print(dns)
          if dns:
            adguard.delete_dns(dns)
            
        print(stack_dns_map)
        print("-")  # Separator for readability

  except Exception as e:
    print(f"Error listening to Docker events: {e}")

if __name__ == "__main__":
  print("Starting...")
  adguard = AdGuardHome(adguard_host, adguard_username, adguard_password)
  print("Polling existing services...")
  poll_existing_services()
  print("Listening for Docker service events...")
  listen_to_events()

