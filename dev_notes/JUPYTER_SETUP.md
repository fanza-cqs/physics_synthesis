# Jupyter Classic Setup

This project uses Jupyter Classic interface (not JupyterLab).

## Key version constraints:
- `notebook>=6.5.0,<7.0.0` - Ensures classic interface
- Avoid `jupyterlab` package completely

## Setup process:
1. Create virtual environment: `python3 -m venv physics_pipeline_env`
2. Activate: `source physics_pipeline_env/bin/activate`
3. Install: `pip install -r requirements.txt`
4. Register kernel: `python -m ipykernel install --user --name=physics_pipeline_env --display-name "Physics Pipeline"`
5. Start: `jupyter notebook`

## If JupyterLab accidentally gets installed:
```bash
pip uninstall jupyterlab notebook jupyter_server jupyterlab_server notebook_shim jupyter-lsp jupyter-events jupyterlab_pygments jupyterlab_widgets
pip install "notebook<7.0.0"

## 4. Test your setup works:

```bash
# Test that your pinned requirements work
deactivate
rm -rf test_env
python3 -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
jupyter notebook  # Should open classic interface
deactivate
rm -rf test_env