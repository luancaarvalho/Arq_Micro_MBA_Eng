from __future__ import annotations

import argparse
import json
from typing import Optional

from confluent_kafka import Consumer, KafkaException


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Consumidor read_committed para verificar ordenação e transações."
    )
    parser.add_argument(
        "--bootstrap-server",
        default="localhost:9092",
        help="Bootstrap server (padrão: localhost:9092)",
    )
    parser.add_argument(
        "--topic",
        default="ordering.transactions",
        help="Tópico alvo.",
    )
    parser.add_argument(
        "--group",
        default="ordering-demo",
        help="Consumer group usado no teste.",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=5,
        help="Quantidade máxima de mensagens consumidas.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout total para aguardar mensagens (s).",
    )
    return parser.parse_args()


def create_consumer(args: argparse.Namespace) -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": args.bootstrap_server,
            "group.id": args.group,
            "auto.offset.reset": "earliest",
            "isolation.level": "read_committed",
        }
    )


def consume(args: argparse.Namespace) -> None:
    consumer = create_consumer(args)
    consumer.subscribe([args.topic])
    received = 0
    elapsed = 0.0
    interval = 0.2

    print(
        f"[Consumer] group={args.group} topic={args.topic} max_messages={args.max_messages}"
    )

    try:
        while received < args.max_messages and elapsed < args.timeout:
            msg = consumer.poll(0.2)
            elapsed += interval
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())
            payload: Optional[dict] = json.loads(msg.value())
            print(
                f" ↳ offset={msg.offset()} partition={msg.partition()} key={msg.key().decode()} seq={payload['sequence']} status={payload['status']}"
            )
            received += 1
    finally:
        consumer.close()
        print(f"[Consumer] Finalizado. Mensagens recebidas: {received}")


if __name__ == "__main__":
    consume(parse_args())
