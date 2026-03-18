from __future__ import annotations

from core.entities import Block, SummaryLine


def _page_label(count: int) -> str:
    return "1 p\u00e1gina" if count == 1 else f"{count} p\u00e1ginas"


def _prize_label(count: int) -> str:
    return "1 pr\u00eamio" if count == 1 else f"{count} pr\u00eamios"


def build_summary(blocks: list[Block], result_loaded: bool) -> list[SummaryLine]:
    if not result_loaded:
        lines = [SummaryLine(f"Total de blocos: {len(blocks)}", "neutral", kind="section")]
        for block in blocks:
            lines.append(
                SummaryLine(
                    f"Bloco {block.number} \u00b7 {_page_label(len(block.pages))}",
                    "neutral",
                    kind="section",
                )
            )
        return lines

    lines: list[SummaryLine] = []
    for block in blocks:
        winner_lines: list[str] = []
        for page in block.pages:
            valid_lines = [line for line in page.lines if line.is_valid_bet]
            for position, line in enumerate(valid_lines, start=1):
                for winner in line.winners:
                    winner_lines.append(
                        f"{line.spec.normalized_text} \u00b7 Linha {position} \u00b7 "
                        f"P\u00e1gina {page.number} \u00b7 {winner.prize_label} pr\u00eamio"
                    )
        if winner_lines:
            lines.append(
                SummaryLine(
                    f"Bloco {block.number} \u00b7 {_page_label(len(block.pages))} \u00b7 "
                    f"Com vencedor \u2014 {_prize_label(len(winner_lines))}",
                    "positive",
                    kind="section",
                )
            )
            for winner_line in winner_lines:
                lines.append(SummaryLine(winner_line, "positive", kind="detail", indent=1))
        else:
            lines.append(
                SummaryLine(
                    f"Bloco {block.number} \u00b7 {_page_label(len(block.pages))} \u00b7 Sem vencedor",
                    "neutral",
                    kind="section",
                )
            )
    return lines
