# Протокол WebSocket

Подключение: `/ws` (реконнект — `/ws?token=<player_token>`).

Все сообщения — JSON вида `{"type": "...", ...поля}`.

## Клиент → сервер

| type | Поля | Ответ |
| --- | --- | --- |
| `ping` | — | `pong` |
| `create` | `max_players?` (3–7), `player_name?` | `created` |
| `join` | `room_code`, `player_name?` | `joined` |
| `leave` | — | `left` |
| `chat` | `text` | `chat` (всем) |
| `start_game` | — (только хост) | `game_started` |
| `submit_plan` | `actions` — 3 строки-карты | `plan_submitted` |

## Сервер → клиент

- `created` / `joined`: `room_code, player_id, token, host_id, max_players, status, players[]`
- `left`, `player_joined`, `player_left`, `player_disconnected`, `player_reconnected`, `reconnected`
- `chat`: `player_id, player_name, text`
- `error`: `code, message` (коды: `bad_message`, `room_not_found`, `room_full`, `already_in_room`, `not_in_room`)
- `game_started`: `room_code, players[]`
- `plan_submitted`: `player_id`; `planning_timed_out`
- События игры: `{type, round_number, ...data}` — `moved`, `changed_level`, `turned_around`, `shoot`, `knocked`, `horse`, `stood_up`, `lay_down`, `eliminated`, `entered_delorean`, `time_paradox`, `wagon_detached`, `money_awarded`, `round_started`, `game_finished`.

## Коды ошибок

`bad_message`, `room_not_found`, `room_full`, `already_in_room`, `not_in_room`.