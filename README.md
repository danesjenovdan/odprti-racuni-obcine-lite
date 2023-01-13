## odprti racuni obcine

### How to run?

```
docker-compose up
```

### SETUP

This will migrate and seed the database, collect static files, compile messages (translations), and createa a superuser with the username `admin`, email `admin@example.dev`, and password `changeme`.

```
docker-compose run odprti-racuni ./setup.sh
```

You can then start the app with `docker-compose up` if you haven't already.
