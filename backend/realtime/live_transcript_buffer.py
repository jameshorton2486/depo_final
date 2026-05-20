from __future__ import annotations

from dataclasses import dataclass, field

from backend.realtime.live_readback import search_live_blocks


@dataclass
class LiveTranscriptBuffer:
    session_id: int
    blocks: list[dict[str, object]] = field(default_factory=list)
    word_timeline: list[dict[str, object]] = field(default_factory=list)
    packet_count: int = 0
    last_latency_ms: int = 0
    stream_status: str = "idle"
    reconnect_count: int = 0
    sequence: int = 0

    def add_block(self, block: dict[str, object], *, latency_ms: int) -> dict[str, object]:
        self.sequence += 1
        enriched = {**block, "sequence": self.sequence}
        self.blocks.append(enriched)
        for word in block.get("words", []):
            self.word_timeline.append(
                {
                    "sequence": self.sequence,
                    "word_id": word["id"],
                    "block_id": block["id"],
                    "word_text": word.get("word_text"),
                    "start_time": word.get("start_time"),
                    "end_time": word.get("end_time"),
                    "speaker_label": block.get("speaker_label"),
                    "confidence": word.get("confidence"),
                }
            )
        self.packet_count += max(1, len(block.get("words", [])))
        self.last_latency_ms = latency_ms
        self.stream_status = "streaming"
        return enriched

    def mark_completed(self) -> None:
        self.stream_status = "completed"

    def mark_stopped(self) -> None:
        self.stream_status = "stopped"

    def snapshot(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "stream_status": self.stream_status,
            "packet_count": self.packet_count,
            "last_latency_ms": self.last_latency_ms,
            "reconnect_count": self.reconnect_count,
            "timeline": self.blocks,
            "word_timeline": self.word_timeline,
            "speaker_labels": sorted(
                {
                    str(block.get("speaker_label"))
                    for block in self.blocks
                    if block.get("speaker_label")
                }
            ),
        }

    def search(self, query: str) -> list[dict[str, object]]:
        return search_live_blocks(self.blocks, query)
