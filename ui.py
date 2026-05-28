import contextlib
import io

import pandas as pd
import streamlit as st
from matplotlib.figure import Figure

from solvers.convex_hull import giai_bai_toan_hinh_hoc_2_rb
from solvers.graphical import giai_bai_toan_truot_ham_muc_tieu
from solvers.simplex_bland import giai_bai_toan_don_hinh_bland
from solvers.simplex_pivot import giai_bai_toan_xoay_don_hinh
from solvers.simplex_tableau import giai_bai_toan_don_hinh_dang_bang
from solvers.simplex_twophase import giai_bai_toan_don_hinh
from utils import chuyen_sang_dang_chuan, chuyen_tong_quat_sang_chinh_tac


FLOW_OPTIONS = [
	("Đồ thị (2 biến)", "graphical"),
	("Hình học (2 ràng buộc)", "convex"),
	("Đơn hình dạng bảng", "tableau"),
	("Xoay đơn hình", "pivot"),
	("Bland", "bland"),
	("Đơn hình 2 pha", "twophase"),
]


def init_state():
	st.session_state.setdefault("num_vars", 2)
	st.session_state.setdefault("num_constraints", 2)
	st.session_state.setdefault("opt_type", "Max")
	st.session_state.setdefault("data_ready", False)
	st.session_state.setdefault("results", {})
	st.session_state.setdefault("show_confirmation_section", False)
	st.session_state.setdefault("standard_form_result", None)
	st.session_state.setdefault("canonical_form_result", None)


def sync_defaults(num_vars, num_constraints):
	for i in range(num_vars):
		st.session_state.setdefault(f"x_cond_{i}", ">= 0")
		st.session_state.setdefault(f"c_{i}", 0.0)

	for i in range(num_constraints):
		st.session_state.setdefault(f"sign_{i}", "<=")
		st.session_state.setdefault(f"b_{i}", 0.0)
		for j in range(num_vars):
			st.session_state.setdefault(f"a_{i}_{j}", 0.0)


def build_problem_from_state(num_vars, num_constraints):
	opt_type = st.session_state.get("opt_type", "Max")
	c = [float(st.session_state.get(f"c_{i}", 0.0)) for i in range(num_vars)]
	x_conds = [st.session_state.get(f"x_cond_{i}", ">= 0") for i in range(num_vars)]
	constraints = []

	for i in range(num_constraints):
		row = [float(st.session_state.get(f"a_{i}_{j}", 0.0)) for j in range(num_vars)]
		sign = st.session_state.get(f"sign_{i}", "<=")
		b_val = float(st.session_state.get(f"b_{i}", 0.0))
		constraints.append({"A_row": row, "sign": sign, "b": b_val})

	return opt_type, c, constraints, x_conds


def format_linear_expression(coeffs, var_names):
	parts = []
	for coef, var in zip(coeffs, var_names):
		if abs(coef) < 1e-9:
			continue
		if coef == 1:
			parts.append(f"+ {var}")
		elif coef == -1:
			parts.append(f"- {var}")
		elif coef > 0:
			parts.append(f"+ {coef:g}{var}")
		else:
			parts.append(f"- {abs(coef):g}{var}")

	if not parts:
		return "0"

	expr = " ".join(parts)
	if expr.startswith("+ "):
		expr = expr[2:]
	return expr


def render_problem_block(opt_type, c, constraints, x_conds):
	var_names = [f"x{i + 1}" for i in range(len(c))]
	lines = [f"Loại bài toán: {opt_type}", "", "Hàm mục tiêu:"]
	lines.append(f"{opt_type} Z = {format_linear_expression(c, var_names)}")
	lines.append("")
	lines.append("Ràng buộc:")
	for i, const in enumerate(constraints):
		lhs = format_linear_expression(const["A_row"], var_names)
		lines.append(f"{lhs} {const['sign']} {const['b']}")
	lines.append("")
	lines.append("Điều kiện biến:")
	for i, cond in enumerate(x_conds):
		lines.append(f"x{i + 1} {cond}")
	return "\n".join(lines)


def render_conversion_result(title, c, A, b, var_names, relation):
	lines = [f"{title}", "", "Loại bài toán: Min", "", "Hàm mục tiêu:"]
	lines.append(f"Min Z = {format_linear_expression(c, var_names)}")
	lines.append("")
	lines.append("Ràng buộc:")
	for row, rhs in zip(A, b):
		lines.append(f"{format_linear_expression(row, var_names)} {relation} {rhs}")
	return "\n".join(lines)


def run_solver_with_output(run_func, *args, **kwargs):
	buf = io.StringIO()
	fig = None

	with contextlib.redirect_stdout(buf):
		result = run_func(*args, **kwargs)

	if isinstance(result, Figure):
		fig = result

	return buf.getvalue(), fig


def is_header_line(line):
	line_stripped = line.strip()
	if not line_stripped:
		return False
	if line_stripped.startswith("___"):
		return True
	if line_stripped.startswith("GIẢI BÀI TOÁN"):
		return True
	if line_stripped.startswith("THUẬT TOÁN"):
		return True
	if "KẾT LUẬN" in line_stripped:
		return True
	return False


def split_sections(output_text):
	lines = output_text.splitlines()
	sections = []
	current_title = "Chi tiết"
	current_lines = []

	for line in lines:
		if is_header_line(line):
			if current_lines:
				sections.append((current_title, current_lines))
			current_title = line.strip("_ ")
			current_lines = []
		else:
			current_lines.append(line)

	if current_lines:
		sections.append((current_title, current_lines))

	if not sections and lines:
		sections = [("Chi tiết", lines)]

	return sections


def split_segments(lines):
	segments = []
	table_lines = []
	text_lines = []

	def flush_text():
		if text_lines:
			segments.append(("text", text_lines.copy()))
			text_lines.clear()

	def flush_table():
		if table_lines:
			segments.append(("table", table_lines.copy()))
			table_lines.clear()

	for line in lines:
		if "|" in line:
			if text_lines:
				flush_text()
			table_lines.append(line)
		elif table_lines and line.strip().startswith("-"):
			continue
		else:
			if table_lines:
				flush_table()
			text_lines.append(line)

	flush_table()
	flush_text()

	return segments


def table_from_lines(lines):
	rows = []
	for line in lines:
		cells = [c.strip() for c in line.split("|") if c.strip()]
		if cells:
			rows.append(cells)

	if not rows:
		return None

	header = rows[0]
	data_rows = rows[1:]

	if data_rows and all(len(r) == len(header) for r in data_rows):
		return pd.DataFrame(data_rows, columns=header)

	return pd.DataFrame(rows)


def extract_summary(output_text):
	lines = [line for line in output_text.splitlines() if line.strip()]
	if not lines:
		return ""

	last_idx = None
	for i, line in enumerate(lines):
		if "KẾT LUẬN" in line or line.strip().startswith("KẾT QUẢ"):
			last_idx = i

	if last_idx is not None:
		return "\n".join(lines[last_idx:])

	return "\n".join(lines[-8:])


def render_log(output_text):
	sections = split_sections(output_text)

	for title, lines in sections:
		if title:
			st.subheader(title)

		segments = split_segments(lines)
		for seg_type, seg_lines in segments:
			if seg_type == "table":
				df = table_from_lines(seg_lines)
				if df is not None:
					st.table(df)
				else:
					st.code("\n".join(seg_lines))
			else:
				text = "\n".join(seg_lines).strip()
				if text:
					st.code(text)


def show_result(flow_key, output_text, fig):
	summary = extract_summary(output_text)

	st.markdown("### Tóm tắt kết quả")
	if summary:
		st.code(summary)
	else:
		st.info("Chưa có kết quả để hiển thị.")

	if fig is not None:
		st.markdown("### Đồ thị")
		st.pyplot(fig)


def main():
	st.set_page_config(page_title="QHTT Demo", layout="wide")

	init_state()

	st.title("Quy hoạch tuyến tính")
	
	num_vars = st.session_state.num_vars
	num_constraints = st.session_state.num_constraints
	sync_defaults(num_vars, num_constraints)

	with st.form("input_form"):
		st.subheader("Nhập dữ liệu bài toán")

		col_a, col_b, col_c = st.columns([1, 1, 1])
		with col_a:
			st.number_input(
				"Số biến (n)",
				min_value=1,
				max_value=20,
				step=1,
				key="num_vars",
			)
		with col_b:
			st.number_input(
				"Số ràng buộc (m)",
				min_value=1,
				max_value=20,
				step=1,
				key="num_constraints",
			)
		with col_c:
			st.selectbox("Loại bài toán", ["Max", "Min"], key="opt_type")

		num_vars = st.session_state.num_vars
		num_constraints = st.session_state.num_constraints
		sync_defaults(num_vars, num_constraints)

		st.markdown("#### Điều kiện biến")
		var_cols = st.columns(min(num_vars, 4))
		for i in range(num_vars):
			with var_cols[i % len(var_cols)]:
				st.selectbox(
					f"x{i + 1}",
					[">= 0", "<= 0", "tự do"],
					key=f"x_cond_{i}",
				)

		st.markdown("#### Hệ số hàm mục tiêu")
		coef_cols = st.columns(min(num_vars, 4))
		for i in range(num_vars):
			with coef_cols[i % len(coef_cols)]:
				st.number_input(
					f"c{i + 1}",
					step=0.5,
					key=f"c_{i}",
				)

		st.markdown("#### Ràng buộc")
		for i in range(num_constraints):
			st.markdown(f"**Ràng buộc {i + 1}**")
			row_cols = st.columns(num_vars + 2)
			for j in range(num_vars):
				row_cols[j].number_input(
					f"a{i + 1},{j + 1}",
					step=0.5,
					key=f"a_{i}_{j}",
				)
			row_cols[num_vars].selectbox(
				"dấu",
				["<=", ">=", "="],
				key=f"sign_{i}",
			)
			row_cols[num_vars + 1].number_input(
				"b",
				step=0.5,
				key=f"b_{i}",
			)

		submitted = st.form_submit_button("Áp dụng dữ liệu")
		confirm_original = st.form_submit_button("XÁC NHẬN BÀI TOÁN GỐC ĐÃ NHẬP")

	if submitted:
		problem_data = build_problem_from_state(num_vars, num_constraints)
		st.session_state["problem_data"] = problem_data
		st.session_state["data_ready"] = True
		st.session_state["show_confirmation_section"] = False
		st.session_state["standard_form_result"] = None
		st.session_state["canonical_form_result"] = None
		st.success("Đã cập nhật dữ liệu bài toán.")

	if confirm_original:
		problem_data = build_problem_from_state(num_vars, num_constraints)
		st.session_state["problem_data"] = problem_data
		st.session_state["data_ready"] = True
		st.session_state["show_confirmation_section"] = True
		st.session_state["standard_form_result"] = None
		st.session_state["canonical_form_result"] = None
		st.success("Đã xác nhận bài toán gốc đã nhập.")

	if st.session_state.get("show_confirmation_section", False):
		problem_data = st.session_state.get("problem_data")
		if problem_data is None:
			problem_data = build_problem_from_state(num_vars, num_constraints)
		opt_type, c, constraints, x_conds = problem_data
		st.markdown("### XÁC NHẬN BÀI TOÁN GỐC ĐÃ NHẬP")
		st.code(render_problem_block(opt_type, c, constraints, x_conds))

		col_std, col_can = st.columns(2)
		with col_std:
			if st.button("Chuyển sang Dạng Chuẩn", key="btn_standard_form"):
				st.session_state["standard_form_result"] = chuyen_sang_dang_chuan(opt_type, c, constraints, x_conds)
		with col_can:
			if st.button("Chuyển sang Dạng Chính tắc", key="btn_canonical_form"):
				st.session_state["canonical_form_result"] = chuyen_tong_quat_sang_chinh_tac(opt_type, c, constraints, x_conds)

		if st.session_state.get("standard_form_result") is not None:
			c_std, A_std, b_std, var_names_std = st.session_state["standard_form_result"]
			st.markdown("#### Dạng chuẩn")
			st.code(render_conversion_result("Dạng chuẩn", c_std, A_std, b_std, var_names_std, "<="))

		if st.session_state.get("canonical_form_result") is not None:
			c_can, A_can, b_can, var_names_can = st.session_state["canonical_form_result"]
			st.markdown("#### Dạng chính tắc")
			st.code(render_conversion_result("Dạng chính tắc", c_can, A_can, b_can, var_names_can, "="))

	label_to_key = {label: key for label, key in FLOW_OPTIONS}
	flow_label = st.radio(
		"Chọn phương pháp",
		[label for label, _ in FLOW_OPTIONS],
		horizontal=True,
	)
	flow_key = label_to_key[flow_label]

	show_detail = st.checkbox("Hiển thị log chi tiết", value=False)

	run_clicked = st.button("Giải", type="primary")

	if run_clicked:
		if not st.session_state.get("data_ready"):
			st.warning("Bạn chưa bấm 'Áp dụng dữ liệu'. Đang dùng dữ liệu hiện tại.")

		problem_data = build_problem_from_state(num_vars, num_constraints)

		opt_type, c, constraints, x_conds = problem_data

		if flow_key == "graphical" and num_vars != 2:
			st.warning("Phương pháp Đồ thị chỉ hỗ trợ 2 biến.")
		elif flow_key == "convex" and num_constraints != 2:
			st.warning("Phương pháp Hình học yêu cầu đúng 2 ràng buộc.")
		else:
			try:
				if flow_key == "graphical":
					output, fig = run_solver_with_output(
						giai_bai_toan_truot_ham_muc_tieu,
						opt_type,
						c,
						constraints,
						x_conds,
						show_plot=False,
						return_fig=True,
					)
				elif flow_key == "convex":
					output, fig = run_solver_with_output(
						giai_bai_toan_hinh_hoc_2_rb,
						opt_type,
						c,
						constraints,
						x_conds,
						show_plot=False,
						return_fig=True,
					)
				elif flow_key == "tableau":
					output, fig = run_solver_with_output(
						giai_bai_toan_don_hinh_dang_bang,
						opt_type,
						c,
						constraints,
						x_conds,
					)
				elif flow_key == "pivot":
					output, fig = run_solver_with_output(
						giai_bai_toan_xoay_don_hinh,
						opt_type,
						c,
						constraints,
						x_conds,
					)
				elif flow_key == "bland":
					output, fig = run_solver_with_output(
						giai_bai_toan_don_hinh_bland,
						opt_type,
						c,
						constraints,
						x_conds,
					)
				else:
					output, fig = run_solver_with_output(
						giai_bai_toan_don_hinh,
						opt_type,
						c,
						constraints,
						x_conds,
					)

				st.session_state.results[flow_key] = {
					"output": output,
					"fig": fig,
				}
			except Exception as exc:
				st.error(f"Không thể chạy giải thuật: {exc}")

	result = st.session_state.results.get(flow_key)
	if result:
		show_result(flow_key, result.get("output", ""), result.get("fig"))

		if show_detail:
			with st.expander("Chi tiết log", expanded=True):
				render_log(result.get("output", ""))
	else:
			st.info("Hãy nhập dữ liệu và bấm 'Giải' để xem kết quả.")


if __name__ == "__main__":
	main()
