.. These are examples of badges you might want to add to your README:
   please update the URLs accordingly

    .. image:: https://api.cirrus-ci.com/github/<USER>/iGritty.svg?branch=main
        :alt: Built Status
        :target: https://cirrus-ci.com/github/<USER>/iGritty
    .. image:: https://readthedocs.org/projects/iGritty/badge/?version=latest
        :alt: ReadTheDocs
        :target: https://iGritty.readthedocs.io/en/stable/
    .. image:: https://img.shields.io/coveralls/github/<USER>/iGritty/main.svg
        :alt: Coveralls
        :target: https://coveralls.io/r/<USER>/iGritty
    .. image:: https://img.shields.io/pypi/v/iGritty.svg
        :alt: PyPI-Server
        :target: https://pypi.org/project/iGritty/
    .. image:: https://img.shields.io/conda/vn/conda-forge/iGritty.svg
        :alt: Conda-Forge
        :target: https://anaconda.org/conda-forge/iGritty
    .. image:: https://pepy.tech/badge/iGritty/month
        :alt: Monthly Downloads
        :target: https://pepy.tech/project/iGritty
    .. image:: https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter
        :alt: Twitter
        :target: https://twitter.com/iGritty

.. image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
    :alt: Project generated with PyScaffold
    :target: https://pyscaffold.org/

|

========
iGritty
========


    Gritty is a discord bot!


Simple discord bot which supports the following commands:

`!train <game>` Launch a game train!
  - game (optional): game for which this train runs
`!schedule_train <time> <game> <recurrance>` Schedule a game train for the future
  - time: time to run the train, HH:MM format
  - game: game for which this train runs
  - recurrance (optional): how often to repeat this train (ONCE or DAILY, default option is ONCE)
`!upcoming_trains` List all upcoming scheduled trains
`!cancel_train <train_id>` Cancel given upcoming train
  - train_id: train id number, obtainable from `!upcoming_trains`

`!version`` - print the bot version and exit

----------------
Operation Manual
----------------

* Installation

Create a virtual environment and install iGritty and its dependencies
```
# In iGritty clone directory...
$> python -m venv .venv
$> source .venv/bin/activate
(venv) $> pip install .
```

* Configuration

Get a discord bot token and store in .env
```
# In iGritty clone directory...
echo "BOT_TOKEN=<your_token_here> > .env"
```

**Never share this token anywhere, with anyone**

* Execution

Start the bot with the `launch` console script
```
# In iGritty clone directory...
$> source .venv/bin/activate
(venv) $> launch
2025-03-16 18:55:53 INFO     discord.client logging in using static token
...<snip>...
```

* Logs

Logfiles can be found in the `logs/` directory of the iGritty clone directory.

Logs are capped at a reasonable size and will rotate through 5 backups 

* Database

When run, iGritty will generate a database in the `database/` directory of the iGritty clone directory.

This database is used to make settings persistent across bot restarts, and should not be hand-modified.

If this database is deleted, iGritty will create a new one from scratch


.. _pyscaffold-notes:

Note
====

This project has been set up using PyScaffold 4.6. For details and usage
information on PyScaffold see https://pyscaffold.org/.
