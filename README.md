## Installation Guide for this project using UV, no more PIP

To install UV, please refer to the official [UV Installation Tutorial](https://docs.astral.sh/uv/getting-started/installation/).

### Steps to Get Started
1. **Install UV**: Follow the instructions in the link above.
2. **Sync and Set Up Environment**: Once UV is installed, run the following command in your project directory:
   ```bash
   uv sync
   ```
   This will automatically create a virtual environment under the project folder.
3. **Run the Local Server**: Start the server by running:
   ```bash
   uv run uvicorn src.main:app
   ```
4. **The Visrtual Environtmennt is valid only for this folder**