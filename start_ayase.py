# Starter code to run ayase programmatically for use with a debugger

import uvicorn
from src import main

app = main.app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
