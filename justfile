build:
    docker build -t registry.paynepride.com/book-tracker:latest .

push:
    just build
    docker push registry.paynepride.com/book-tracker:latest
