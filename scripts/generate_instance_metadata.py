import requests
from bs4 import BeautifulSoup
import json

def scrape_aws_instances():
    url = "https://aws.amazon.com/ec2/instance-types/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    instances = {}
    
    # Locate the container holding instance details
    instance_sections = soup.find_all("tr")
    
    for section in instance_sections:
        cells = section.find_all('td')
        if len(cells) < 6:  # Skip invalid rows
            continue
            
        instance_type = cells[0].text.strip()
        if any(x in instance_type for x in ["Instance Size", "Size", "Type"]):
            continue
            
        try:
            vcpu = int(cells[1].text.strip().replace("*", ""))
            memory = float(cells[2].text.strip())
        except ValueError:
            continue
    
        storage = cells[3].text.strip()
        storage_type = "ssd" if "SSD" in storage else "ebs"
        arch = "arm64" if "g" in instance_type else "x86_64"
            
        # Simple storage type check
        storage_type = "ssd" if "SSD" in storage else "ebs"
        # Simple arch check
        arch = "arm64" if "g" in instance_type else "x86_64"
        
        instances[instance_type] = {
            "arch": arch,
            "storage": storage_type,
            "vcpu": vcpu,
            "memory": memory
        }
        
    # Save to JSON
    with open("spot_optimizer/resources/instance_metadata.json", "w") as f:
        json.dump(instances, f, indent=4)
    
    print(f"Extracted {len(instances)} AWS instance types. Data saved to instance_metadata.json.")

if __name__ == "__main__":
    scrape_aws_instances()
