# Short Spot

It’s not about silencing the ads; it’s about making them timeless.
[Read more...](https://rhew.org/projects/posts/2024-10-13-short-spot/)

## Get

```
ssh rhew.org
cd short-spot
git pull origin main
```

## Podcast stripper secrets

Add "`OPEN_AI_KEY`" to `podcast-stripper/secrets.env`.

## Build

```
make podcast-stripper
make podcast-manager
```

## Deploy

```
cd ../rhew.org
docker-compose up manager stripper -d
```

