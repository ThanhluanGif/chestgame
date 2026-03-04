from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

try:
    import chess
except ImportError as exc:
    raise SystemExit("Thieu thu vien python-chess. Cai dat bang: pip install chess") from exc


PIECE_ICONS = {
    "P": "♙",
    "N": "♘",
    "B": "♗",
    "R": "♖",
    "Q": "♕",
    "K": "♔",
    "p": "♟",
    "n": "♞",
    "b": "♝",
    "r": "♜",
    "q": "♛",
    "k": "♚",
}

TERMINATION_TEXT = {
    chess.Termination.CHECKMATE: "chieu het",
    chess.Termination.STALEMATE: "stalemate",
    chess.Termination.INSUFFICIENT_MATERIAL: "khong du quan de chieu het",
    chess.Termination.SEVENTYFIVE_MOVES: "luat 75 nuoc",
    chess.Termination.FIVEFOLD_REPETITION: "lap lai 5 lan",
    chess.Termination.FIFTY_MOVES: "luat 50 nuoc",
    chess.Termination.THREEFOLD_REPETITION: "lap lai 3 lan",
}


class ChessGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Co vua Python - GUI")
        self.root.resizable(False, False)

        self.tile_size = 82
        self.board = chess.Board()
        self.selected_square: int | None = None
        self.legal_targets: set[int] = set()
        self.move_log: list[str] = []

        self.status_var = tk.StringVar()
        self._build_ui()
        self._refresh_all()

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, bg="#efe8d8")
        container.pack(padx=10, pady=10)

        self.canvas = tk.Canvas(
            container,
            width=self.tile_size * 8,
            height=self.tile_size * 8,
            highlightthickness=0,
            bg="#efe8d8",
        )
        self.canvas.grid(row=0, column=0, padx=(0, 12), pady=0)
        self.canvas.bind("<Button-1>", self._on_board_click)

        side = tk.Frame(container, bg="#efe8d8")
        side.grid(row=0, column=1, sticky="ns")

        status_label = tk.Label(
            side,
            textvariable=self.status_var,
            font=("Segoe UI", 11, "bold"),
            bg="#efe8d8",
            justify="left",
            anchor="w",
            width=30,
        )
        status_label.pack(anchor="w", pady=(0, 8))

        button_row = tk.Frame(side, bg="#efe8d8")
        button_row.pack(anchor="w", pady=(0, 10))
        tk.Button(button_row, text="Van moi", width=10, command=self._new_game).pack(side="left", padx=(0, 8))
        tk.Button(button_row, text="Hoan tac", width=10, command=self._undo_move).pack(side="left")

        tk.Label(side, text="Lich su nuoc di", bg="#efe8d8", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.history_list = tk.Listbox(side, width=30, height=22, font=("Consolas", 10))
        self.history_list.pack(anchor="w", pady=(4, 0))

    @staticmethod
    def _row_col_to_square(row: int, col: int) -> int:
        file_idx = col
        rank_idx = 7 - row
        return chess.square(file_idx, rank_idx)

    def _square_to_row_col(self, square: int) -> tuple[int, int]:
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)
        row = 7 - rank_idx
        col = file_idx
        return row, col

    def _draw_board(self) -> None:
        self.canvas.delete("all")

        light = "#f2e9dc"
        dark = "#b88964"
        selected = "#f5d06a"

        for row in range(8):
            for col in range(8):
                x0 = col * self.tile_size
                y0 = row * self.tile_size
                x1 = x0 + self.tile_size
                y1 = y0 + self.tile_size
                square = self._row_col_to_square(row, col)

                base_color = light if (row + col) % 2 == 0 else dark
                fill_color = selected if square == self.selected_square else base_color
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill_color, outline=fill_color)

                if square in self.legal_targets:
                    piece_on_target = self.board.piece_at(square)
                    if piece_on_target is None:
                        self.canvas.create_oval(
                            x0 + self.tile_size * 0.4,
                            y0 + self.tile_size * 0.4,
                            x0 + self.tile_size * 0.6,
                            y0 + self.tile_size * 0.6,
                            fill="#2f2f2f",
                            outline="",
                        )
                    else:
                        self.canvas.create_rectangle(
                            x0 + 4,
                            y0 + 4,
                            x1 - 4,
                            y1 - 4,
                            outline="#cc2c2c",
                            width=3,
                        )

                piece = self.board.piece_at(square)
                if piece:
                    icon = PIECE_ICONS[piece.symbol()]
                    self.canvas.create_text(
                        x0 + self.tile_size / 2,
                        y0 + self.tile_size / 2 + 1,
                        text=icon,
                        font=("Segoe UI Symbol", int(self.tile_size * 0.58)),
                        fill="#121212",
                    )

        for col in range(8):
            file_char = chr(ord("a") + col)
            self.canvas.create_text(
                col * self.tile_size + self.tile_size - 10,
                self.tile_size * 8 - 10,
                text=file_char,
                font=("Segoe UI", 9, "bold"),
                fill="#5b4635",
            )

        for row in range(8):
            rank_char = str(8 - row)
            self.canvas.create_text(
                10,
                row * self.tile_size + 12,
                text=rank_char,
                font=("Segoe UI", 9, "bold"),
                fill="#5b4635",
            )

    def _refresh_history(self) -> None:
        self.history_list.delete(0, tk.END)
        for i in range(0, len(self.move_log), 2):
            w = self.move_log[i]
            b = self.move_log[i + 1] if i + 1 < len(self.move_log) else ""
            line = f"{(i // 2) + 1:>2}. {w:<8} {b}"
            self.history_list.insert(tk.END, line.strip())
        if self.move_log:
            self.history_list.see(tk.END)

    def _outcome_text(self) -> str:
        outcome = self.board.outcome(claim_draw=True)
        if outcome is None:
            return "Chua ket thuc"

        if outcome.winner is None:
            result = "Hoa"
        else:
            result = "Trang thang" if outcome.winner == chess.WHITE else "Den thang"

        reason = TERMINATION_TEXT.get(outcome.termination, str(outcome.termination).lower())
        return f"{result} ({reason})"

    def _update_status(self) -> None:
        if self.board.is_game_over(claim_draw=True):
            self.status_var.set(f"Trang thai: {self._outcome_text()}")
            return

        side_to_move = "Trang" if self.board.turn == chess.WHITE else "Den"
        if self.board.is_check():
            self.status_var.set(f"Luot di: {side_to_move} | Dang bi chieu")
        else:
            self.status_var.set(f"Luot di: {side_to_move}")

    def _refresh_all(self) -> None:
        self._draw_board()
        self._refresh_history()
        self._update_status()

    def _clear_selection(self) -> None:
        self.selected_square = None
        self.legal_targets.clear()

    def _select_square(self, square: int) -> None:
        piece = self.board.piece_at(square)
        if piece is None or piece.color != self.board.turn:
            self._clear_selection()
            self._draw_board()
            return

        self.selected_square = square
        self.legal_targets = {move.to_square for move in self.board.legal_moves if move.from_square == square}
        self._draw_board()

    def _promotion_choice(self) -> int | None:
        raw = simpledialog.askstring(
            "Phong cap",
            "Nhap quan muon phong cap: q, r, b, n",
            parent=self.root,
        )
        if raw is None:
            return None

        text = raw.strip().lower()
        mapper = {
            "q": chess.QUEEN,
            "r": chess.ROOK,
            "b": chess.BISHOP,
            "n": chess.KNIGHT,
        }
        return mapper.get(text)

    def _choose_move(self, start: int, end: int) -> chess.Move | None:
        candidates = [move for move in self.board.legal_moves if move.from_square == start and move.to_square == end]
        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        if not any(move.promotion for move in candidates):
            return candidates[0]

        promo = self._promotion_choice()
        if promo is None:
            return None
        for move in candidates:
            if move.promotion == promo:
                return move
        return None

    def _push_move(self, move: chess.Move) -> None:
        san = self.board.san(move)
        self.board.push(move)
        self.move_log.append(san)
        self._clear_selection()
        self._refresh_all()

        if self.board.is_game_over(claim_draw=True):
            messagebox.showinfo("Ket qua", self._outcome_text(), parent=self.root)

    def _on_board_click(self, event: tk.Event) -> None:
        if self.board.is_game_over(claim_draw=True):
            return

        col = event.x // self.tile_size
        row = event.y // self.tile_size
        if not (0 <= row < 8 and 0 <= col < 8):
            return

        clicked_square = self._row_col_to_square(row, col)
        clicked_piece = self.board.piece_at(clicked_square)

        if self.selected_square is None:
            self._select_square(clicked_square)
            return

        if clicked_square == self.selected_square:
            self._clear_selection()
            self._draw_board()
            return

        chosen = self._choose_move(self.selected_square, clicked_square)
        if chosen is not None:
            self._push_move(chosen)
            return

        if clicked_piece is not None and clicked_piece.color == self.board.turn:
            self._select_square(clicked_square)
        else:
            self._clear_selection()
            self._draw_board()

    def _new_game(self) -> None:
        self.board.reset()
        self.move_log.clear()
        self._clear_selection()
        self._refresh_all()

    def _undo_move(self) -> None:
        if not self.board.move_stack:
            return
        self.board.pop()
        if self.move_log:
            self.move_log.pop()
        self._clear_selection()
        self._refresh_all()


def main() -> None:
    root = tk.Tk()
    ChessGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
