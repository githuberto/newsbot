import argparse
import sqlite3


from collections.abc import Mapping, Iterable


def placeholders(data: Iterable) -> str:
  return ", ".join("?" for _ in data)


class DB:
  def __init__(self, con: sqlite3.Connection):
    con.row_factory = sqlite3.Row
    self.con = con

  @staticmethod
  def with_cursor(f):
    def wrapper(*args, **kwargs):
      if not kwargs.get("cursor"):
        with args[0].con as con:
          kwargs["cursor"] = con.cursor()
          return f(*args, **kwargs)
      else:
        return f(*args, **kwargs)
    return wrapper

  def create_tables(self):
    with self.con as con:
      cur = con.cursor()
      cur.execute("PRAGMA foreign_keys = ON;")
      sql = """
        CREATE TABLE IF NOT EXISTS feeds(
          id INTEGER PRIMARY KEY,
          url STRING NOT NULL,
          channel INTEGER NOT NULL
        );"""
      cur.execute(sql)
      sql = """
        CREATE TABLE IF NOT EXISTS posts(
          id STRING NOT NULL,
          feed_id INTEGER NOT NULL,
          FOREIGN KEY(feed_id) REFERENCES feeds(id) ON DELETE CASCADE
        );"""
      cur.execute(sql)

  def insert(self, table: str, m: Mapping) -> int:
    with self.con as con:
      cur = con.cursor()
      sql = f"""
        INSERT INTO {table}({', '.join(m.keys())})
        VALUES ({placeholders(m)});
        """
      return cur.execute(sql, tuple(m.values())).lastrowid or 0

  def delete(self, table: str, row_filter: Mapping) -> bool:
    with self.con as con:
      cur = con.cursor()
      sql = f"""
        DELETE FROM {table}
        WHERE {", ".join(f"{k} = ?" for k in row_filter)}
        """
      cur.execute(sql, tuple(row_filter.values()))
      return cur.rowcount > 0

  def select(self, table: str, column_list: list[str] = ["*"],
             row_filter: Mapping = {}) -> list[sqlite3.Row]:
    with self.con as con:
      cur = con.cursor()
      sql = f"""SELECT {", ".join(column_list)} FROM {table}"""
      if row_filter:
        sql += f"""\nWHERE {", ".join(f"{k} = ?" for k in row_filter)}"""
      sql += ";"

      return cur.execute(sql, tuple(row_filter.values())).fetchall()


parser = argparse.ArgumentParser()
parser.add_argument("database", help="The path to the database.")
args = parser.parse_args()
db = DB(sqlite3.connect(args.database))
db.create_tables()
