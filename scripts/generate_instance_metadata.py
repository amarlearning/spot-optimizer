#!/usr/bin/env python3
import json
import time
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Set
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Silence other loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# Use us-east-1 as primary source for instance metadata
# Rationale: Instance specifications (vCPU, memory, storage type, architecture) are 
# global constants - m5.large has the same specs regardless of region. us-east-1 
# provides the most complete instance catalog as AWS typically launches new instance 
# types here first. Region-specific data like pricing and spot interruption rates 
# are handled separately by other components.
BASE_URL = "https://pricing.us-east-1.amazonaws.com"
PRICING_URL = f"{BASE_URL}/offers/v1.0/aws/AmazonEC2/current/us-east-1/index.json"

# ARM instance type prefixes for faster lookup
ARM_PREFIXES = {"t4g", "m6g", "m7g", "c6g", "c7g", "r6g", "r7g", "x2g", "im4g", "is4g"}

def create_session() -> requests.Session:
    """Create an optimized requests session"""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    return session

def parse_memory(mem_str: str) -> float:
    """Parse memory string to GiB value"""
    if not mem_str:
        return 0.0
    # Extract numeric part more efficiently
    numeric = ''.join(c for c in mem_str.split()[0] if c.isdigit() or c == '.')
    try:
        return float(numeric) if numeric else 0.0
    except ValueError:
        return 0.0

def is_arm_instance(instance_type: str, processor: str) -> bool:
    """Fast ARM detection using prefix matching"""
    prefix = instance_type.split('.')[0] if '.' in instance_type else instance_type
    return prefix in ARM_PREFIXES or 'graviton' in processor.lower()

def fetch_instance_data(session: requests.Session) -> Dict[str, Dict[str, Any]]:
    """Fetch all instance data from us-east-1 pricing API"""
    logger.info("Fetching instance metadata from AWS pricing API...")
    
    try:
        response = session.get(PRICING_URL, timeout=60)
        response.raise_for_status()
        
        logger.info("Parsing pricing data...")
        data = response.json()
        
        instances = {}
        products = data.get('products', {})
        logger.info(f"Processing {len(products)} products...")
        
        # Process in batches for better memory usage
        batch_size = 1000
        processed = 0
        
        for product_id, product in products.items():
            if product.get('productFamily') != 'Compute Instance':
                continue
                
            attrs = product.get('attributes', {})
            
            # Skip if missing critical data
            instance_type = attrs.get('instanceType')
            vcpu_str = attrs.get('vcpu', '')
            memory_str = attrs.get('memory', '')
            
            if not all([instance_type, vcpu_str, memory_str]):
                continue
                
            # Parse vCPU count
            try:
                vcpu = int(vcpu_str)
            except (ValueError, TypeError):
                continue
                
            # Parse memory
            memory = parse_memory(memory_str)
            if memory <= 0:
                continue
            
            # Determine architecture
            processor = attrs.get('physicalProcessor', '')
            arch = "arm64" if is_arm_instance(instance_type, processor) else "x86_64"
            
            # Determine storage type
            storage_info = attrs.get('storage', '').upper()
            storage = "instance" if 'SSD' in storage_info else "ebs"
            
            instances[instance_type] = {
                "arch": arch,
                "vcpu": vcpu,
                "memory": memory,
                "storage": storage
            }
            
            processed += 1
            if processed % batch_size == 0:
                logger.info(f"Processed {processed} instances...")
        
        logger.info(f"Successfully processed {len(instances)} instance types")
        return instances
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch pricing data: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse pricing JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

def validate_instances(instances: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Validate and clean instance data"""
    valid_instances = {}
    
    for instance_type, data in instances.items():
        # Ensure all required fields are present and valid
        if not all([
            data.get('arch') in ['x86_64', 'arm64'],
            isinstance(data.get('vcpu'), int) and data['vcpu'] > 0,
            isinstance(data.get('memory'), (int, float)) and data['memory'] > 0,
            data.get('storage') in ['ebs', 'instance']
        ]):
            continue
            
        valid_instances[instance_type] = data
    
    logger.info(f"Validated {len(valid_instances)} instances")
    return valid_instances

def main():
    """Main execution function"""
    start_time = time.time()
    
    try:
        session = create_session()
        
        # Fetch all instance data from single source
        instances = fetch_instance_data(session)
        
        # Validate the data
        valid_instances = validate_instances(instances)
        
        if not valid_instances:
            logger.error("No valid instances found")
            return
        
        # Save results
        output_path = Path(__file__).parent.parent / "spot_optimizer" / "resources" / "instance_metadata.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(valid_instances, f, indent=2, sort_keys=True)
        
        total_time = time.time() - start_time
        logger.info(f"Successfully saved metadata for {len(valid_instances)} instances in {total_time:.2f}s")
        
        # Print some stats
        arch_counts = {}
        storage_counts = {}
        for data in valid_instances.values():
            arch_counts[data['arch']] = arch_counts.get(data['arch'], 0) + 1
            storage_counts[data['storage']] = storage_counts.get(data['storage'], 0) + 1
        
        logger.info(f"Architecture breakdown: {dict(arch_counts)}")
        logger.info(f"Storage breakdown: {dict(storage_counts)}")
        
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Failed to generate metadata: {e}")
        raise

if __name__ == "__main__":
    main()