# Spark Cluster Optimiser

## Overview

This Python library helps users select the best AWS EMR instance configurations for their Spark jobs based on resource requirements such as cores, RAM, storage type (SSD), instance architecture (x86 or ARM), and EMR version compatibility. The library also allows users to optimize for fewer nodes (low latency), more nodes (fault tolerance), or balanced configurations, while selecting instances with the lowest spot interruption rates.

It ensures that the selected configuration meets or exceeds the user’s requirements. For example, if you request 20 cores and 100GB of RAM, the library will suggest a configuration with at least those resources, rounding up to the nearest available configuration.

---

## Goals

1. **Ease of Use**: Provide a simple interface to specify job requirements.
2. **Optimization**: Suggest instance types and counts tailored to user preferences (latency, fault tolerance, or balanced configurations).
3. **Flexibility**: Support various filters such as SSD storage, ARM architecture, and EMR version compatibility.
4. **Scalability**: Handle diverse Spark workloads with varying resource needs.
5. **Reliability**: Prioritize instance types with the lowest spot interruption rates.

---

## Function Signature

```python
result = cluster_optimiser(
    cores: int,              # Total number of cores required
    ram: int,                # Total amount of RAM required (in GB)
    ssd_only: bool,          # Filter for SSD-backed instances
    arm_instances: bool,     # Include ARM-based instances if True
    emr_version: str,        # EMR version compatibility filter (e.g., "6.10.0")
    mode: str = "latency"    # Optimization mode: "latency", "fault_tolerance", or "balanced"
)
```

---

## Inputs

### Required Parameters

1. **cores (int)**: The total number of CPU cores required by the Spark job.
2. **ram (int)**: The total amount of memory (in GB) required by the Spark job.

### Optional Parameters

1. **ssd\_only (bool)**: If `True`, only suggest instances with SSD-backed storage.
2. **arm\_instances (bool)**: If `True`, include ARM-based instances in the recommendations.
3. **emr\_version (str)**: The EMR version to ensure instance compatibility.
4. **mode (str)**:
   - **`latency`**: Optimize for fewer, larger nodes (lower latency).
   - **`fault_tolerance`**: Optimize for more, smaller nodes (better fault tolerance).
   - **`balanced`**: Aim for a middle ground between fewer nodes and more nodes.

---

## Outputs

The function returns a dictionary containing the suggested instance type, node count, and additional metadata.

### Example Output

#### Case 1: `mode="latency"`

```json
{
  "instances": {
    "type": "r5.8xlarge",   # Suggested instance type
    "count": 5               # Number of instances needed
  },
  "mode": "latency",         # Optimization mode used
  "total_cores": 80,          # Total cores available in the cluster
  "total_ram": 512            # Total RAM available in the cluster (in GB)
}
```

#### Case 2: `mode="fault_tolerance"`

```json
{
  "instances": {
    "type": "r5.xlarge",    # Suggested instance type
    "count": 40              # Number of instances needed
  },
  "mode": "fault_tolerance", # Optimization mode used
  "total_cores": 80,          # Total cores available in the cluster
  "total_ram": 480            # Total RAM available in the cluster (in GB)
}
```

#### Case 3: `mode="balanced"`

```json
{
  "instances": {
    "type": "r5.4xlarge",   # Suggested instance type
    "count": 10              # Number of instances needed
  },
  "mode": "balanced",        # Optimization mode used
  "total_cores": 80,          # Total cores available in the cluster
  "total_ram": 512            # Total RAM available in the cluster (in GB)
}
```

#### Error Case: No Suitable Instances Found

```json
{
  "error": "No suitable instance type found."
}
```

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

## Issues

If you encounter any bugs, please report them on the [issue tracker](https://github.com/amarlearning/spark-cluster-optimiser/issues).
Alternatively, feel free to [tweet me](https://twitter.com/iamarpandey) if you're having trouble. In fact, you should tweet me anyway.

---

## License

Built with ♥ by Amar Prakash Pandey([@amarlearning](http://github.com/amarlearning)) under Apache License 2.0. 
