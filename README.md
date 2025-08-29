# Hydra Launcher plugin for CCC Tools

CCC Tools includes a Hydra launcher plugin that allows you to use CCC's GPU allocation and distributed execution capabilities with Hydra's configuration and job launching framework. The plugin provides similar functionality to Hydra's `submitit_local` launcher but uses CCC to manage GPU resources.

## Using the Launcher Plugin

1. First, ensure you have both CCC Tools and Hydra installed:
```bash
pip install git+https://github.com/vicoslab/ccc-tools
pip install git+https://github.com/vicoslab/ccc-hydra-launcher
```

2. Configure your Hydra application to use the CCC launcher by adding this to your config:
```yaml
defaults:
  - override hydra/launcher: ccc

hydra:
  launcher:
    cluster_info: path/to/cluster_info.json  # Path to cluster info file
    num_gpus: 1  # Number of GPUs per job
    min_gpus_per_host: 1  # Minimum GPUs per host
    hosts: null  # Optional: comma-separated list of hosts
    ignore_hosts: null  # Optional: comma-separated list of hosts to ignore
    gpus_as_single_host: true  # Group GPUs on same host
    wait_for_available: -1  # Wait policy for GPU availability
```

3. Run your Hydra application with parameter sweeps:
```bash
python my_app.py --multirun model.type=resnet50,resnet101 training.batch_size=32,64
```

The launcher will:
1. Use CCC to find available GPUs based on your configuration
2. Launch jobs in parallel using the available GPU resources
3. Clean up GPU allocations when jobs complete

### Example

See a complete example in [example/hydra_example.py](example/hydra_example.py).

The example demonstrates how to:
- Configure the CCC launcher
- Run parameter sweeps across multiple GPUs
- Use CCC's GPU allocation and job management features