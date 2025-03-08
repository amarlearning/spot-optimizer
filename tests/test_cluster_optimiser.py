from spot_optimizer import cluster_optimiser


def test_cluster_optimiser():
    assert cluster_optimiser(cores=80, memory=512) == {
        "instances": {
            "type": "r5.8xlarge",
            "count": 5
        },
        "mode": "latency",
        "total_cores": 80,
        "total_ram": 512
    }
