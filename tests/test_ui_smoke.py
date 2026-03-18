from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLineEdit,
    QToolBar,
    QToolButton,
)

from core.enums import BetType, CommitMode, Flag, RowType
from services.controller import BancaController
from ui.delegates.bet_delegate import BetDelegate
from ui.dialogs.result_dialog import ResultDialog
from ui.main_window import MainWindow
from ui.models.bets_table_model import BetsTableModel
from ui.models.finance_table_model import FinanceTableModel
from ui.theme import color
from ui.views.bets_table_view import BetsTableView


def _build_bets_view(tmp_path: Path):
    controller = BancaController(tmp_path)
    _, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    second_line = controller.state.blocks[0].pages[0].lines[1].line_id
    controller.upsert_bet_text(second_line, "666", commit_mode=CommitMode.ENTER)
    model = BetsTableModel(controller)
    view = BetsTableView(controller)
    view.setModel(model)
    view.show()
    QTest.qWait(10)
    return controller, model, view, page_id


def test_ctrl_up_selects_multiple_rows(tmp_path, qapp):
    controller, model, view, page_id = _build_bets_view(tmp_path)
    first_row = model.first_editable_row_for_page(page_id)
    second_row = first_row + 1
    view.setCurrentIndex(model.index(second_row, 0))
    view.selectionModel().select(
        model.index(second_row, 0),
        QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows,
    )
    view.setFocus()

    QTest.keyClick(view, Qt.Key_Up, Qt.ControlModifier)

    assert len(view.selectionModel().selectedRows()) >= 2


def test_shift_still_converts_milhar_to_mc(tmp_path, qapp):
    controller = BancaController(tmp_path)
    _, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "1234", commit_mode=CommitMode.ENTER)
    model = BetsTableModel(controller)
    view = BetsTableView(controller)
    view.setModel(model)
    view.show()
    QTest.qWait(10)
    first_row = model.first_editable_row_for_page(page_id)
    view.setCurrentIndex(model.index(first_row, 0))
    view.selectionModel().select(
        model.index(first_row, 0),
        QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows,
    )
    view.setFocus()

    QTest.keyClick(view, Qt.Key_Shift)

    assert controller.state.blocks[0].pages[0].lines[0].spec.bet_type == BetType.MILHAR_CENTENA


def test_enter_starts_editing_without_mouse(tmp_path, qapp):
    controller, model, view, page_id = _build_bets_view(tmp_path)
    first_row = model.first_editable_row_for_page(page_id)
    view.setCurrentIndex(model.index(first_row, 0))
    view.setFocus()

    QTest.keyClick(view, Qt.Key_Return)

    assert view.state() == QAbstractItemView.State.EditingState


def test_numpad_flag_applies_on_current_line(tmp_path, qapp):
    controller, model, view, page_id = _build_bets_view(tmp_path)
    first_row = model.first_editable_row_for_page(page_id)
    view.setCurrentIndex(model.index(first_row, 0))
    view.selectionModel().select(
        model.index(first_row, 0),
        QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows,
    )
    view.setFocus()

    QTest.keyClick(view, Qt.Key_Plus, Qt.KeypadModifier)

    assert Flag.DE in controller.state.blocks[0].pages[0].lines[0].spec.flags


def test_flag_during_edit_preserves_typed_number(tmp_path, qapp):
    controller = BancaController(tmp_path)
    _, page_id, _ = controller.create_block("452")
    model = BetsTableModel(controller)
    view = BetsTableView(controller)
    view.setModel(model)
    view.show()
    QTest.qWait(10)
    first_row = model.first_editable_row_for_page(page_id)
    index = model.index(first_row, 0)
    view.setCurrentIndex(index)
    view.edit(index)
    QTest.qWait(20)
    editor = view.findChild(QLineEdit)
    editor.setFocus()

    QTest.keyClicks(editor, "555")
    QTest.keyClick(editor, Qt.Key_Plus, Qt.KeypadModifier)
    QTest.qWait(20)

    line = controller.state.blocks[0].pages[0].lines[0]
    assert line.spec.normalized_text == "C 555 DE"


def test_flag_on_existing_line_moves_to_next_row(tmp_path, qapp):
    controller, model, view, page_id = _build_bets_view(tmp_path)
    first_row = model.first_editable_row_for_page(page_id)
    second_row = first_row + 1
    view.setCurrentIndex(model.index(first_row, 0))
    view.selectionModel().select(
        model.index(first_row, 0),
        QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows,
    )
    view.setFocus()

    QTest.keyClick(view, Qt.Key_Plus, Qt.KeypadModifier)
    QTest.qWait(20)

    assert view.currentIndex().row() == second_row


def test_value_blank_row_skips_to_next_page(tmp_path, qapp):
    controller = BancaController(tmp_path)
    _, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    next_page_id, next_page_line = controller.create_page_after(page_id)
    controller.upsert_bet_text(next_page_line, "777", commit_mode=CommitMode.ENTER)
    model = BetsTableModel(controller)
    view = BetsTableView(controller)
    view.setModel(model)
    view.show()
    QTest.qWait(10)

    first_page_blank_row = next(
        row_index
        for row_index in range(model.rowCount())
        if model.row_at(row_index).page_id == page_id and model.row_at(row_index).is_trailing_blank
    )
    next_page_first_value_row = model.first_editable_row_for_page(next_page_id)
    view.setCurrentIndex(model.index(first_page_blank_row, 1))
    view.setFocus()

    QTest.keyClick(view, Qt.Key_Return)

    assert view.currentIndex().row() == next_page_first_value_row
    assert view.currentIndex().column() == 1


def test_finance_block_click_focuses_bet_block(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    for number in ("452", "453", "454", "455", "456", "457", "458", "459", "986"):
        controller.create_block(number)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(50)
    finance_index = window.finance_model.index(2, FinanceTableModel.COL_BLOCK)
    rect = window.finance_view.visualRect(finance_index)

    QTest.mouseClick(window.finance_view.viewport(), Qt.LeftButton, Qt.NoModifier, rect.center())

    current_projection = window.bets_model.row_at(window.bets_view.currentIndex().row())
    top_row = window.bets_view.rowAt(0)
    top_projection = window.bets_model.row_at(top_row)
    assert current_projection.block_number == "454"
    assert current_projection.row_type.value == "block_header"
    assert top_projection.block_number == "454"
    window.close()


def test_launch_filters_toggle_projection_modes_and_compact_mode(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    _, _, awarded_line_id = controller.create_block("452")
    controller.upsert_bet_text(awarded_line_id, "M 6554", commit_mode=CommitMode.ENTER)
    controller.set_result(["6554", "1234", "5678", "9012", "3456"])
    controller.create_block("986")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    assert set(window.launch_filter_buttons) == {"all", "current", "awarded", "pending"}
    assert window.launch_filter_buttons["all"].isChecked() is True

    window.launch_filter_buttons["awarded"].click()
    QTest.qWait(20)

    block_headers = [row for row in window.bets_model.rows if row.row_type == RowType.BLOCK_HEADER]
    assert window.bets_model.filter_mode == "awarded"
    assert len(block_headers) == 1
    assert block_headers[0].block_number == "452"

    window.launch_compact_button.click()
    QTest.qWait(20)

    assert window.bets_view.compact_mode is True
    window.close()


def test_f9_opens_result_dialog_from_finance_focus(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    window = MainWindow(controller, root)
    opened = {"count": 0}
    monkeypatch.setattr(
        "ui.main_window.ResultDialog.exec",
        lambda self: opened.__setitem__("count", opened["count"] + 1) or QDialog.DialogCode.Rejected,
    )
    window.show()
    window.finance_view.setFocus()
    QTest.qWait(40)

    QTest.keyClick(window.finance_view, Qt.Key_F9)
    QTest.qWait(20)

    assert opened["count"] == 1
    window.close()


def test_f11_toggles_fullscreen_globally(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    QTest.keyClick(window, Qt.Key_F11)
    QTest.qWait(20)
    assert window.isFullScreen() is True

    QTest.keyClick(window, Qt.Key_F11)
    QTest.qWait(20)
    assert window.isFullScreen() is False
    window.close()


def test_b_shortcut_creates_block_with_window_focus(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    monkeypatch.setattr("ui.main_window.BlockDialog.exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("ui.main_window.BlockDialog.value", lambda self: "452")
    window = MainWindow(controller, root)
    window.show()
    window.bottom_bar.block_selector.setFocus()
    QTest.qWait(20)

    QTest.keyClick(window.bottom_bar.block_selector, Qt.Key_B)
    QTest.qWait(20)

    assert len(controller.state.blocks) == 1
    assert controller.state.blocks[0].number == "452"


def test_b_shortcut_works_immediately_after_open(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    monkeypatch.setattr("ui.main_window.BlockDialog.exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("ui.main_window.BlockDialog.value", lambda self: "986")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(50)

    QTest.keyClick(window, Qt.Key_B)
    QTest.qWait(20)

    assert len(controller.state.blocks) == 1
    assert controller.state.blocks[0].number == "986"


def test_b_shortcut_does_not_fire_inside_notes_field(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    monkeypatch.setattr("ui.main_window.BlockDialog.exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("ui.main_window.BlockDialog.value", lambda self: "111")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)
    window.finance_totals_panel.notes_input.setFocus()

    QTest.keyClick(window.finance_totals_panel.notes_input, Qt.Key_B)
    QTest.qWait(20)

    assert len(controller.state.blocks) == 0
    assert window.finance_totals_panel.notes_input.toPlainText().lower() == "b"


def test_b_shortcut_does_not_fire_inside_total_paid_input(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    monkeypatch.setattr("ui.main_window.BlockDialog.exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("ui.main_window.BlockDialog.value", lambda self: "222")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)
    window.finance_totals_panel.total_paid_input.setFocus()

    QTest.keyClick(window.finance_totals_panel.total_paid_input, Qt.Key_B)
    QTest.qWait(20)

    assert len(controller.state.blocks) == 0
    assert window.finance_totals_panel.total_paid_input.text().lower() == "b"
    window.finance_totals_panel.total_paid_input.clear()
    window.close()


def test_b_shortcut_works_during_bet_editing(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    controller.create_block("452")
    monkeypatch.setattr("ui.main_window.BlockDialog.exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("ui.main_window.BlockDialog.value", lambda self: "777")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(60)

    first_bet_row = next(
        row_index
        for row_index in range(window.bets_model.rowCount())
        if window.bets_model.row_at(row_index).row_type == RowType.BET_ENTRY
    )
    index = window.bets_model.index(first_bet_row, 0)
    window.bets_view.setCurrentIndex(index)
    window.bets_view.edit(index)
    QTest.qWait(20)
    editor = window.bets_view.findChild(QLineEdit)
    editor.setFocus()

    QTest.keyClick(editor, Qt.Key_B)
    QTest.qWait(40)

    assert len(controller.state.blocks) == 2
    assert controller.state.blocks[-1].number == "777"
    window.close()


def test_handle_create_block_focuses_page_one_for_immediate_typing(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    monkeypatch.setattr("ui.main_window.BlockDialog.exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("ui.main_window.BlockDialog.value", lambda self: "452")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    window.handle_create_block()
    QTest.qWait(60)

    assert len(controller.state.blocks) == 1
    block = controller.state.blocks[0]
    current_projection = window.bets_model.row_at(window.bets_view.currentIndex().row())
    top_row = window.bets_view.rowAt(8)
    top_projection = window.bets_model.row_at(top_row)

    assert current_projection.block_id == block.block_id
    assert current_projection.page_id == block.pages[0].page_id
    assert current_projection.row_type == RowType.BET_ENTRY
    assert window.bets_view.state() == QAbstractItemView.State.EditingState
    assert window.bets_view.findChild(QLineEdit) is not None
    assert top_projection.block_id == block.block_id
    window.close()


def test_new_block_removes_only_previous_extra_empty_page(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    _, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    controller.create_page_after(page_id)
    monkeypatch.setattr("ui.main_window.BlockDialog.exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("ui.main_window.BlockDialog.value", lambda self: "986")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    window.handle_create_block()
    QTest.qWait(60)

    assert len(controller.state.blocks) == 2
    assert controller.state.blocks[0].number == "452"
    assert len(controller.state.blocks[0].pages) == 1
    assert controller.state.blocks[-1].number == "986"
    window.close()


def test_new_block_keeps_previous_single_empty_page(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    controller.create_block("452")
    monkeypatch.setattr("ui.main_window.BlockDialog.exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("ui.main_window.BlockDialog.value", lambda self: "986")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    window.handle_create_block()
    QTest.qWait(60)

    assert len(controller.state.blocks) == 2
    assert controller.state.blocks[0].number == "452"
    assert len(controller.state.blocks[0].pages) == 1
    assert controller.state.blocks[-1].number == "986"
    window.close()


def test_new_block_does_not_remove_last_page_with_relevant_content(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    _, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    second_page_id, second_line_id = controller.create_page_after(page_id)
    controller.upsert_bet_text(second_line_id, "entrada invalida", commit_mode=CommitMode.ENTER)
    monkeypatch.setattr("ui.main_window.BlockDialog.exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("ui.main_window.BlockDialog.value", lambda self: "986")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    window.handle_create_block()
    QTest.qWait(60)

    assert len(controller.state.blocks) == 2
    assert controller.state.blocks[0].number == "452"
    assert len(controller.state.blocks[0].pages) == 2
    assert controller.state.blocks[0].pages[-1].page_id == second_page_id
    window.close()


def test_focus_page_action_opens_page_entry_for_immediate_edit(tmp_path, qapp):
    controller = BancaController(tmp_path)
    _, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    target_page_id, _ = controller.create_page_after(page_id)
    model = BetsTableModel(controller)
    view = BetsTableView(controller)
    view.setModel(model)
    view.show()
    QTest.qWait(20)

    view.focus_page_action(target_page_id)
    QTest.qWait(20)

    current_projection = model.row_at(view.currentIndex().row())
    assert current_projection.page_id == target_page_id
    assert current_projection.row_type == RowType.BET_ENTRY
    assert view.state() == QAbstractItemView.State.EditingState
    view.close()


def test_prepare_context_selection_preserves_multi_selection(tmp_path, qapp):
    controller, model, view, page_id = _build_bets_view(tmp_path)
    first_row = model.first_editable_row_for_page(page_id)
    second_row = first_row + 1
    view.selectionModel().select(
        model.index(first_row, 0),
        QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows,
    )
    view.selectionModel().select(
        model.index(second_row, 0),
        QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows,
    )

    assert view.prepare_context_selection(model.index(second_row, 0)) is True
    assert len(view.selectionModel().selectedRows()) == 2


def test_prepare_context_selection_collapses_when_clicking_outside_selection(tmp_path, qapp):
    controller = BancaController(tmp_path)
    _, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    second_line = controller.state.blocks[0].pages[0].lines[1].line_id
    controller.upsert_bet_text(second_line, "666", commit_mode=CommitMode.ENTER)
    third_line = controller.state.blocks[0].pages[0].lines[2].line_id
    controller.upsert_bet_text(third_line, "777", commit_mode=CommitMode.ENTER)
    model = BetsTableModel(controller)
    view = BetsTableView(controller)
    view.setModel(model)
    view.show()
    QTest.qWait(10)
    first_row = model.first_editable_row_for_page(page_id)
    second_row = first_row + 1
    third_row = first_row + 2
    view.selectionModel().select(
        model.index(first_row, 0),
        QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows,
    )
    view.selectionModel().select(
        model.index(second_row, 0),
        QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows,
    )

    assert view.prepare_context_selection(model.index(third_row, 0)) is True
    assert len(view.selectionModel().selectedRows()) == 1
    assert view.selectionModel().selectedRows()[0].row() == third_row


def test_context_menu_groups_actions_in_operational_order(tmp_path, qapp):
    controller, model, view, page_id = _build_bets_view(tmp_path)
    row_index = model.first_editable_row_for_page(page_id)
    row = model.row_at(row_index)

    menu, actions, transform_actions, flag_actions, clear_flags_action = view._build_context_menu(row)
    top_level_texts = ["---" if action.isSeparator() else action.text() for action in menu.actions()]

    assert top_level_texts == [
        "Inserir acima",
        "Inserir abaixo",
        "Nova página",
        "Novo bloco",
        "---",
        "Transformar",
        "Alternar MC",
        "---",
        "Flags",
        "---",
        "Excluir linha",
        "Excluir página",
        "Excluir bloco",
    ]
    assert [action.text() for action in transform_actions] == [
        "Centena (C)",
        "Milhar (M)",
        "Milhar/centena (MC)",
        "Dezena (D)",
        "Duque de dezena (DD)",
        "Terno de dezena (TD)",
        "Grupo (G)",
        "Terno de grupo (TG)",
        "Fechamento (F)",
    ]
    assert [action.text() for action in flag_actions] == ["Marcar I.V.", "Marcar DE", "Marcar DEM"]
    assert clear_flags_action.text() == "Limpar flags"
    assert actions["delete_line"].text() == "Excluir linha"
    view.close()


def test_invalid_bet_value_cell_is_not_editable(tmp_path, qapp):
    controller = BancaController(tmp_path)
    _, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "entrada invalida", commit_mode=CommitMode.ENTER)
    model = BetsTableModel(controller)
    first_row = model.first_editable_row_for_page(page_id)

    flags = model.flags(model.index(first_row, 1))

    assert not bool(flags & Qt.ItemIsEditable)


def test_result_dialog_requires_all_fields_complete(qapp):
    dialog = ResultDialog()
    dialog.show()
    QTest.qWait(10)
    ok_button = dialog.buttons.button(QDialogButtonBox.Ok)

    assert ok_button is not None
    assert ok_button.isEnabled() is False

    for index, field in enumerate(dialog.inputs):
        field.setText("1234")
        if index < len(dialog.inputs) - 1:
            assert ok_button.isEnabled() is False

    assert ok_button.isEnabled() is True


def test_result_dialog_rejects_non_numeric_input(qapp):
    dialog = ResultDialog()
    dialog.show()
    QTest.qWait(10)
    field = dialog.inputs[0]

    QTest.keyClicks(field, "12ab34")

    assert field.text() == "1234"


def test_finance_table_fits_without_horizontal_scroll(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    controller.create_block("452")
    controller.create_block("986")
    window = MainWindow(controller, root)
    window.show()
    window.resize(1500, 920)
    QTest.qWait(80)

    header_labels = [
        window.finance_model.headerData(index, Qt.Orientation.Horizontal)
        for index in range(window.finance_model.columnCount())
    ]
    total_width = sum(window.finance_view.columnWidth(index) for index in range(window.finance_model.columnCount()))

    assert header_labels == ["Status", "Bloco", "Dinheiro", "Bruto", "L\u00edquido (70%)", "Saldo"]
    assert window.finance_view.horizontalScrollBar().isVisible() is False
    assert total_width <= window.finance_view.viewport().width()
    window.close()


def test_operational_panels_use_more_vertical_area_for_lists(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    controller.create_block("452")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    assert window.result_panel.maximumHeight() < 286
    assert window.finance_totals_panel.notes_input.maximumHeight() < 92
    assert window.finance_view.verticalHeader().defaultSectionSize() < 44
    assert window.overview_panel.blocks_layout.spacing() < 12
    window.close()


def test_finance_contact_cell_opens_compact_menu(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    controller.create_block("452")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)
    contact_index = window.finance_model.index(0, FinanceTableModel.COL_CONTACT)
    rect = window.finance_view.visualRect(contact_index)

    QTest.mouseClick(window.finance_view.viewport(), Qt.LeftButton, Qt.NoModifier, rect.center())
    QTest.qWait(20)

    assert window._contact_menu is not None
    assert [action.text() for action in window._contact_menu.actions()] == [
        "Configurar contato / WhatsApp",
        "Enviar para o número",
    ]
    assert [action.isEnabled() for action in window._contact_menu.actions()] == [True, False]
    window._contact_menu.close()
    window.close()


def test_toolbar_block_search_focuses_matching_block(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    for number in ("452", "453", "454", "455", "456", "457", "458", "459", "986"):
        controller.create_block(number)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)
    window.block_search_input.lineEdit().setText("454")
    window.block_search_input.setFocus()

    QTest.keyClick(window.block_search_input.lineEdit(), Qt.Key_Return)
    QTest.qWait(30)

    current_projection = window.bets_model.row_at(window.bets_view.currentIndex().row())
    assert current_projection.block_number == "454"
    assert window.finance_view.currentIndex().row() == 2
    assert "454" in window.statusBar().currentMessage()
    window.close()


def test_toolbar_block_search_shows_discrete_message_when_missing(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    controller.create_block("452")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)
    window.block_search_input.lineEdit().setText("999")
    window.block_search_input.setFocus()

    QTest.keyClick(window.block_search_input.lineEdit(), Qt.Key_Return)
    QTest.qWait(30)

    assert "999" in window.statusBar().currentMessage()
    assert "não encontrado" in window.statusBar().currentMessage().lower()
    window.close()


def test_finance_saldo_uses_positive_negative_and_neutral_colors(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    for number, money in (("452", "90"), ("453", "60"), ("454", "70")):
        block_id, _, line_id = controller.create_block(number)
        controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
        controller.set_line_value(line_id, "100")
        controller.set_block_money(block_id, money)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    positive = window.finance_model.data(
        window.finance_model.index(0, FinanceTableModel.COL_SALDO),
        Qt.ItemDataRole.ForegroundRole,
    )
    negative = window.finance_model.data(
        window.finance_model.index(1, FinanceTableModel.COL_SALDO),
        Qt.ItemDataRole.ForegroundRole,
    )
    neutral = window.finance_model.data(
        window.finance_model.index(2, FinanceTableModel.COL_SALDO),
        Qt.ItemDataRole.ForegroundRole,
    )

    assert positive.color().name() == color("success_detail").name()
    assert negative.color().name() == color("danger_detail").name()
    assert neutral.color().name() == color("text_muted").name()
    window.close()


def test_overview_panel_switches_to_awarded_once_after_result(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "M 6554", commit_mode=CommitMode.ENTER)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    assert window.overview_panel.current_tab_key() == "blocks"

    controller.set_result(["6554", "1234", "5678", "9012", "3456"])
    QTest.qWait(40)

    assert window.overview_panel.current_tab_key() == "awarded"

    window.overview_panel.tab_buttons[0].click()
    controller.set_result(["6554", "1234", "5678", "9012", "3456"])
    QTest.qWait(40)

    assert window.overview_panel.current_tab_key() == "blocks"
    window.close()


def test_overview_panel_shows_only_awarded_blocks_and_expands_details(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    _, _, first_line_id = controller.create_block("452")
    controller.upsert_bet_text(first_line_id, "M 6554", commit_mode=CommitMode.ENTER)
    _, _, second_line_id = controller.create_block("986")
    controller.upsert_bet_text(second_line_id, "555", commit_mode=CommitMode.ENTER)
    controller.set_result(["6554", "1234", "5678", "9012", "3456"])
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    awarded_buttons = [
        button
        for button in window.overview_panel.awarded_page.findChildren(QToolButton)
        if button.property("overviewKind") == "awarded"
    ]

    assert len(awarded_buttons) == 1
    assert awarded_buttons[0].text().startswith("Bloco 452")

    awarded_buttons[0].click()
    QTest.qWait(20)

    bet_labels = [
        label
        for label in window.overview_panel.awarded_page.findChildren(type(window.title_label))
        if label.property("overviewDetailBet")
    ]
    meta_labels = [
        label
        for label in window.overview_panel.awarded_page.findChildren(type(window.title_label))
        if label.property("overviewDetailMeta")
    ]
    assert any(label.isVisible() and "M 6554" in label.text() for label in bet_labels)
    assert any(label.isVisible() and "Pág. 1 • Linha 1 • 1° prêmio" in label.text() for label in meta_labels)
    window.close()


def test_overview_panel_marks_selected_block(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    controller.create_block("452")
    controller.create_block("986")
    controller.update_selection(
        type(
            "SelectionContextStub",
            (),
            {
                "block_id": controller.state.blocks[1].block_id,
                "page_id": None,
                "line_id": None,
                "column": 0,
            },
        )()
    )
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    block_buttons = [
        button
        for button in window.overview_panel.blocks_page.findChildren(QToolButton)
        if button.property("overviewKind") == "block"
    ]

    assert any(
        button.text().startswith("Bloco 986") and button.property("overviewSelected") is True
        for button in block_buttons
    )
    window.close()


def test_overview_block_click_moves_launches_to_top(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    for number in ("452", "453", "454", "455", "456", "457", "458", "459", "986"):
        controller.create_block(number)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    target_button = next(
        button
        for button in window.overview_panel.blocks_page.findChildren(QToolButton)
        if button.property("overviewKind") == "block" and button.text().startswith("Bloco 454")
    )

    target_button.click()
    QTest.qWait(30)

    current_projection = window.bets_model.row_at(window.bets_view.currentIndex().row())
    top_row = window.bets_view.rowAt(0)
    top_projection = window.bets_model.row_at(top_row)

    assert current_projection.block_number == "454"
    assert top_projection.block_number == "454"
    window.close()


def test_awarded_overview_block_click_also_navigates_launches(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "M 6554", commit_mode=CommitMode.ENTER)
    controller.set_result(["6554", "1234", "5678", "9012", "3456"])
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    awarded_button = next(
        button
        for button in window.overview_panel.awarded_page.findChildren(QToolButton)
        if button.property("overviewKind") == "awarded"
    )

    awarded_button.click()
    QTest.qWait(30)

    current_projection = window.bets_model.row_at(window.bets_view.currentIndex().row())
    top_row = window.bets_view.rowAt(0)
    top_projection = window.bets_model.row_at(top_row)

    assert current_projection.block_number == "452"
    assert top_projection.block_number == "452"
    window.close()


def test_pending_panel_uses_grouped_collapsed_sections(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    controller.upsert_bet_text(controller.state.blocks[0].pages[0].lines[1].line_id, "erro livre", commit_mode=CommitMode.ENTER)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    summary_buttons = [
        button
        for button in window.pending_panel.findChildren(QToolButton)
        if button.property("pendencySummaryButton")
    ]
    detail_labels = [
        label
        for label in window.pending_panel.findChildren(type(window.title_label))
        if label.property("pendencyDetail")
    ]

    assert window.pending_panel.title() == "Pendências do horário"
    assert [button.text() for button in summary_buttons] == [
        "Sessão • 1 crítica",
        "Bloco 452 • 3 críticas • 1 aviso",
    ]
    assert all(label.isVisible() is False for label in detail_labels)

    summary_buttons[1].click()
    QTest.qWait(20)

    visible_details = [label.text() for label in detail_labels if label.isVisible()]
    assert "Dinheiro não informado" in visible_details
    assert "Contato não configurado" in visible_details
    window.close()
    return


def test_middle_column_orders_result_then_overview_then_pendencies(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(30)

    middle_layout = window.overview_panel.parentWidget().layout()

    assert middle_layout.itemAt(0).widget() is window.result_panel
    assert middle_layout.itemAt(1).widget() is window.overview_panel
    assert middle_layout.itemAt(2).widget() is window.pending_panel
    window.close()
    return

    texts = [label.text() for label in window.pending_panel.findChildren(type(window.title_label))]

    assert window.pending_panel.title() == "Pendências do horário"
    assert "⚠ SESSÃO" in texts
    assert "⚠ BLOCO 452" in texts
    assert "• Resultado não informado" in texts
    assert "• Contato não configurado" in texts
    window.close()


def test_open_file_dialog_uses_qt_styled_dialog(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    window = MainWindow(controller, root)

    dialog = window.build_open_file_dialog()

    assert dialog.acceptMode() == QFileDialog.AcceptMode.AcceptOpen
    assert dialog.fileMode() == QFileDialog.FileMode.ExistingFile
    assert dialog.testOption(QFileDialog.Option.DontUseNativeDialog) is True
    dialog.close()
    window.close()


def test_session_name_action_updates_controller_state(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    monkeypatch.setattr("ui.main_window.SessionNameDialog.exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("ui.main_window.SessionNameDialog.value", lambda self: "Operacao da tarde")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(30)

    window.handle_session_name()

    assert controller.state.session_name == "Operacao da tarde"
    window.close()


def test_toolbar_exposes_explicit_session_actions(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    window = MainWindow(controller, root)
    toolbar = window.findChild(QToolBar, "mainToolbar")
    session_button = window.findChild(QToolButton, "sessionMenuButton")
    search_input = window.findChild(QComboBox, "toolbarBlockSearch")

    assert toolbar is not None
    assert session_button is not None
    assert search_input is not None
    assert session_button.text() == "Sessão"
    assert [action.text() for action in toolbar.actions() if action.text()] == ["Salvar", "Compartilhar", "Preencher", "Resultado"]
    assert [action.text() for action in session_button.menu().actions() if not action.isSeparator()] == [
        "Abrir sessão salva...",
        "Nova sessão...",
        "Salvar",
        "Renomear sessão...",
        "Encerrar sessão",
    ]
    assert "sessão atual" in session_button.toolTip().lower()
    window.close()


def test_toolbar_block_search_dropdown_keeps_target_block_at_top(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    for number in ("452", "453", "454", "455", "456", "457", "458", "459", "986"):
        controller.create_block(number)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    window.block_search_input.setCurrentIndex(window.block_search_input.findText("454"))
    window.handle_block_search()
    QTest.qWait(20)

    current_projection = window.bets_model.row_at(window.bets_view.currentIndex().row())
    top_row = window.bets_view.rowAt(0)
    top_projection = window.bets_model.row_at(top_row)

    assert current_projection.block_number == "454"
    assert top_projection.block_number == "454"
    window.close()


def test_block_navigation_applies_short_flash_to_destination(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    for number in ("452", "453", "454", "455"):
        controller.create_block(number)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    window.handle_focus_block(controller.state.blocks[2].block_id)

    assert window.bets_view._flash_block_id == controller.state.blocks[2].block_id
    QTest.qWait(980)
    assert window.bets_view._flash_block_id is None
    window.close()


def test_share_session_copies_dynamic_mobile_link(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    monkeypatch.setattr("ui.main_window.detect_local_network_ip", lambda: "192.168.0.55")
    monkeypatch.setattr("ui.main_window.is_mobile_backend_reachable", lambda host, port: True)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(30)
    QApplication.clipboard().clear()

    window.handle_share_session()

    assert QApplication.clipboard().text() == "http://192.168.0.55:8765/mobile"
    assert "Link da sessão copiado" in window.statusBar().currentMessage()
    window.close()


def test_share_session_can_copy_even_when_backend_is_offline(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    monkeypatch.setattr("ui.main_window.detect_local_network_ip", lambda: "192.168.0.88")
    monkeypatch.setattr("ui.main_window.is_mobile_backend_reachable", lambda host, port: False)
    monkeypatch.setattr("ui.main_window.ask_confirmation", lambda *args, **kwargs: True)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(30)
    QApplication.clipboard().clear()

    window.handle_share_session()

    assert QApplication.clipboard().text() == "http://192.168.0.88:8765/mobile"
    assert "Link copiado" in window.statusBar().currentMessage()
    window.close()


def test_share_session_shows_error_when_local_ip_is_unavailable(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    errors: list[str] = []
    monkeypatch.setattr("ui.main_window.detect_local_network_ip", lambda: None)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(30)
    QApplication.clipboard().setText("preserve")
    monkeypatch.setattr(window, "show_error", lambda message: errors.append(message))

    window.handle_share_session()

    assert errors == ["Não foi possível detectar um IP válido da rede local para compartilhar a sessão."]
    assert QApplication.clipboard().text() == "preserve"
    window.close()


def test_window_starts_and_stops_mobile_backend_manager(tmp_path, qapp):
    class FakeMobileBackendManager:
        def __init__(self) -> None:
            self.start_calls = 0
            self.stop_calls = 0

        def ensure_running(self):
            self.start_calls += 1
            return type("Result", (), {"running": True, "message": ""})()

        def stop(self) -> None:
            self.stop_calls += 1

    root = Path(tmp_path)
    controller = BancaController(root)
    manager = FakeMobileBackendManager()
    window = MainWindow(controller, root, mobile_backend_manager=manager)
    window.show()
    QTest.qWait(30)
    window.close()

    assert manager.start_calls == 1
    assert manager.stop_calls == 1



def test_new_session_opens_name_dialog_immediately(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    controller = BancaController(root)
    controller.create_block("452")
    monkeypatch.setattr("ui.main_window.ask_confirmation", lambda *args, **kwargs: True)
    monkeypatch.setattr("ui.main_window.SessionNameDialog.exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("ui.main_window.SessionNameDialog.value", lambda self: "Nova rodada")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(30)

    window.handle_new_session()

    assert controller.state.blocks == []
    assert controller.state.session_name == "Nova rodada"
    window.close()


def test_startup_resume_prompt_restores_runtime_when_accepted(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    source = BancaController(root)
    source.set_session_name("Operacao salva")
    source.create_block("452")

    controller = BancaController(root, restore_active_session=False)
    monkeypatch.setattr("ui.main_window.ask_confirmation", lambda *args, **kwargs: True)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(60)

    assert controller.state.session_name == "Operacao salva"
    assert len(controller.state.blocks) == 1
    window.close()


def test_startup_resume_prompt_can_discard_runtime(tmp_path, qapp, monkeypatch):
    root = Path(tmp_path)
    source = BancaController(root)
    source.set_session_name("Operacao salva")
    source.create_block("452")

    controller = BancaController(root, restore_active_session=False)
    monkeypatch.setattr("ui.main_window.ask_confirmation", lambda *args, **kwargs: False)
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(60)

    assert controller.state.session_name == ""
    assert controller.has_active_runtime_session() is False
    window.close()


def test_open_window_syncs_mobile_value_from_shared_session(tmp_path, qapp):
    root = Path(tmp_path)
    desktop = BancaController(root)
    _, _, first_line_id = desktop.create_block("452")
    desktop.upsert_bet_text(first_line_id, "555", commit_mode=CommitMode.ENTER)
    second_line_id = desktop.state.blocks[0].pages[0].lines[1].line_id
    desktop.upsert_bet_text(second_line_id, "666", commit_mode=CommitMode.ENTER)
    window = MainWindow(desktop, root)
    window.show()
    QTest.qWait(40)

    mobile = BancaController(root)
    mobile.set_line_value(second_line_id, "7")
    window.sync_external_mobile_values()

    target_row = next(
        row_index
        for row_index in range(window.bets_model.rowCount())
        if window.bets_model.line_id_for_row(row_index) == second_line_id
    )

    assert window.bets_model.data(window.bets_model.index(target_row, 1), Qt.DisplayRole) == "7,00"
    window.close()


def test_finance_totals_panel_shows_cash_result(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    block_id, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "555", commit_mode=CommitMode.ENTER)
    controller.set_line_value(line_id, "100")
    controller.set_block_money(block_id, "200")
    controller.set_total_paid_prizes("50")
    window = MainWindow(controller, root)
    window.show()
    QTest.qWait(40)

    assert window.finance_totals_panel.total_received_value.text() == "200,00"
    assert window.finance_totals_panel.total_bruto_value.text() == "100,00"
    assert window.finance_totals_panel.total_liquido_value.text() == "70,00"
    assert window.finance_totals_panel.cash_result_value.text() == "+150,00"
    assert window.finance_totals_panel.cash_result_value.property("cashTone") == "positive"
    window.close()


def test_splitter_prioritizes_launches_over_finance(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    controller.create_block("452")
    window = MainWindow(controller, root)
    window.show()
    window.resize(1500, 920)
    QTest.qWait(80)

    left_size, middle_size, right_size = window.splitter.sizes()

    assert left_size > middle_size
    assert abs(left_size - right_size) <= 40


def test_result_panel_keeps_five_rows_and_center_value(tmp_path, qapp):
    root = Path(tmp_path)
    controller = BancaController(root)
    window = MainWindow(controller, root)
    controller.set_result(["6554", "1234", "5678", "9012", "3456"])
    window.show()
    QTest.qWait(40)

    first_row = window.result_panel.rows[0]

    assert len(window.result_panel.rows) == 5
    assert first_row[0].text() == "1\u00b0 pr\u00eamio"
    assert first_row[1].text() == "6554"
    assert first_row[2].text() == "Grupo 14"


def test_bet_delegate_displays_type_before_number(tmp_path, qapp):
    controller = BancaController(tmp_path)
    _, _, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "C 555 DE", commit_mode=CommitMode.ENTER)
    delegate = BetDelegate(None)
    spec = controller.state.blocks[0].pages[0].lines[0].spec

    type_text, number_text, flag_texts = delegate.display_tokens(spec)

    assert type_text == "C"
    assert number_text == "555"
    assert flag_texts == ["DE"]


def test_value_column_stays_blank_until_monetary_value_exists(tmp_path, qapp):
    controller = BancaController(tmp_path)
    _, page_id, line_id = controller.create_block("452")
    controller.upsert_bet_text(line_id, "MC 6312 DE", commit_mode=CommitMode.ENTER)
    model = BetsTableModel(controller)
    first_row = model.first_editable_row_for_page(page_id)

    assert model.data(model.index(first_row, 1), Qt.DisplayRole) == ""
