from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class GPU:
    gpu_id: int
    total_memory: int  # GB
    available_memory: int
    utilization: float  # 0-100
    allocated_to: Optional[str] = None

class ResourceScheduler:
    """GPU resource scheduler with bin-packing"""
    
    def __init__(self, num_gpus: int = 4, memory_per_gpu: int = 16):
        self.gpus = [
            GPU(
                gpu_id=i,
                total_memory=memory_per_gpu,
                available_memory=memory_per_gpu,
                utilization=0.0
            )
            for i in range(num_gpus)
        ]
        
    def allocate(self, job_id: str, num_gpus: int, memory_per_gpu: int) -> List[int]:
        """Allocate GPUs to job using first-fit"""
        allocated = []
        
        for gpu in self.gpus:
            if len(allocated) >= num_gpus:
                break
                
            if gpu.available_memory >= memory_per_gpu and gpu.allocated_to is None:
                gpu.allocated_to = job_id
                gpu.available_memory -= memory_per_gpu
                gpu.utilization = ((gpu.total_memory - gpu.available_memory) / gpu.total_memory) * 100
                allocated.append(gpu.gpu_id)
        
        if len(allocated) == num_gpus:
            logger.info(f"Allocated GPUs {allocated} to job {job_id}")
            return allocated
        else:
            # Rollback allocation
            self.release(job_id)
            logger.warning(f"Could not allocate {num_gpus} GPUs for job {job_id}")
            return []
    
    def release(self, job_id: str):
        """Release GPUs from job"""
        for gpu in self.gpus:
            if gpu.allocated_to == job_id:
                gpu.available_memory = gpu.total_memory
                gpu.utilization = 0.0
                gpu.allocated_to = None
        logger.info(f"Released GPUs from job {job_id}")
    
    def get_available_gpus(self) -> int:
        """Count available GPUs"""
        return sum(1 for gpu in self.gpus if gpu.allocated_to is None)
    
    def get_gpu_status(self) -> List[Dict]:
        """Get status of all GPUs"""
        return [
            {
                'gpu_id': gpu.gpu_id,
                'total_memory': gpu.total_memory,
                'available_memory': gpu.available_memory,
                'utilization': gpu.utilization,
                'allocated_to': gpu.allocated_to
            }
            for gpu in self.gpus
        ]
