"""SQL query builder for spot instance optimization."""

from typing import List, Optional, Tuple


class OptimizationQueryBuilder:
    """Builds SQL queries for spot instance optimization."""
    
    @staticmethod
    def build_optimization_query(
        ssd_only: bool = False,
        arm_instances: bool = True,
        instance_family: Optional[List[str]] = None
    ) -> str:
        """
        Build the main optimization query with filters.
        
        Args:
            ssd_only: Whether to filter for SSD-only instances
            arm_instances: Whether to include ARM instances
            instance_family: List of instance families to filter by
            
        Returns:
            str: Complete SQL query with placeholders
        """
        # Build filter conditions
        storage_filter = "AND i.storage_type = 'instance'" if ssd_only else ""
        arch_filter = "AND i.architecture != 'arm64'" if not arm_instances else ""
        
        family_filter = ""
        if instance_family:
            placeholders = ','.join(['?' for _ in instance_family])
            family_filter = f"AND i.instance_family IN ({placeholders})"
        
        query = f"""
            WITH ranked_instances AS (
                SELECT 
                    i.instance_type,
                    i.cores,
                    i.ram_gb,
                    s.s as spot_score,
                    s.r as interruption_rate,
                    GREATEST(
                        CEIL(CAST(? AS FLOAT) / i.cores),
                        CEIL(CAST(? AS FLOAT) / i.ram_gb)
                    ) as instances_needed
                FROM instance_types i
                JOIN spot_advisor s ON i.instance_type = s.instance_types
                WHERE 
                    s.region = ?
                    AND s.os = 'Linux'
                    {storage_filter}
                    {arch_filter}
                    {family_filter}
            )
            SELECT 
                *,
                cores * instances_needed as total_cores,
                ram_gb * instances_needed as total_memory,
                ((cores * instances_needed) - ?) * 100.0 / ? as cpu_waste_pct,
                ((ram_gb * instances_needed) - ?) * 100.0 / ? as memory_waste_pct
            FROM ranked_instances
            WHERE 
                total_cores >= ?
                AND total_memory >= ?
                AND instances_needed BETWEEN ? AND ?  -- Apply mode-specific instance bounds
            ORDER BY 
                interruption_rate ASC,
                spot_score DESC,
                (cpu_waste_pct + memory_waste_pct) ASC
            LIMIT 1
        """
        
        return query
    
    @staticmethod
    def build_query_parameters(
        cores: int,
        memory: int,
        region: str,
        instance_family: Optional[List[str]],
        min_instances: int,
        max_instances: int
    ) -> List:
        """
        Build the parameter list for the optimization query.
        
        Args:
            cores: Number of CPU cores required
            memory: Amount of RAM required (in GB)
            region: AWS region
            instance_family: List of instance families to filter by
            min_instances: Minimum number of instances (from mode)
            max_instances: Maximum number of instances (from mode)
            
        Returns:
            List: Parameters in the correct order for the query
        """
        # Build parameters in the correct order for the query
        params = [
            cores, memory, region,  # Basic params for instances_needed calculation and region filter
        ]
        
        # Add instance family parameters if specified
        if instance_family:
            params.extend(instance_family)
        
        # Add remaining parameters for the main query
        params.extend([
            cores, cores,           # CPU waste calculation
            memory, memory,         # Memory waste calculation
            cores, memory,          # Minimum resource requirements
            int(min_instances), int(max_instances)  # Mode-specific instance bounds
        ])
        
        return params
    
    @staticmethod
    def build_error_message_params(
        cores: int,
        memory: int,
        region: str,
        mode: str,
        instance_family: Optional[List[str]] = None,
        emr_version: Optional[str] = None,
        ssd_only: bool = False,
        arm_instances: bool = True
    ) -> str:
        """
        Build error message parameters for when no instances are found.
        
        Args:
            cores: Number of CPU cores required
            memory: Amount of RAM required (in GB)
            region: AWS region
            mode: Optimization mode
            instance_family: List of instance families to filter by
            emr_version: EMR version if specified
            ssd_only: Whether SSD-only filter is applied
            arm_instances: Whether ARM instances are included
            
        Returns:
            str: Formatted error message
        """
        params = []
        params.append(f"cpu = {cores}")
        params.append(f"memory = {memory}")
        params.append(f"region = {region}")
        params.append(f"mode = {mode}")
        
        if instance_family:
            params.append(f"instance_family = {instance_family}")
        if emr_version:
            params.append(f"emr_version = {emr_version}")
        if ssd_only:
            params.append("ssd_only = True")
        if not arm_instances: 
            params.append("arm_instances = False")
        
        return "No suitable instances found matching for " + " and ".join(params)