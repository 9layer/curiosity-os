# Curiosity OS

Секретарь любопытства: быстро фиксирует вопросы, не отвлекая от дела, и помогает разбирать их позже.

## Быстрый старт

    cp .env.example .env   # заполните ключи
    docker compose up -d --build
    docker compose exec api alembic upgrade head

Интерфейс: Telegram-бот. Команды: /start /focus /back /inbox /review /explore.