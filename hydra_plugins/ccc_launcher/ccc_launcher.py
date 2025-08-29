import logging
import os,sys
import tempfile
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from hydra.core.hydra_config import HydraConfig
from hydra.core.singleton import Singleton
from hydra.core.utils import (
    JobReturn,
    JobStatus,
    filter_overrides,
    setup_globals,
)
from hydra.plugins.launcher import Launcher
from hydra.types import HydraContext, TaskFunction
from omegaconf import DictConfig, OmegaConf

log = logging.getLogger(__name__)



class CCCLauncher(Launcher):
    def __init__(self, **kwargs: Any) -> None:
        self.config = kwargs
        self.config_loader: Optional[Any] = None
        
    def setup(self, *, hydra_context: HydraContext, task_function: TaskFunction, config: DictConfig) -> None:
        self.config_loader = hydra_context.config_loader
        self.task_function = task_function
        self.hydra_context = hydra_context
        self.config = config

    def cleanup_gpu_file(self, gpu_file: str) -> None:
        """Clean up the GPU allocation file"""
        try:
            if os.path.exists(gpu_file):
                os.unlink(gpu_file)
                log.info(f"Cleaned up GPU allocation file: {gpu_file}")
        except Exception as e:
            log.warning(f"Could not remove GPU allocation file {gpu_file}: {str(e)}")

    def launch(self, job_overrides: Sequence[Sequence[str]], initial_job_idx: int) -> Sequence[JobReturn]:
        """
        Launch jobs using CCC launcher
        Args:
            job_overrides: a batch of job arguments
            initial_job_idx: Initial job idx in batch
        Returns:
            Sequence of return values from run function
        """
        setup_globals()
        assert self.config_loader is not None
        assert self.task_function is not None

        log.info(f"CCCLauncher launching {len(job_overrides)} jobs")
        log.info(f"Launching jobs with CCC on cluster...")
        

        # Get launcher config
        launcher_cfg = self.config.hydra.launcher

        # Setup the gpu allocation command
        ccc_gpus_cmd = ["ccc", "gpus"]
        if launcher_cfg.cluster_info:
            ccc_gpus_cmd.extend(["--on_cluster", launcher_cfg.cluster_info])
        ccc_gpus_cmd.extend(["--gpus", str(launcher_cfg.num_gpus)])
        ccc_gpus_cmd.extend(["--tasks", str(len(job_overrides))])
        ccc_gpus_cmd.extend(["--min_gpus_per_host", str(launcher_cfg.min_gpus_per_host)])
        if launcher_cfg.hosts:
            ccc_gpus_cmd.extend(["--hosts", launcher_cfg.hosts])
        if launcher_cfg.ignore_hosts:
            ccc_gpus_cmd.extend(["--ignore_hosts", launcher_cfg.ignore_hosts])
        ccc_gpus_cmd.extend(["--gpus_as_single_host", str(launcher_cfg.gpus_as_single_host)])
        ccc_gpus_cmd.extend(["--wait_for_available", str(launcher_cfg.wait_for_available)])

        gpu_file = None
        try:
            # Get GPU file with available GPUs
            gpu_file = subprocess.check_output(ccc_gpus_cmd).decode().strip()
            log.info(f"GPU allocation file: {gpu_file}")

            returns: List[JobReturn] = []
            current_job_idx = initial_job_idx
            for i, overrides in enumerate(job_overrides):
                log.info(f"\t[{i + initial_job_idx}] Launching with config:\n{' '.join(filter_overrides(overrides))}")
                sweep_config = self.config_loader.load_sweep_config(
                    master_config=self.config,
                    sweep_overrides=list(overrides)
                )

                config_args = []
                if hasattr(self.config.hydra, 'config_name'):
                    config_args.extend(['--config-name', self.config.hydra.config_name])
                if hasattr(self.config.hydra, 'config_dir'):
                    config_args.extend(['--config-dir', self.config.hydra.config_dir])
                if hasattr(self.config.hydra, 'config_path'):
                    config_args.extend(['--config-path', self.config.hydra.config_path])

                ccc_run_cmd = ["ccc", "run", gpu_file, sys.executable]
                if self.config.hydra.launcher.get("dryrun", False):
                    ccc_run_cmd.insert(2, "dryrun")

                # Get the actual script file path
                script_file = sys.modules[self.task_function.__module__].__file__
                cmd = ccc_run_cmd + [script_file] + config_args + list(overrides)


                log.info(f"\t[{i + initial_job_idx}] Launching cmd:\n{' '.join(cmd)}")
                # Start process in background
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Store process and its config for later
                returns.append(
                    (proc, JobReturn(
                        working_dir=os.getcwd(),
                        cfg=sweep_config,
                        hydra_cfg=OmegaConf.create({
                            "overrides": overrides,
                            "job": {"id": f"job_{current_job_idx}", "num": current_job_idx},
                        }),
                        task_name=self.task_function.__name__,
                        status=JobStatus.UNKNOWN,
                    ))
                )
                current_job_idx += 1

            # Wait for all processes to complete and collect results
            final_returns = []
            for proc, ret in returns:
                stdout, stderr = proc.communicate()
                log.info(f"Job {ret.hydra_cfg.job.id} output:")
                log.info(stdout.decode())
                log.info(stderr.decode())
                
                ret.status = JobStatus.COMPLETED if proc.returncode == 0 else JobStatus.FAILED
                final_returns.append(ret)

            return final_returns
        finally:
            # Ensure GPU file is cleaned up even if an error occurs
            if gpu_file:
                self.cleanup_gpu_file(gpu_file)
