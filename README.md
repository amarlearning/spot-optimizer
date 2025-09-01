# Spot Optimizer

[![PyPI version](https://img.shields.io/pypi/v/spot-optimizer.svg)](https://pypi.org/project/spot-optimizer/)
[![Python Tests](https://github.com/amarlearning/spot-optimizer/actions/workflows/python-tests.yml/badge.svg)](https://github.com/amarlearning/spot-optimizer/actions/workflows/python-tests.yml)
[![codecov](https://codecov.io/gh/amarlearning/spot-optimizer/graph/badge.svg?token=3QJ89GFSWC)](https://codecov.io/gh/amarlearning/spot-optimizer)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/spot-optimizer.svg)](https://pypi.org/project/spot-optimizer/)
[![License](https://img.shields.io/:license-Apache%202-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0.txt)
[![PyPI Downloads](https://static.pepy.tech/badge/spot-optimizer)](https://pepy.tech/projects/spot-optimizer)

🚀 Spot Optimizer is a Python library that helps users select the best AWS spot instances based on their resource requirements, including cores, RAM, storage type (SSD), instance architecture (x86 or ARM), AWS region, EMR version compatibility, and instance family preferences. 

It replaces complex, in-house logic for finding the best spot instances with a simple and powerful abstraction. No more manual guesswork — just the right instances at the right time.

## Why Spot Optimizer?
Managing spot instance selection within your codebase can be tedious and error-prone. Spot Optimizer provides a clean, abstracted solution to intelligently select the most stable and cost-effective instances.

### Configuration Guarantee
It ensures that the selected configuration meets or exceeds the user's requirements. For example, if you request 20 cores and 100GB of RAM, the library will suggest a configuration with at least those resources, rounding up to the nearest available configuration.

### Key Benefits
- **💡 Informed Decisions**: Picks instances with the lowest interruption rates and the best fit for your workload.
- **🧠 Dynamic Reliability**: Smartly updates interruption rates every hour to ensure the most stable instance selection.
- **🛠️ Operational Efficiency**: No more homegrown scripts or complex logic — just plug and play.
- **⚡ High Performance**: DuckDB-powered analytics with 98.4% test coverage and 5.4ms average response time.
- **🏗️ Scalable and Reliable**: Automatically adjusts to changing resource needs while minimizing downtime.

---

## Spot Optimizer vs AWS EC2 Fleet

### How They Differ

**Spot Optimizer** is a **decision-making tool** that helps you choose the optimal instance types before launching, while **AWS EC2 Fleet** is a **provisioning service** that launches and manages the actual instances.

| Aspect | Spot Optimizer | AWS EC2 Fleet |
|--------|----------------|---------------|
| **Purpose** | Instance type selection & optimization | Instance provisioning & management |
| **When to Use** | Before launching instances | When launching instances |
| **Output** | Recommended instance types & counts | Running EC2 instances |
| **Focus** | Interruption rates, resource fit, cost optimization | Capacity fulfillment, diversification |
| **Scope** | Analysis and recommendations | Infrastructure deployment |

### How They Work Together

**Perfect Complementary Workflow:**

```python
# Step 1: Use Spot Optimizer to find the best instance types
from spot_optimizer import optimize

result = optimize(cores=64, memory=256, region="us-east-1", mode="fault_tolerance")
# Output: {"instances": {"type": "m5.4xlarge", "count": 4}, ...}

# Step 2: Use the recommendations with AWS EC2 Fleet
import boto3

ec2 = boto3.client('ec2')
response = ec2.create_fleet(
    LaunchTemplateConfigs=[
        {
            'LaunchTemplateSpecification': {
                'LaunchTemplateName': 'my-template',
                'Version': '1'
            },
            'Overrides': [
                {
                    'InstanceType': result['instances']['type'],  # m5.4xlarge
                    'AvailabilityZone': 'us-east-1a',
                }
            ]
        }
    ],
    TargetCapacitySpecification={
        'TotalTargetCapacity': result['instances']['count'],  # 4
        'DefaultTargetCapacityType': 'spot'
    }
)
```

### Use Cases for Each

**Use Spot Optimizer when:**
- Planning infrastructure for new workloads
- Optimizing existing deployments for cost/stability
- Analyzing instance options across regions
- Building infrastructure-as-code templates
- Integrating spot instance logic into applications

**Use AWS EC2 Fleet when:**
- Actually launching the recommended instances
- Managing instance lifecycle and replacement
- Handling spot interruptions automatically
- Scaling capacity up/down dynamically
- Diversifying across multiple instance types/AZs

### Integration Benefits

1. **Smarter Fleet Configurations**: Use Spot Optimizer's recommendations to configure more effective EC2 Fleet launch templates
2. **Reduced Trial and Error**: Skip the guesswork of which instance types to include in your fleet
3. **Better Cost Optimization**: Combine Spot Optimizer's interruption rate analysis with Fleet's diversification
4. **Improved Reliability**: Use fault-tolerance mode recommendations for mission-critical Fleet deployments

---

## Installation

### For Users
```bash
pip install spot-optimizer
```

### For Development
```bash
# Clone the repository
git clone git@github.com:amarlearning/spot-optimizer.git
cd spot-optimizer

# Install dependencies and set up development environment
make install
```

---

## Usage

### API Usage

```python
from spot_optimizer import optimize

# Basic usage
result = optimize(cores=8, memory=32)

# Advanced usage with all options
result = optimize(
    cores=8,
    memory=32,
    region="us-east-1",
    ssd_only=True,
    arm_instances=False,
    instance_family=["m6i", "r6i"],
    mode="balanced"
)

# Enhanced output with reliability metrics
{
   "instances": {
      "type": "m6i.2xlarge",
      "count": 1
   },
   "mode": "balanced",
   "total_cores": 8,
   "total_ram": 32,
   "reliability": {
      "spot_score": 0.85,
      "interruption_rate": "< 5%"
   }
}
```

### CLI Usage

```bash
# Basic usage
spot-optimizer --cores 8 --memory 32

# Advanced usage
spot-optimizer \
    --cores 8 \
    --memory 32 \
    --region us-east-1 \
    --ssd-only \
    --no-arm \
    --instance-family m6i r6i \
    --mode balanced

# Get help
spot-optimizer --help
```

---

## Inputs

### Required Parameters

1. **cores (int)**: The total number of CPU cores required.
2. **memory (int)**: The total amount of memory required in GB.

### Optional Parameters

1. **region (str)**: AWS region for spot instance selection (default: "us-west-2").
2. **ssd_only (bool)**: If `True`, only suggest instances with SSD-backed storage (default: False).
3. **arm_instances (bool)**: If `True`, include ARM-based instances (default: True).
4. **instance_family (List[str])**: Filter by specific instance families (e.g., ['m6i', 'r6i']).
5. **emr_version (str)**: Optional EMR version to ensure instance compatibility.
6. **mode (str)**:
   - **`latency`**: Optimize for fewer, larger nodes (lower latency).
   - **`fault_tolerance`**: Optimize for more, smaller nodes (better fault tolerance).
   - **`balanced`**: Aim for a middle ground between fewer and more nodes.

---

## Development

### Make Commands

```bash
# Install dependencies
make install

# Run all tests (unit + integration)
make test

# Run only unit tests
make test-unit

# Check test coverage
make coverage

# Clean up build artifacts
make clean
```

---

## Performance Optimizations

- Efficiently updates the instance interruption table only every hour, avoiding unnecessary data fetches.
- Focuses on providing the most stable instances based on the latest interruption rate data.
- DuckDB-powered analytics with average 5.4ms query response time.

---

## Future Enhancements

1. **Cost Optimization**:
   - Include estimated instance costs and recommend the most cost-effective configuration.
2. **Support for Other Cloud Providers**:
   - Extend the library to support GCP and Azure instance types.
3. **Advanced Analytics**:
   - Historical interruption pattern analysis and predictive modeling.

---

## Issues

If you encounter any bugs, please report them on the [issue tracker](https://github.com/amarlearning/spot-optimizer/issues).
Alternatively, feel free to [tweet me](https://twitter.com/iamarpandey) if you're having trouble. In fact, you should tweet me anyway.

---

## License

Built with ♥ by Amar Prakash Pandey([@amarlearning](http://github.com/amarlearning)) under Apache License 2.0.