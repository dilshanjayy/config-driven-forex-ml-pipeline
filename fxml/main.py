import typer

app = typer.Typer(help="Forex ML Pipeline CLI")

@app.callback()
def callback():
    pass

def main():
    app()
