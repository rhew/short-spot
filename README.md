# Short Spot

It’s not about silencing the ads; it’s about making them timeless.
[Read more...](https://rhew.org/projects/posts/2024-10-13-short-spot/)

## Get

```
git clone https://github.com/rhew/short-spot.git
cd short-spot
```

## Podcast stripper secrets

Add "`OPEN_AI_KEY`" to `podcast-stripper/secrets.env`.

## Build

```
make
```

## Deploy

```
docker-compose up manager stripper -d
```

