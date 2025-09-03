from click.testing import CliRunner
import redact_cli
import os

def run_redaction():
    runner = CliRunner()

    # Get the project root (folder where this script lives, one level up from src)
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    samples_dir = os.path.join(root, "samples")
    out_dir = os.path.join(root, "out")

    args = [
        samples_dir,
        "--out", out_dir,
        "--style", "black",
        "--lang", "eng+hin",
        "--min-conf", "60",
        "--fields", "AADHAAR,PAN,PHONE,EMAIL,DATE",
        "--extensions", ".pdf,.png,.jpg,.jpeg,.tif,.tiff,.bmp",
        "--dpi", "200"
    ]

    result = runner.invoke(redact_cli.main, args)
    print(result.output)

    if result.exit_code != 0:
        print("Error:", result.exception)

if __name__ == "__main__":
    run_redaction()
