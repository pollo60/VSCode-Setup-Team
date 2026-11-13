# Local model awareness

Before claiming which local Ollama models or capabilities are currently
available, if the optional model inventory is installed, run:

```sh
/usr/bin/python3 "$HOME/Library/Application Support/VSCode-Model-Inventory/model-inventory.py" --refresh
```

Treat unavailable endpoints, missing capabilities and failed checks as
unknown, not as evidence of absence. Do not select or download a model, open a
network service, forward a port, or transmit the inventory externally without
the user's approval. The metadata is not proof of actual model performance or
availability in a specific VS Code or Codex model picker.
