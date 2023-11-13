# Meme Competition App

The Meme Competition App is a Django-based web application that allows users to participate in meme competitions. Users can create competitions, submit memes, and vote on memes to determine the winners.

See the app in production here: <https://meme-competition.fly.dev/>

## Features

- User registration and authentication
- Create and manage meme competitions
- Submit memes for competitions
- Vote on memes
- Track participant statistics
- Display competition results

## Installation

To set up the Meme Competition App on your local machine, follow the steps below:

### Clone the repository

    git clone https://github.com/lindenhutchinson/meme-comp.git

### Navigate to the project directory

    cd meme-comp

### Create a virtual environment and activate it

    python3 -m venv venv
    source venv/bin/activate

### Install the required dependencies

    pip install -r requirements.txt

### Create a .env.dev file in the project root directory and add the following configuration

    SECRET_KEY=your-secret-key
    ENVIRONMENT=development

Replace your-secret-key with a secure secret key for your application.

### Run database migrations

    python manage.py migrate

### Start the development server

    python manage.py runserver

To run a docker container as the channel message broker:

    docker run -p 6379:6379 -d redis:5

Access the app in your browser at <http://localhost:8000>.

To run celery:

    celery -A MemeComp worker -l info -E -Q memes --without-gossip --without-mingle --without-heartbeat -Ofair --concurrency 1 -P solo

## Usage

- Register a new user account or log in with an existing account.
- Create a competition or join an existing competition.
- Submit memes for the competition.
- Vote on memes submitted by other participants.
- Track participant statistics and view competition results.

## Contributing

Contributions are welcome! If you have any suggestions, bug reports, or feature requests, please open an issue or submit a pull request.
