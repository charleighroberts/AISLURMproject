# inference (Role 4)

SLURM job scripts and model-serving setup go here: sbatch scripts, vLLM / llama.cpp config, and notes on where model weights live on the cluster.

The web app talks to models only through `web/llm/backends.py`. To add a real backend, subclass `LLMBackend` there (`submit`, `status`, `result`) and register it in `get_backend()`.
