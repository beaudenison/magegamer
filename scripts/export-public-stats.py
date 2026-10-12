#!/usr/bin/env python3
"""Read XMage user_stats.db and write a public leaderboard JSON file.

The authorized-user database is never opened. Email addresses are not in
this database. A locked database leaves the previous JSON in place.
"""

import json
import sqlite3
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("/home/beaudenison/xmage/mage-server/db/user_stats.db")
OUT_PATH = Path("/home/beaudenison/magegamer-site/stats.json")


def read_varint(buf, index):
    value = 0
    shift = 0
    while index < len(buf):
        byte = buf[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, index
        shift += 7
        if shift > 70:
            raise ValueError("varint too long")
    raise ValueError("truncated varint")


def parse_fields(buf):
    fields = {}
    index = 0
    while index < len(buf):
        key, index = read_varint(buf, index)
        number = key >> 3
        wire = key & 7
        if wire == 0:
            value, index = read_varint(buf, index)
        elif wire == 1:
            value = buf[index:index + 8]
            index += 8
        elif wire == 2:
            length, index = read_varint(buf, index)
            value = buf[index:index + length]
            index += length
        elif wire == 5:
            value = buf[index:index + 4]
            index += 4
        else:
            raise ValueError(f"unsupported wire type {wire}")
        fields[number] = value
    return fields


def signed_int(value, bits):
    sign = 1 << (bits - 1)
    return value - (1 << bits) if value & sign else value


def glicko(blob):
    if not isinstance(blob, (bytes, bytearray)) or not blob:
        return None
    fields = parse_fields(blob)
    rating = fields.get(1)
    if not isinstance(rating, (bytes, bytearray)) or len(rating) != 8:
        return None
    return round(struct.unpack("<d", rating)[0])


def player_row(name, proto, end_time_ms):
    fields = parse_fields(proto or b"")
    matches = signed_int(fields.get(6, 0), 32)
    quits = (
        signed_int(fields.get(7, 0), 32)
        + signed_int(fields.get(8, 0), 32)
        + signed_int(fields.get(9, 0), 32)
    )
    tournaments = signed_int(fields.get(2, 0), 32)
    quit_rate = None if matches <= 0 else round(quits / matches, 4)
    last_played = None
    if end_time_ms:
        last_played = datetime.fromtimestamp(end_time_ms / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    proto_name = fields.get(1)
    if isinstance(proto_name, (bytes, bytearray)) and proto_name:
        name = proto_name.decode("utf-8", "replace")
    return {
        "name": name,
        "matches": matches,
        "quitRate": quit_rate,
        "tournaments": tournaments,
        "rating": glicko(fields.get(10)),
        "lastPlayed": last_played,
    }


def load_players():
    uri = f"file:{DB_PATH}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=2)
    try:
        rows = connection.execute("SELECT userName, proto, endTimeMs FROM user_stats").fetchall()
    finally:
        connection.close()
    players = [player_row(name, proto, end_ms or 0) for name, proto, end_ms in rows]
    players.sort(key=lambda item: (-item["matches"], -1 if item["rating"] is None else -item["rating"], item["name"].lower()))
    return players


def main():
    try:
        players = load_players()
    except sqlite3.OperationalError as exc:
        print(f"stats database unavailable: {exc}", file=sys.stderr)
        return 0
    payload = {
        "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "players": players,
    }
    text = json.dumps(payload, indent=2) + "\n"
    if any("@" in player["name"] for player in players):
        print("refusing to write a name that looks like an email", file=sys.stderr)
        return 1
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    current = OUT_PATH.read_text(encoding="utf-8") if OUT_PATH.exists() else ""
    # Compare player rows only so a timestamp-only change does not republish.
    def body(raw):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return data.get("players")
    if body(current) == players and current:
        print("unchanged")
        return 0
    temporary = OUT_PATH.with_suffix(".json.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(OUT_PATH)
    print(f"wrote {len(players)} players")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
