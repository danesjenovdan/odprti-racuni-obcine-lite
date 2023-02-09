## odprti racuni obcine

### How to run?

```
docker-compose up
```

### SETUP

This will migrate and seed the database, collect static files, and createa a superuser with the username `admin`, email `admin@example.dev`, and password `changeme`.

```
docker-compose run odprti-racuni-obcine ./setup.sh
```

You can then start the app with `docker-compose up` if you haven't already.

Visit `http://localhost:8000/admin/`, log in with `admin` and `changeme` and edit the municipality in order to be able to see something rendered at one of the urls below.

### URLS

#### Admin
http://localhost:8000/admin/

#### Front end
http://localhost:8000/pregled/1/1/
