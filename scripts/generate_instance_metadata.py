#!/usr/bin/env python3
import json
import time
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, List, Tuple
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

# Constants
BASE_URL = "https://pricing.us-east-1.amazonaws.com"
PRICING_INDEX = f"{BASE_URL}/offers/v1.0/aws/AmazonEC2/current/region_index.json"

# AWS regions to process
AWS_REGIONS = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2",
    "ap-south-1", "ca-central-1", "sa-east-1"
]

# ARM processor identifiers
ARM_IDENTIFIERS = [
    "graviton",  # For processor name
    "t4g", "m6g", "m7g", "c6g", "c7g", "r6g", "r7g"  # For instance types
]

def create_session() -> requests.Session:
    """Create an optimized requests session"""
    session = requests.Session()
    retries = Retry(
        total=5,  # More retries
        backoff_factor=0.1,  # Faster retry
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=False  # Don't wait for retry-after
    )
    # Larger connection pools and longer timeouts
    adapter = HTTPAdapter(
        max_retries=retries,
        pool_connections=50,
        pool_maxsize=50,
        pool_block=False
    )
    session.mount("https://", adapter)
    return session

def parse_memory(mem_str: str) -> float:
    """Parse memory string to GiB value"""
    try:
        return float(''.join(c for c in mem_str if c.isdigit() or c == '.'))
    except (ValueError, TypeError):
        return 0.0

def get_region_urls() -> Dict[str, str]:
    """Get pricing URLs for all regions"""
    try:
        response = session.get(PRICING_INDEX, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        urls = {}
        for region in AWS_REGIONS:
            region_data = data.get('regions', {}).get(region, {})
            if region_data and 'currentVersionUrl' in region_data:
                urls[region] = f"{BASE_URL}{region_data['currentVersionUrl']}"
        
        logger.info(f"Found pricing URLs for {len(urls)} regions")
        return urls
    except Exception as e:
        logger.error(f"Failed to fetch region index: {e}")
        raise

def process_region(region: str, url: str) -> Tuple[str, Dict[str, Dict[str, Any]]]:
    """Process a single region's instance data"""
    start_time = time.time()
    instances = {}
    product_count = 0
    
    try:
        # Download data in binary mode
        response = session.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Read all data and decode once
        raw_data = response.content.decode('utf-8')
        
        # Parse JSON
        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in {region} at position {e.pos}: {e.msg}")
            logger.debug(f"Raw data snippet around error: {raw_data[max(0, e.pos-100):e.pos+100]}")
            raise
        
        # Process compute instances
        for product in data.get('products', {}).values():
            product_count += 1
            if product_count % 5000 == 0:
                logger.debug(f"Processed {product_count} products in {region}")
                
            if product.get('productFamily') != 'Compute Instance':
                continue
                
            attrs = product.get('attributes', {})
            itype = attrs.get('instanceType')
            if not itype:
                continue
                
            # Quick check for required fields
            vcpu = attrs.get('vcpu', '')
            if not vcpu.isdigit():
                continue
            
            # Efficient architecture check
            proc_info = attrs.get('physicalProcessor', '').lower()
            is_arm = any(arm in proc_info or arm in itype.lower() for arm in ARM_IDENTIFIERS)
            
            instances[itype] = {
                "arch": "arm64" if is_arm else "x86_64",
                "vcpu": int(vcpu),
                "memory": parse_memory(attrs.get('memory', '0')),
                "storage": "instance" if 'SSD' in attrs.get('storage', '') else "ebs"
            }
        
        process_time = time.time() - start_time
        logger.info(f"Processed {region} in {process_time:.2f}s ({len(instances)} instances from {product_count} products)")
        return region, instances
        
    except requests.exceptions.ReadTimeout:
        logger.error(f"Timeout reading data from {region}")
        return region, {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {region}: {e}")
        return region, {}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {region}: {e}")
        return region, {}
    except Exception as e:
        logger.error(f"Unexpected error processing {region}: {str(e)}")
        return region, {}

def merge_instance_data(region_data: List[Tuple[str, Dict[str, Dict[str, Any]]]]) -> Dict[str, Dict[str, Any]]:
    """Merge instance data from all regions"""
    merged = {}
    for region, instances in region_data:
        for itype, data in instances.items():
            if itype not in merged:
                merged[itype] = data
            else:
                # Fill in any missing data
                for key, value in data.items():
                    if not merged[itype].get(key) and value:
                        merged[itype][key] = value
    return merged

def process_regions_batch(regions_batch, session):
    """Process a batch of regions with shared session"""
    results = []
    for region, url in regions_batch:
        try:
            result = process_region(region, url)
            results.append(result)
        except Exception as e:
            logger.error(f"Batch processing failed for {region}: {e}")
    return results

def main():
    try:
        global session
        session = create_session()
        
        # Get region URLs
        region_urls = get_region_urls()
        if not region_urls:
            logger.error("No region URLs found")
            return
            
        # Convert to list for batching
        regions = list(region_urls.items())
        
        # Process regions sequentially with timeout protection
        results = []
        with tqdm(total=len(regions), desc="Processing regions") as pbar:
            for region, url in regions:
                logger.info(f"Processing {region}")
                
                try:
                    # Set a strict timeout for each region
                    with ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(process_region, region, url)
                        try:
                            result = future.result(timeout=60)  # 60 second timeout per region
                            results.append(result)
                            pbar.set_postfix_str(f"Success: {region}")
                        except TimeoutError:
                            logger.error(f"Timeout processing {region}")
                            results.append((region, {}))
                            pbar.set_postfix_str(f"Timeout: {region}")
                        except Exception as e:
                            logger.error(f"Failed to process {region}: {e}")
                            results.append((region, {}))
                            pbar.set_postfix_str(f"Failed: {region}")
                except Exception as e:
                    logger.error(f"Executor failed for {region}: {e}")
                    results.append((region, {}))
                    pbar.set_postfix_str(f"Failed: {region}")
                
                pbar.update(1)
                
                # Small delay between regions
                if region != regions[-1][0]:  # If not the last region
                    time.sleep(1)
        
        # Merge and validate data
        merged_data = merge_instance_data(results)
        
        # Filter incomplete entries
        final_data = {
            k: v for k, v in merged_data.items()
            if all(v.get(f) for f in ["arch", "vcpu", "memory", "storage"])
        }
        
        # Save results
        output_path = Path(__file__).parent.parent / "spot_optimizer" / "resources" / "instance_metadata.json"
        with open(output_path, 'w') as f:
            json.dump(final_data, f, indent=2, sort_keys=True)
            
        logger.info(f"Successfully saved metadata for {len(final_data)} instances")
        
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
    except Exception as e:
        logger.error(f"Failed to generate metadata: {e}")
        raise

if __name__ == "__main__":
    main()