"""
Sequential Thinking MCP — SQLite 异步持久化存储
路径: Storage/Store.py
原作者: 小逸 (重构自 spences10/mcp-sequentialthinking-tools)
官方仓库: https://github.com/LseKit/SequentialThinking

使用 aiosqlite 实现异步 SQLite 存储，WAL 模式优化并发读取。
数据库路径通过相对路径计算，不写死绝对路径。
"""
import json, secrets, os
from datetime import datetime, timezone
from typing import Optional
import aiosqlite

try:
    import jieba
    _jieba_ok = True
except ImportError:
    _jieba_ok = False


def _fts5_query(raw: str) -> str:
    """
    将用户搜索文本转为 FTS5 MATCH 兼容的查询。
    有 jieba 时对中文分词后用 OR 连接（"代码质量"→"代码 OR 质量"），
    无 jieba 时回退到直接传递原字符串。
    """
    if not _jieba_ok or not raw:
        return raw or ""
    words = [w.strip() for w in jieba.cut(raw) if len(w.strip()) >= 2]
    if not words:
        return raw
    return " OR ".join(words[:20])

from ..Utils.Logger import setup_logger
log = setup_logger("store")

from ..Core.Models import (
    ThinkingSession, ThinkingStep, Branch, SessionSummary,
    SessionMetrics, ThinkingPattern, MAX_QUALITY_STEPS, Assumption,
)

# 数据库路径：GitHubSrc 内部的 Data/ 文件夹（大驼峰命名，不写死绝对路径）
_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
_DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, "Data", "sequential-thinking.db")


class Store:
    """SQLite 异步持久化存储"""
    def __init__(self, db_path: str = None):
        # db_path 由 CLI 参数传入，不提供则使用默认值 Data/sequential-thinking.db
        self.db_path = db_path if db_path else _DEFAULT_DB_PATH
        self.db: Optional[aiosqlite.Connection] = None

    async def open(self):
        # 确保数据库文件所在目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self.db.execute("PRAGMA foreign_keys=ON")
        # 性能 PRAGMA：synchronous=NORMAL（WAL 模式已保证原子性）、
        # cache_size=负值表 KiB、mmap_size 启内存映射 I/O
        await self.db.execute("PRAGMA synchronous=NORMAL")
        await self.db.execute("PRAGMA cache_size=-8000")
        await self.db.execute("PRAGMA mmap_size=33554432")
        await self._init_schema()

    async def _init_schema(self):
        statements = [
            """CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, problem TEXT, context_json TEXT,
                quality_score REAL DEFAULT 0.5, status TEXT DEFAULT 'active',
                current_step INTEGER DEFAULT 0, initial_analysis TEXT DEFAULT '',
                created_at TEXT, modified_at TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS session_tags (
                session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
                tag TEXT, PRIMARY KEY(session_id, tag)
            )""",
            """CREATE TABLE IF NOT EXISTS steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
                branch_id TEXT DEFAULT '', number INTEGER, type TEXT,
                content TEXT, timestamp TEXT, parent_step INTEGER,
                metadata_json TEXT, connections_json TEXT,
                is_revision INTEGER DEFAULT 0, revises_step INTEGER
            )""",
            """CREATE TABLE IF NOT EXISTS branches (
                id TEXT, session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
                from_step INTEGER, alt_desc TEXT, created_at TEXT,
                PRIMARY KEY(id, session_id)
            )""",
            """CREATE TABLE IF NOT EXISTS assumptions (
                id TEXT, session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
                text TEXT, step_number INTEGER, confidence REAL DEFAULT 0.5,
                critical INTEGER DEFAULT 0, verified INTEGER DEFAULT 0,
                invalidated INTEGER DEFAULT 0, verified_by TEXT DEFAULT '[]',
                invalidated_by TEXT DEFAULT '[]',
                PRIMARY KEY(id, session_id)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_steps_session ON steps(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_tags_session ON session_tags(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_assumptions_session ON assumptions(session_id)",
            # FTS5 全文搜索虚拟表（替代 LIKE 的 %keyword% 全表扫描）
            "CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(problem, tokenize='unicode61')",
        ]
        for stmt in statements:
            await self.db.execute(stmt)

    async def create_session(
        self, problem: str, ctx: dict, tags: list[str]
    ) -> ThinkingSession:
        sid = secrets.token_hex(16)
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "INSERT INTO sessions(id,problem,context_json,created_at,modified_at) VALUES(?,?,?,?,?)",
            (sid, problem, json.dumps(ctx, ensure_ascii=False), now, now)
        )
        for t in tags:
            await self.db.execute(
                "INSERT INTO session_tags(session_id,tag) VALUES(?,?)", (sid, t)
            )
        await self.db.commit()
        # 同步 FTS5 索引
        await self._sync_fts(sid, problem)
        return await self.get_session(sid)

    async def get_session(self, sid: str) -> Optional[ThinkingSession]:
        row = await self.db.execute(
            "SELECT * FROM sessions WHERE id=?", (sid,)
        )
        row = await row.fetchone()
        if not row:
            return None
        s = ThinkingSession(
            id=row["id"], problem=row["problem"],
            context=json.loads(row["context_json"]) if row["context_json"] else {},
            quality_score=row["quality_score"], status=row["status"],
            current_step=row["current_step"],
            initial_analysis=row["initial_analysis"] or "",
            created=datetime.fromisoformat(row["created_at"]),
            last_modified=datetime.fromisoformat(row["modified_at"]),
            tags=await self._load_tags(sid),
        )
        s.steps = await self._load_steps(sid, "")
        s.branches = await self._load_branches(sid)
        return s

    async def delete_session(self, sid: str) -> bool:
        """删除会话及其所有关联数据（级联删除）。返回 True 表示实际删除了数据。"""
        # 先检查会话是否存在
        row = await self.db.execute("SELECT 1 FROM sessions WHERE id=?", (sid,))
        if not await row.fetchone():
            return False
        # 级联删除：先删关联数据，再删主记录
        await self.db.execute("DELETE FROM assumptions WHERE session_id=?", (sid,))
        await self.db.execute("DELETE FROM steps WHERE session_id=?", (sid,))
        await self.db.execute("DELETE FROM branches WHERE session_id=?", (sid,))
        await self.db.execute("DELETE FROM session_tags WHERE session_id=?", (sid,))
        await self.db.execute("DELETE FROM sessions WHERE id=?", (sid,))
        # 同步删除 FTS5 索引
        await self.db.execute("DELETE FROM sessions_fts WHERE rowid=(SELECT rowid FROM sessions WHERE id=?)", (sid,))
        await self.db.commit()
        return True

    async def list_sessions(self, status: str = "", tags: list[str] = None,
                            limit: int = 50) -> list[SessionSummary]:
        # 动态构建 WHERE 子句
        where_clauses = []
        params = []
        if status:
            where_clauses.append("status=?")
            params.append(status)
        if tags:
            # 多标签 AND 过滤：需要同时匹配所有标签
            tag_placeholders = ",".join("?" for _ in tags)
            where_clauses.append(
                f"id IN (SELECT session_id FROM session_tags WHERE tag IN ({tag_placeholders}) "
                f"GROUP BY session_id HAVING COUNT(DISTINCT tag)=?)"
            )
            params.extend(tags)
            params.append(len(tags))
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        params.append(limit)
        query = f"SELECT * FROM sessions {where_sql} ORDER BY modified_at DESC LIMIT ?"
        rows = await self.db.execute(query, tuple(params))
        rows = await rows.fetchall()
        result = []
        for row in rows:
            step_count = (await (
                await self.db.execute(
                    "SELECT COUNT(*) FROM steps WHERE session_id=? AND branch_id=''",
                    (row["id"],)
                )
            ).fetchone())[0]
            branch_count = (await (
                await self.db.execute(
                    "SELECT COUNT(*) FROM branches WHERE session_id=?", (row["id"],)
                )
            ).fetchone())[0]
            result.append(SessionSummary(
                id=row["id"], problem=row["problem"],
                step_count=step_count, branch_count=branch_count,
                status=row["status"], quality_score=row["quality_score"],
                created=datetime.fromisoformat(row["created_at"]),
                last_modified=datetime.fromisoformat(row["modified_at"]),
                tags=await self._load_tags(row["id"]),
            ))
        return result

    async def update_session_status(self, sid: str, status: str):
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE sessions SET status=?,modified_at=? WHERE id=?",
            (status, now, sid)
        )
        await self.db.commit()

    async def search_sessions(self, query: str) -> list[SessionSummary]:
        # FTS5 全文搜索——中文用 jieba 分词构建 OR 查询，避免不可见字符导致 FTS5 语法错误
        safe_query = _fts5_query(query)
        if not safe_query:
            return []
        try:
            rows = await self.db.execute(
                "SELECT s.* FROM sessions s "
                "JOIN sessions_fts f ON f.rowid = s.rowid "
                "WHERE sessions_fts MATCH ? ORDER BY rank LIMIT 50",
                (safe_query,)
            )
        except Exception:
            # FTS5 语法异常时降级为 LIKE 模糊匹配
            rows = await self.db.execute(
                "SELECT * FROM sessions WHERE problem LIKE ? OR initial_analysis LIKE ? "
                "ORDER BY modified_at DESC LIMIT 50",
                (f"%{query}%", f"%{query}%")
            )
        rows = await rows.fetchall()
        return [
            SessionSummary(
                id=r["id"], problem=r["problem"],
                status=r["status"], quality_score=r["quality_score"],
                created=datetime.fromisoformat(r["created_at"]),
                last_modified=datetime.fromisoformat(r["modified_at"]),
                tags=await self._load_tags(r["id"]),
            ) for r in rows
        ]

    async def add_step(self, session_id: str, content: str, step_type: str,
                       parent: Optional[int] = None, meta: dict = None,
                       branch_id: str = "",
                       is_revision: bool = False,
                       revises_step: Optional[int] = None) -> ThinkingStep:
        max_row = await self.db.execute(
            "SELECT COALESCE(MAX(number),0) FROM steps WHERE session_id=? AND branch_id=?",
            (session_id, branch_id)
        )
        max_num = (await max_row.fetchone())[0]
        num = max_num + 1
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "INSERT INTO steps(session_id,branch_id,number,type,content,timestamp,parent_step,metadata_json,connections_json,is_revision,revises_step) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (session_id, branch_id, num, step_type, content, now, parent,
             json.dumps(meta or {}), json.dumps([]),
             1 if is_revision else 0, revises_step)
        )
        await self._update_session_meta(session_id, num)
        await self.db.commit()
        step = await self._load_single_step(session_id, num, branch_id)
        return step

    async def update_step(self, session_id: str, num: int,
                          content: Optional[str] = None,
                          step_type: Optional[str] = None,
                          meta: Optional[dict] = None) -> Optional[ThinkingStep]:
        if content is not None:
            await self.db.execute(
                "UPDATE steps SET content=? WHERE session_id=? AND number=? AND branch_id=''",
                (content, session_id, num)
            )
        if step_type is not None:
            await self.db.execute(
                "UPDATE steps SET type=? WHERE session_id=? AND number=? AND branch_id=''",
                (step_type, session_id, num)
            )
        if meta is not None:
            await self.db.execute(
                "UPDATE steps SET metadata_json=? WHERE session_id=? AND number=? AND branch_id=''",
                (json.dumps(meta), session_id, num)
            )
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE sessions SET modified_at=?,current_step=? WHERE id=?",
            (now, num, session_id)
        )
        await self.db.commit()
        return await self._load_single_step(session_id, num, "")

    async def create_branch(self, session_id: str, from_step: int,
                            alt_desc: str) -> Branch:
        bid = secrets.token_hex(16)
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "INSERT INTO branches(id,session_id,from_step,alt_desc,created_at) VALUES(?,?,?,?,?)",
            (bid, session_id, from_step, alt_desc, now)
        )
        await self.db.commit()
        return Branch(id=bid, from_step=from_step,
                      alternative_desc=alt_desc, created=datetime.fromisoformat(now))

    async def add_step_to_branch(self, session_id: str, branch_id: str,
                                 content: str, step_type: str,
                                 parent: Optional[int] = None,
                                 meta: dict = None) -> ThinkingStep:
        return await self.add_step(session_id, content, step_type, parent, meta, branch_id)

    async def get_metrics(self, time_range: str = "all") -> SessionMetrics:
        m = SessionMetrics()
        cutoff = None
        if time_range == "day":
            cutoff = datetime.now(timezone.utc).isoformat()[:10]
        elif time_range == "week":
            from datetime import timedelta
            cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        elif time_range == "month":
            from datetime import timedelta
            cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

        if cutoff:
            rows = await self.db.execute(
                "SELECT id,quality_score,created_at FROM sessions WHERE created_at >= ?",
                (cutoff,)
            )
        else:
            rows = await self.db.execute(
                "SELECT id,quality_score,created_at FROM sessions"
            )
        rows = await rows.fetchall()
        total_steps = total_quality = total_branches = 0
        for r in rows:
            m.total_sessions += 1
            total_quality += r["quality_score"]
            day = r["created_at"][:10]
            m.sessions_by_day[day] = m.sessions_by_day.get(day, 0) + 1
            sc = (await (await self.db.execute(
                "SELECT COUNT(*) FROM steps WHERE session_id=?", (r["id"],)
            )).fetchone())[0]
            bc = (await (await self.db.execute(
                "SELECT COUNT(*) FROM branches WHERE session_id=?", (r["id"],)
            )).fetchone())[0]
            total_steps += sc
            total_branches += bc
        if m.total_sessions > 0:
            m.average_steps = total_steps / m.total_sessions
            m.average_quality = total_quality / m.total_sessions
            m.average_branches = total_branches / m.total_sessions
        # 额外查询 active/completed 计数
        active_row = await (await self.db.execute(
            "SELECT COUNT(*) FROM sessions WHERE status='active'"
        )).fetchone()
        completed_row = await (await self.db.execute(
            "SELECT COUNT(*) FROM sessions WHERE status='completed'"
        )).fetchone()
        m.active_sessions = active_row[0] if active_row else 0
        m.completed_sessions = completed_row[0] if completed_row else 0
        return m

    async def _load_tags(self, sid: str) -> list[str]:
        rows = await self.db.execute(
            "SELECT tag FROM session_tags WHERE session_id=?", (sid,)
        )
        return [r[0] for r in await rows.fetchall()]

    async def _load_steps(self, sid: str, bid: str) -> list[ThinkingStep]:
        rows = await self.db.execute(
            "SELECT * FROM steps WHERE session_id=? AND branch_id=? ORDER BY number",
            (sid, bid)
        )
        steps = []
        for r in await rows.fetchall():
            steps.append(ThinkingStep(
                number=r["number"], type=r["type"], content=r["content"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                parent_step=r["parent_step"],
                metadata=json.loads(r["metadata_json"]) if r["metadata_json"] else {},
                connections=json.loads(r["connections_json"]) if r["connections_json"] else [],
                is_revision=bool(r["is_revision"]) if "is_revision" in r.keys() else False,
                revises_step=r["revises_step"] if "revises_step" in r.keys() else None
            ))
        return steps

    async def _load_branches(self, sid: str) -> dict[str, Branch]:
        rows = await self.db.execute(
            "SELECT * FROM branches WHERE session_id=?", (sid,)
        )
        branches = {}
        for r in await rows.fetchall():
            b = Branch(
                id=r["id"], from_step=r["from_step"],
                alternative_desc=r["alt_desc"] or "",
                created=datetime.fromisoformat(r["created_at"]),
                steps=await self._load_steps(sid, r["id"]),
            )
            branches[b.id] = b
        return branches

    async def _load_single_step(self, sid: str, num: int,
                                bid: str) -> Optional[ThinkingStep]:
        row = await self.db.execute(
            "SELECT * FROM steps WHERE session_id=? AND number=? AND branch_id=?",
            (sid, num, bid)
        )
        r = await row.fetchone()
        if not r:
            return None
        return ThinkingStep(
            number=r["number"], type=r["type"], content=r["content"],
            timestamp=datetime.fromisoformat(r["timestamp"]),
            parent_step=r["parent_step"],
            metadata=json.loads(r["metadata_json"]) if r["metadata_json"] else {},
            connections=json.loads(r["connections_json"]) if r["connections_json"] else [],
            is_revision=bool(r["is_revision"]) if "is_revision" in r.keys() else False,
            revises_step=r["revises_step"] if "revises_step" in r.keys() else None
        )

    async def _update_session_meta(self, sid: str, step_num: int):
        qs = await self._calculate_quality(sid)
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE sessions SET quality_score=?,current_step=?,modified_at=? WHERE id=?",
            (qs, step_num, now, sid)
        )

    async def _calculate_quality(self, sid: str) -> float:
        rows = await self.db.execute(
            "SELECT type,connections_json FROM steps WHERE session_id=?", (sid,)
        )
        rows = await rows.fetchall()
        if not rows:
            return 0.5
        type_map, total_conns = {}, 0
        for r in rows:
            type_map[r["type"]] = type_map.get(r["type"], 0) + 1
            conns = json.loads(r["connections_json"]) if r["connections_json"] else []
            total_conns += len(conns)
        total_steps = len(rows)
        variety = len(type_map) / 4.0
        conn_score = min(1.0, total_conns / total_steps)
        depth = min(1.0, total_steps / MAX_QUALITY_STEPS)
        return round(variety * 0.3 + conn_score * 0.3 + depth * 0.4, 4)

    # ── 假设管理方法 ──

    async def add_assumption(self, assumption: Assumption, session_id: str) -> None:
        """保存一个假设到数据库"""
        await self.db.execute(
            """INSERT OR REPLACE INTO assumptions 
               (id, session_id, text, step_number, confidence, critical, verified, invalidated, verified_by, invalidated_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                assumption.id, session_id, assumption.text, assumption.step_number,
                assumption.confidence, 1 if assumption.critical else 0,
                1 if assumption.verified else 0, 1 if assumption.invalidated else 0,
                json.dumps(assumption.verified_by), json.dumps(assumption.invalidated_by)
            )
        )
        await self.db.commit()

    async def get_assumptions(self, session_id: str) -> list[Assumption]:
        """获取会话的所有假设"""
        rows = await self.db.execute(
            "SELECT * FROM assumptions WHERE session_id=? ORDER BY step_number, id",
            (session_id,)
        )
        results = []
        for r in await rows.fetchall():
            results.append(Assumption(
                id=r["id"], text=r["text"], step_number=r["step_number"],
                confidence=r["confidence"], critical=bool(r["critical"]),
                verified=bool(r["verified"]), invalidated=bool(r["invalidated"]),
                verified_by=json.loads(r["verified_by"] or "[]"),
                invalidated_by=json.loads(r["invalidated_by"] or "[]")
            ))
        return results

    async def update_assumption(self, session_id: str, assumption_id: str, 
                                verified: Optional[bool] = None, invalidated: Optional[bool] = None,
                                verified_by: Optional[int] = None, invalidated_by: Optional[int] = None) -> bool:
        """更新假设的验证或推翻状态"""
        row = await self.db.execute(
            "SELECT verified, invalidated, verified_by, invalidated_by FROM assumptions WHERE id=? AND session_id=?",
            (assumption_id, session_id)
        )
        r = await row.fetchone()
        if not r:
            return False
        
        new_verified = verified if verified is not None else bool(r["verified"])
        new_invalidated = invalidated if invalidated is not None else bool(r["invalidated"])
        new_verified_by = json.loads(r["verified_by"] or "[]")
        new_invalidated_by = json.loads(r["invalidated_by"] or "[]")
        
        if verified_by is not None and verified_by not in new_verified_by:
            new_verified_by.append(verified_by)
        if invalidated_by is not None and invalidated_by not in new_invalidated_by:
            new_invalidated_by.append(invalidated_by)
            
        await self.db.execute(
            """UPDATE assumptions SET verified=?, invalidated=?, verified_by=?, invalidated_by=?
               WHERE id=? AND session_id=?""",
            (
                1 if new_verified else 0, 1 if new_invalidated else 0,
                json.dumps(new_verified_by), json.dumps(new_invalidated_by),
                assumption_id, session_id
            )
        )
        await self.db.commit()
        return True
        
    async def delete_assumption(self, session_id: str, assumption_id: str) -> bool:
        """删除一个假设"""
        cursor = await self.db.execute(
            "DELETE FROM assumptions WHERE id=? AND session_id=?",
            (assumption_id, session_id)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    # ── 会话生命周期方法 ──

    async def complete_session(self, session_id: str) -> bool:
        """将会话状态更新为 'completed'"""
        now = datetime.now(timezone.utc).isoformat()
        cursor = await self.db.execute(
            "UPDATE sessions SET status='completed', modified_at=? WHERE id=? AND status='active'",
            (now, session_id)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    # ── 标签管理方法 ──

    async def add_tags(self, session_id: str, tags: list[str]) -> None:
        """为会话添加标签（忽略已存在的）"""
        for tag in tags:
            await self.db.execute(
                "INSERT OR IGNORE INTO session_tags(session_id, tag) VALUES(?, ?)",
                (session_id, tag)
            )
        await self.db.commit()

    async def remove_tags(self, session_id: str, tags: list[str]) -> None:
        """移除会话的指定标签"""
        if not tags:
            return
        placeholders = ",".join("?" for _ in tags)
        await self.db.execute(
            f"DELETE FROM session_tags WHERE session_id=? AND tag IN ({placeholders})",
            (session_id, *tags)
        )
        await self.db.commit()

    async def _sync_fts(self, sid: str, problem: str):
        """同步 FTS5 索引——将 problem 和 initial_analysis 合并后用 jieba 分词入库。"""
        # 读取 initial_analysis 合并索引，中文场景下搜索命中率显著提高
        row = await self.db.execute(
            "SELECT initial_analysis FROM sessions WHERE id=?", (sid,)
        )
        row = await row.fetchone()
        full = problem
        if row and row[0]:
            full = problem + " " + row[0]
        if _jieba_ok:
            full = " ".join(w for w in jieba.cut(full) if len(w.strip()) >= 1)
        await self.db.execute(
            "INSERT INTO sessions_fts(rowid, problem) "
            "VALUES((SELECT rowid FROM sessions WHERE id=?), ?)",
            (sid, full)
        )

    async def close(self):
        if self.db:
            await self.db.close()
