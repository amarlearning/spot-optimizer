import requests
from bs4 import BeautifulSoup
import json
import logging
from pathlib import Path
from typing import Dict, Any
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstanceMetadataGenerator:
    def __init__(self):
        self.url = "https://aws.amazon.com/ec2/instance-types/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.output_path = Path(__file__).parent.parent / "spot_optimizer" / "resources" / "instance_metadata.json"

    def fetch_page(self) -> str:
        try:
            response = requests.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch AWS instance types page: {e}")
            sys.exit(1)

    def determine_architecture(self, instance_type: str) -> str:
        # More accurate architecture detection
        if any(x in instance_type.lower() for x in ['a1', 'c6g', 'm6g', 'r6g', 't4g']):
            return "arm64"
        return "x86_64"

    def determine_storage_type(self, storage_info: str) -> str:
        storage_info = storage_info.lower()
        if any(x in storage_info for x in ['nvme', 'ssd']):
            return "ssd"
        return "ebs"

    def parse_instance_data(self, html: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        instances = {}
        
        for section in soup.find_all("tr"):
            cells = section.find_all('td')
            if len(cells) < 6:
                continue

            instance_type = cells[0].text.strip()
            if any(x in instance_type for x in ["Instance Size", "Size", "Type"]):
                continue

            try:
                vcpu = int(cells[1].text.strip().replace("*", ""))
                memory = float(cells[2].text.strip().replace(",", ""))
                storage = cells[3].text.strip()
            except (ValueError, IndexError) as e:
                logger.warning(f"Skipping row due to parsing error: {e}")
                continue

            instances[instance_type] = {
                "arch": self.determine_architecture(instance_type),
                "storage": self.determine_storage_type(storage),
                "vcpu": vcpu,
                "memory": memory
            }

        return instances

    def validate_data(self, instances: Dict[str, Any]) -> bool:
        if not instances:
            logger.error("No instances found!")
            return False

        # Basic validation checks
        for instance, data in instances.items():
            if not all(k in data for k in ["arch", "storage", "vcpu", "memory"]):
                logger.error(f"Missing required fields in instance {instance}")
                return False
            if data["vcpu"] <= 0 or data["memory"] <= 0:
                logger.error(f"Invalid resource values for instance {instance}")
                return False

        return True

    def save_metadata(self, instances: Dict[str, Any]) -> None:
        try:
            # Create parent directories if they don't exist
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with consistent formatting
            with self.output_path.open('w') as f:
                json.dump(instances, f, indent=4, sort_keys=True)
            
            logger.info(f"Successfully saved metadata for {len(instances)} instances")
        except IOError as e:
            logger.error(f"Failed to save metadata: {e}")
            sys.exit(1)

    def run(self) -> None:
        logger.info("Starting instance metadata generation...")
        html = self.fetch_page()
        instances = self.parse_instance_data(html)
        
        if self.validate_data(instances):
            self.save_metadata(instances)
            logger.info("Instance metadata generation completed successfully")
        else:
            logger.error("Data validation failed")
            sys.exit(1)

if __name__ == "__main__":
    generator = InstanceMetadataGenerator()
    generator.run()
