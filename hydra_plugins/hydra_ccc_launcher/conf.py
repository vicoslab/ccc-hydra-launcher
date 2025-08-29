from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from hydra.core.config_store import ConfigStore
from hydra.plugins.launcher import Launcher
from hydra.types import HydraContext, TaskFunction
from omegaconf import DictConfig

@dataclass
class CCCLauncherConf:
    """Configuration for the CCC Launcher"""
    _target_: str = "hydra_plugins.hydra_ccc_launcher.ccc_launcher.CCCLauncher"
    
    # CCC specific configs
    cluster_info: Optional[str] = None  # path to cluster_info.json
    num_gpus: int = 1  # number of GPUs to select per one job
    min_gpus_per_host: int = 1  # minimum number of GPUs to select per host
    hosts: Optional[str] = None  # comma separated list of hosts to select GPUs from
    ignore_hosts: Optional[str] = None  # comma separated list of hosts to ignore
    gpus_as_single_host: bool = True  # whether to group all GPUs on the same host as one
    wait_for_available: int = -1  # Time to wait for GPUs (-1: no wait, 0: wait indefinitely, >0: timeout)

cs = ConfigStore.instance()
cs.store(
    group="hydra/launcher",
    name="ccc",
    node=CCCLauncherConf,
    provider="ccc_hydra_launcher",
)
