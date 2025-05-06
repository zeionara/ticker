# Ticker

Ticket tracker for free events at [hermitage museum][hermitage]

## Dependencies

To run the app create a conda environment and install necessary dependencies:

```sh
conda create -n ticker python=3.12
conda activate ticker
pip install click requests python-telegram-bot
```

## Running

The run polling to wait until free tickets become available on [the website][hermitage]:

```sh
TG_BOT_TOKEN='foo' TG_CHAT_ID='bar' python -m ticker track -i
```

[hermitage]: https://tickets.hermitagemuseum.org
