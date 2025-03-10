# Spot Optimizer

[![Python Tests](https://github.com/amarlearning/spot-optimizer/actions/workflows/python-tests.yml/badge.svg)](https://github.com/amarlearning/spot-optimizer/actions/workflows/python-tests.yml)

🚀 Spot Optimizer is a Python library that helps users select the best AWS spot instances based on their resource requirements, including cores, RAM, storage type (SSD), instance architecture (x86 or ARM), AWS region, EMR version compatibility, and instance family preferences. 

It replaces complex, in-house logic for finding the best spot instances with a simple and powerful abstraction. No more manual guesswork — just the right instances at the right time. 

## Why Spot Optimizer?
Managing spot instance selection within your codebase can be tedious and error-prone. Spot Optimizer provides a clean, abstracted solution to intelligently select the most stable and cost-effective instances.

### Configuration Guarantee
It ensures that the selected configuration meets or exceeds the user's requirements. For example, if you request 20 cores and 100GB of RAM, the library will suggest a configuration with at least those resources, rounding up to the nearest available configuration.

---

## Key Benefits
- **💡 Informed Decisions**: Picks instances with the lowest interruption rates and the best fit for your workload.
- **🧠 Dynamic Reliability**: Smartly updates interruption rates every hour to ensure the most stable instance selection.
- **🛠️ Operational Efficiency**: No more homegrown scripts or complex logic — just plug and play.
- **⚡ High Flexibility**: Supports diverse use cases like Spark/EMR clusters, ML workloads, gaming servers, and more.
- **🏗️ Scalable and Reliable**: Automatically adjusts to changing resource needs while minimizing downtime.

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

print(result)
# Output:
# {
#     "instances": {
#         "type": "m6i.2xlarge",
#         "count": 1
#     },
#     "mode": "balanced",
#     "total_cores": 8,
#     "total_ram": 32
# }
```

### CLI Usage

```bash
# Basic usage
spot-optimizer optimize --cores 8 --memory 32

# Advanced usage
spot-optimizer optimize \
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

## Future Enhancements

1. **Cost Optimization**:
   - Include estimated instance costs and recommend the most cost-effective configuration.
2. **Support for Other Cloud Providers**:
   - Extend the library to support GCP and Azure instance types.
3. **Spot Interruption Rates**:
   - Include interruption rates in the selection criteria for spot instances.

---

## Development

### Make Commands

```bash
# Install dependencies
make install

# Run tests
make test

# Check test coverage
make coverage

# Clean up build artifacts
make clean
```

---

# Performance Optimisations

- Efficiently updates the instance interruption table only every hour, avoiding unnecessary data fetches.
- Focuses on providing the most stable instances based on the latest interruption rate data.

---

## Issues

If you encounter any bugs, please report them on the [issue tracker](https://github.com/amarlearning/spark-cluster-optimiser/issues).
Alternatively, feel free to [tweet me](https://twitter.com/iamarpandey) if you're having trouble. In fact, you should tweet me anyway.

---

## License

Built with ♥ by Amar Prakash Pandey([@amarlearning](http://github.com/amarlearning)) under Apache License 2.0. 
