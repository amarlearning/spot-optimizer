# Spot Optimizer

[![Python Tests](https://github.com/amarlearning/spot-optimizer/actions/workflows/python-tests.yml/badge.svg)](https://github.com/amarlearning/spot-optimizer/actions/workflows/python-tests.yml)

This Python library helps users select the best AWS spot instances based on their resource requirements such as cores, RAM, storage type (SSD), and instance architecture (x86 or ARM). The library optimizes for various use cases, including but not limited to:
- Spark/EMR clusters
- Machine Learning workloads
- Gaming servers
- General compute workloads
- Containerized applications

It allows users to optimize for fewer nodes (low latency), more nodes (fault tolerance), or balanced configurations while selecting instances with the lowest spot interruption rates.

It ensures that the selected configuration meets or exceeds the user's requirements. For example, if you request 20 cores and 100GB of RAM, the library will suggest a configuration with at least those resources, rounding up to the nearest available configuration.

---

## Goals

1. **Ease of Use**: Provide a simple interface to specify resource requirements.
2. **Optimization**: Suggest instance types and counts tailored to user preferences (latency, fault tolerance, or balanced configurations).
3. **Flexibility**: Support various filters such as SSD storage, ARM architecture, and optional EMR version compatibility.
4. **Scalability**: Handle diverse workloads with varying resource needs.
5. **Reliability**: Prioritize instance types with the lowest spot interruption rates.

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

1. **cores (int)**: The total number of CPU cores required by the Spark job.
2. **ram (int)**: The total amount of memory (in GB) required by the Spark job.

### Optional Parameters

1. **ssd\_only (bool)**: If `True`, only suggest instances with SSD-backed storage.
2. **arm\_instances (bool)**: If `True`, include ARM-based instances in the recommendations.
3. **emr\_version (str)**: Optional EMR version to ensure instance compatibility for EMR workloads.
4. **instance\_family (str)**: Filter by specific instance family (e.g., 'm5', 'c6g', etc.).
5. **mode (str)**:
   - **`latency`**: Optimize for fewer, larger nodes (lower latency).
   - **`fault_tolerance`**: Optimize for more, smaller nodes (better fault tolerance).
   - **`balanced`**: Aim for a middle ground between fewer and more nodes.

---

## Future Enhancements

1. **Cost Optimization**:
   - Include estimated instance costs and recommend the most cost-effective configuration.
2. **Custom Instance Pools**:
   - Let users specify a custom list of allowed instance types.
3. **Support for Other Cloud Providers**:
   - Extend the library to support GCP and Azure instance types.
4. **Spot Interruption Rates**:
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

- Updates the instance interruption table only every hour and not the whole data, such as ranges and instance types, since they don't change often.

---

## Issues

If you encounter any bugs, please report them on the [issue tracker](https://github.com/amarlearning/spark-cluster-optimiser/issues).
Alternatively, feel free to [tweet me](https://twitter.com/iamarpandey) if you're having trouble. In fact, you should tweet me anyway.

---

## License

Built with ♥ by Amar Prakash Pandey([@amarlearning](http://github.com/amarlearning)) under Apache License 2.0. 
