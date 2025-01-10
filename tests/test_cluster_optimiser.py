from spark_cluster_optimiser import cluster_optimiser


def test_cluster_optimiser():
    assert cluster_optimiser(2, 3) == 6
