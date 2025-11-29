from __future__ import annotations

import argparse
import json
import time
from typing import Iterable

from confluent_kafka import Producer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Produz eventos finitos usando transações Kafka."
    )
    parser.add_argument(
        "--bootstrap-server",
        default="localhost:9092",
        help="Bootstrap server (padrão: localhost:9092)",
    )
    parser.add_argument(
        "--topic",
        default="ordering.transactions",
        help="Tópico alvo para o demo.",
    )
    parser.add_argument(
        "--transactional-id",
        default="ordering-demo-tx",
        help="Transactional ID do produtor.",
    )
    parser.add_argument(
        "--key",
        default="ORDER-TRANSACTION-100",
        help="Chave usada em todas as mensagens (garante ordenação).",
    )
    parser.add_argument(
        "--events",
        type=int,
        default=5,
        help="Quantidade de eventos produzidos (finito).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.2,
        help="Intervalo (s) entre cada envio.",
    )
    parser.add_argument(
        "--abort",
        action="store_true",
        help="Aborta a transação ao final para mostrar rollback.",
    )
    return parser.parse_args()


def build_events(count: int) -> Iterable[dict]:
    for seq in range(1, count + 1):
        yield {
            "event_name": "CheckoutReserved",
            "order_id": "ORDER-TRANSACTION-100",
            "sequence": seq,
            "status": "PENDING" if seq < count else "RESERVED",
        }


def configure_producer(args: argparse.Namespace) -> Producer:
    return Producer(
        {
            "bootstrap.servers": args.bootstrap_server,
            "enable.idempotence": True,
            "acks": "all",
            "retries": 5,
            "max.in.flight.requests.per.connection": 1,
            "transactional.id": args.transactional_id,
        }
    )


def produce_transactions(args: argparse.Namespace) -> None:
    producer = configure_producer(args)
    producer.init_transactions()
    producer.begin_transaction()

    print(
        f"[Producer] transaction_id={args.transactional_id} events={args.events} abort={args.abort}"
    )

    for event in build_events(args.events):
        payload = json.dumps(event).encode("utf-8")
        producer.produce(topic=args.topic, key=args.key, value=payload)
        producer.poll(0)
        print(f" ↳ sent seq={event['sequence']} status={event['status']}")
        time.sleep(args.interval)

    if args.abort:
        producer.abort_transaction()
        print("[Producer] Transação abortada (nenhum evento visível).")
    else:
        producer.commit_transaction()
        print("[Producer] Transação commitada com sucesso.")


if __name__ == "__main__":
    produce_transactions(parse_args())
