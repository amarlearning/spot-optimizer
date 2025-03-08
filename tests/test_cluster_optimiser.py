from spot_optimizer.spot_instance_optimizer import cluster_optimiser


def test_cluster_optimiser():
    assert cluster_optimiser(cores=80, memory=512) == {
        "instances": {
            "type": "m6id.32xlarge",
            "count": 1
        },
        "mode": "balanced",
        "total_cores": 128,
        "total_ram": 512
    }
