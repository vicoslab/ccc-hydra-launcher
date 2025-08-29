"""Example using the CCC launcher plugin with Hydra"""
import hydra
from omegaconf import DictConfig, OmegaConf
import os

@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """Main entry point for the example
    
    This example shows how to use the CCC launcher plugin with Hydra.
    It will run multiple jobs in parallel on available GPUs using CCC.
    """
    print(f"Working directory: {os.getcwd()}")
    print(f"Configuration:\n{OmegaConf.to_yaml(cfg)}")
    print("Waiting for 2 seconds to simulate work...")
    import time
    time.sleep(2)
    print("Done waiting!")
    
if __name__ == "__main__":
    main()
